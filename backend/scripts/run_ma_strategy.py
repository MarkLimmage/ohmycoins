import asyncio
import logging
import random
import sys
import os
import time
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import datetime
from zoneinfo import ZoneInfo

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import User, Algorithm, Position
from app.services.trading.executor import get_order_queue
from app.services.trading.algorithm_executor import AlgorithmExecutor
from app.services.trading.strategies.ma_crossover import MACrossoverStrategy
from app.services.trading.paper_exchange import PaperExchange

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Force Paper Mode
settings.TRADING_MODE = 'paper'

async def main():
    logger.info("Starting Strategy Loop (Paper Trading) - 24h Mode")
    
    with Session(engine) as session:
        # 1. Setup Data
        logger.info("Setting up user and algorithm...")
        user = session.exec(select(User).where(User.email == "strategist@omc.local")).first()
        if not user:
            user = User(
                email="strategist@omc.local", 
                hashed_password="dummy",
                full_name="The Strategist",
                timezone="UTC",
                preferred_currency="AUD",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Created user {user.email} ({user.id})")
            
        algo = session.exec(select(Algorithm).where(Algorithm.name == "MA Crossover")).first()
        if not algo:
            algo = Algorithm(
                name="MA Crossover",
                algorithm_type="rule_based",
                created_by=user.id,
                status="active"
            )
            session.add(algo)
            session.commit()
            session.refresh(algo)
            logger.info(f"Created algorithm {algo.name} ({algo.id})")

        # 2. Seed Funds (CRITICAL for Safety Checks)
        aud_position = session.exec(select(Position).where(
            Position.user_id == user.id, 
            Position.coin_type == "AUD"
        )).first()
        
        initial_capital = Decimal("100000.0")
        
        if not aud_position:
            aud_position = Position(
                user_id=user.id,
                coin_type="AUD",
                quantity=initial_capital,
                average_price=Decimal("1.0"),
                total_cost=initial_capital
            )
            session.add(aud_position)
            session.commit()
            logger.info(f"Seeded AUD position: {initial_capital}")
        else:
            logger.info(f"Existing AUD position: {aud_position.quantity}")

        # 3. Initialize OrderQueue
        logger.info("Initializing OrderQueue...")
        queue = get_order_queue()
        queue.initialize(
            session=session,
            api_key="mock",
            api_secret="mock"
        )
        
        # Start OrderExecutor
        executor_task = asyncio.create_task(queue.start())
        
        # 4. Setup Strategy & Executor
        strategy = MACrossoverStrategy(short_window=2, long_window=5)
        
        algo_executor = AlgorithmExecutor(
            session=session,
            api_key="mock",
            api_secret="mock"
        )
        
        # Wait for executor to start
        await asyncio.sleep(2)
        
        # Access PaperExchange
        order_executor = queue._executor
        if not order_executor or not order_executor.paper_exchange:
             logger.error("PaperExchange not initialized in OrderExecutor!")
             await queue.stop()
             return
             
        paper_exchange = order_executor.paper_exchange
        
        # Ensure PaperExchange matches DB funds
        paper_exchange.balances['AUD'] = aud_position.quantity
        
        coin_type = "BTC"
        current_price = Decimal("100000.0")
        paper_exchange.set_price(coin_type, current_price)
        
        logger.info(f"Initial Price: {current_price}")
        
        try:
            logger.info("Starting infinite loop. Press Ctrl+C to stop (if interactive).")
            cycle = 0
            while True:
                # Update Market Data (Simulated Random Walk)
                change_pct = Decimal(random.uniform(-0.01, 0.01))
                current_price = current_price * (Decimal("1.0") + change_pct)
                paper_exchange.set_price(coin_type, current_price)
                
                if cycle % 10 == 0:
                    logger.info(f"Cycle {cycle}: Price {current_price:.2f}")
                
                # Execute Strategy
                market_data = {
                    'coin_type': coin_type,
                    'prices': {
                        coin_type: {
                            'last': float(current_price),
                            'bid': float(current_price * Decimal('0.999')),
                            'ask': float(current_price * Decimal('1.001'))
                        }
                    },
                    'price': float(current_price),
                    'volume_24h': 1000
                }
                
                await algo_executor.execute_algorithm(
                    user_id=user.id,
                    algorithm_id=algo.id,
                    algorithm=strategy,
                    market_data=market_data
                )
                
                cycle += 1
                await asyncio.sleep(1)  # Run every 1 seconds
                
        except KeyboardInterrupt:
            logger.info("Stopping...")
        finally:
            logger.info("Stopping Order Executor...")
            await queue.stop()
            logger.info("Done.")

if __name__ == "__main__":
    asyncio.run(main())
