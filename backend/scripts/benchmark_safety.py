#!/usr/bin/env python3
"""
Safety Mechanism Performance Benchmark

Sprint 2.26 - Track A: Production Hardening

This script benchmarks the latency of the TradingSafetyManager.validate_trade method.
Goal: Ensure <200ms overhead.
"""
import asyncio
import time
import sys
import logging
from pathlib import Path
from decimal import Decimal
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.services.trading.safety import TradingSafetyManager
from app.models import User, Position, Order, RiskRule
from app.core.db import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress other logs
logging.getLogger("httpx").setLevel(logging.WARNING)

async def run_benchmark() -> None:
    logger.info("Initializing Safety Benchmark...")
    
    # Create a dedicated session
    # We use a separate engine/session or the standard one
    # Assuming running in container where DB is accessible
    
    with Session(engine) as session:
        # Create Dummy User
        test_user_id = uuid4()
        user = User(
            id=test_user_id,
            email=f"bench_{test_user_id}@example.com",
            hashed_password="hash",
            is_active=True
        )
        session.add(user)
        
        # Create positions (Portfolio Value ~10,000)
        p1 = Position(
            user_id=test_user_id,
            coin_type="BTC",
            quantity=Decimal("0.1"),
            average_price=Decimal("60000"),
            total_cost=Decimal("6000")
        )
        p2 = Position(
            user_id=test_user_id,
            coin_type="ETH",
            quantity=Decimal("1.0"),
            average_price=Decimal("4000"),
            total_cost=Decimal("4000")
        )
        session.add(p1)
        session.add(p2)
        session.commit()
        
        logger.info(f"Created test user {test_user_id} with portfolio ~10k")

        # Initialize Safety Manager
        manager = TradingSafetyManager(session=session)
        await manager.connect()

        # Warmup Cache/Connection
        logger.info("Warming up...")
        await manager.validate_trade(
            user_id=test_user_id,
            coin_type="ADA",
            side="buy",
            quantity=Decimal("100"),
            estimated_price=Decimal("0.5")
        )

        ITERATIONS = 100
        latencies = []

        logger.info(f"Running {ITERATIONS} iterations...")
        
        try:
            for i in range(ITERATIONS):
                start = time.perf_counter()
                
                await manager.validate_trade(
                    user_id=test_user_id,
                    coin_type="SOL",
                    side="buy",
                    quantity=Decimal("10"),
                    estimated_price=Decimal("100") # 1000 AUD, well within 20% limit
                )
                
                end = time.perf_counter()
                latencies.append((end - start) * 1000) # ms

            # Results
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            # P95
            latencies.sort()
            p95 = latencies[int(len(latencies) * 0.95)]

            print("\n" + "="*40)
            print(f"BENCHMARK RESULTS (N={ITERATIONS})")
            print("="*40)
            print(f"Average Latency: {avg_latency:.2f} ms")
            print(f"P95 Latency:     {p95:.2f} ms")
            print(f"Min Latency:     {min_latency:.2f} ms")
            print(f"Max Latency:     {max_latency:.2f} ms")
            print("="*40)
            
            if avg_latency < 200:
                print("✅ PASS: Average Latency < 200ms")
            else:
                print("❌ FAIL: Average Latency > 200ms")

        finally:
            # Cleanup
            logger.info("Cleaning up...")
            try:
                from app.models import AuditLog
                statement = select(AuditLog).where(AuditLog.user_id == user.id)
                audit_logs = session.exec(statement).all()
                for log in audit_logs:
                    session.delete(log)
                session.commit()
            except Exception as e:
                logger.warning(f"Failed to clean up audit logs: {e}")

            session.delete(p1)
            session.delete(p2)
            session.delete(user)
            session.commit()
            await manager.disconnect()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
