import asyncio
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import Order, User
from app.services.trading.client import CoinspotTradingClient
from app.services.trading.executor import OrderExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# FORCE LIVE MODE FOR THIS SCRIPT
# This overrides the default settings to ensure we actually hit the live endpoint
settings.TRADING_MODE = 'live'

async def main() -> None:
    logger.info("Starting Live Strategy Execution Test")
    logger.info("WARNING: This is a REAL MONEY test. Funds will be spent.")

    if not settings.COINSPOT_API_KEY or not settings.COINSPOT_API_SECRET:
         logger.error("CoinSpot API credentials not found in settings!")
         return

    with Session(engine) as session:
        # 1. Get or Create "The Strategist" User
        user = session.exec(select(User).where(User.email == "strategist@omc.local")).first()
        if not user:
            logger.info("Strategist user not found. Creating new user...")
            user = User(
                email="strategist@omc.local",
                hashed_password="dummy_password_hash",
                full_name="The Strategist",
                timezone="UTC",
                preferred_currency="AUD",
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Created user {user.email} ({user.id})")

        logger.info(f"Acting as user: {user.email} ({user.id})")

        # 2. visual confirmation
        logger.info("-" * 50)
        logger.info(f"TRADING MODE: {settings.TRADING_MODE.upper()}")
        logger.info(f"API KEY: {settings.COINSPOT_API_KEY[:5]}... (verified present)")
        logger.info("-" * 50)

        # 3. Create Executor
        executor = OrderExecutor(
            session=session,
            api_key=settings.COINSPOT_API_KEY,
            api_secret=settings.COINSPOT_API_SECRET
        )

        # 4. Create a small LIVE Buy Order ($5.00 AUD of DOGE)
        # Using DOGE to bypass potential BTC minimum trade size issues.
        buy_amount = Decimal("5.00")
        coin_type = "DOGE"

        logger.info(f"Creating LIVE Buy Order: ${buy_amount} AUD of {coin_type}")

        order = Order(
            user_id=user.id,
            coin_type=coin_type,
            side="buy",
            order_type="market",
            quantity=buy_amount,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(order)
        session.commit()
        session.refresh(order)

        logger.info(f"Order created in DB with ID: {order.id}")

        # 5. Execute Order
        try:
            logger.info("Attempting execution against CoinSpot API...")

            # Start Executor dependencies (Redis/Safety) - Manually connect
            await executor.safety_manager.connect()

            # DEBUG: Check Balance and Orders
            async with CoinspotTradingClient(settings.COINSPOT_API_KEY, settings.COINSPOT_API_SECRET) as client:
                try:
                    logger.info("Checking Open Orders...")
                    orders = await client.get_orders()
                    logger.info(f"Open Orders: {orders}")
                except Exception as e:
                    logger.error(f"Failed to check orders: {e}")

                try:
                    logger.info("Checking AUD Balance...")
                    # Using the read-only endpoint explicitly if needed, but client.get_balances does it via _make_request
                    # which uses /my/balances. Let's try raw request to /ro/my/balances if get_balance fails or just try both.
                    balances = await client.get_balances()
                    logger.info(f"All Balances Response: {balances}")
                except Exception as e:
                    logger.error(f"Failed to check balance: {e}")

            # Manually trigger the execution logic (bypassing the queue worker loop for this test)
            # We call the internal method directly to execute this specific order immediately.
            await executor._execute_order(order.id)

            logger.info("Execution attempt complete.")

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await executor.safety_manager.disconnect()

if __name__ == "__main__":
    # Run async main
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
