#!/usr/bin/env python3
"""
Hard Stop Watcher (The Guard)
Sprint 2.26 - Track A: Production Hardening

This services monitors the Total System Equity in a loop.
If the Total Equity drops below 95% of the "Initial Equity" (set at startup),
it triggers the Global Kill Switch via Redis.

Rules:
- Initial Equity is stored in Redis key 'omc:initial_equity'.
- If key missing, current equity becomes initial equity.
- Hard Stop Threshold: 95% (5% drawdown).
- Action: Activate Emergency Stop (Kill Switch).
"""
import asyncio
import logging
import sys
from decimal import Decimal
from typing import Dict
from pathlib import Path

from sqlmodel import Session, select
from sqlalchemy import func

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import engine
from app.models import User, Position, PriceData5Min
from app.services.trading.safety import TradingSafetyManager
from app.core.config import settings
import redis.asyncio as redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("HardStopWatcher")

CHECK_INTERVAL = 5  # Seconds
DRAWDOWN_LIMIT_PCT = Decimal("0.95")  # 5% max loss
REDIS_KEY_INITIAL_EQUITY = "omc:initial_equity"

async def get_latest_prices(session: Session) -> Dict[str, Decimal]:
    """
    Fetch the latest price for each coin type from PriceData5Min.
    Returns: Dict[coin_type, price]
    """
    # Using a subquery approach to get latest price per coin
    # In PostgreSQL we could use DISTINCT ON, but this is more portable SQLModel approach
    # For simplicity/speed in this watcher, checking distinct coin types first might be better
    # But let's assume valid data exists.
    
    # Efficient query: Get latest prices for all known coins
    # Note: If no price data, we fall back to average_price in Position
    
    prices = {}
    
    # Get all unique coins from positions to limit query
    coins_in_positions = session.exec(select(Position.coin_type).distinct()).all()
    
    for coin in coins_in_positions:
        # Get latest price entry
        statement = (
            select(PriceData5Min)
            .where(PriceData5Min.coin_type == coin)
            .order_by(PriceData5Min.timestamp.desc())
            .limit(1)
        )
        price_data = session.exec(statement).first()
        if price_data:
            prices[coin] = price_data.last
            
    return prices

async def calculate_total_equity(session: Session) -> Decimal:
    """
    Calculate the total equity (Positions only, since cash is not tracked in User model yet)
    of ALL users.
    """
    total_equity = Decimal("0")
    
    # 2. Total Position Value
    positions = session.exec(select(Position)).all()
    if not positions:
        return total_equity
        
    prices = await get_latest_prices(session)
    
    for pos in positions:
        # Use market price if available, else fallback to avg price (safety fallback)
        price = prices.get(pos.coin_type, pos.average_price)
        total_equity += pos.quantity * price
        
    return total_equity

async def monitor_equity():
    logger.info("Starting Hard Stop Watcher...")
    
    redis_client = await redis.from_url(
        settings.REDIS_URL, 
        encoding="utf-8", 
        decode_responses=True
    )
    
    # We can reuse the safety manager logic for activation, 
    # but we need to pass a session. We'll create one per loop or reuse.
    # Better to create one per loop for long running process.
    
    while True:
        try:
            with Session(engine) as session:
                safety = TradingSafetyManager(session)
                
                # Check Global Kill Switch Status first
                # If already active, we just log and wait (or we could stop?)
                is_active = await redis_client.get("omc:emergency_stop")
                if is_active == "true":
                    logger.debug("Emergency Stop already active.")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                current_equity = await calculate_total_equity(session)
                
                # Get Initial Equity
                initial_equity_str = await redis_client.get(REDIS_KEY_INITIAL_EQUITY)
                
                if not initial_equity_str:
                    # Initialize
                    # NOTE: In production, this might be set by a daily cron job at 00:00.
                    # Here, we set it on first run if missing.
                    if current_equity > 0:
                        await redis_client.set(REDIS_KEY_INITIAL_EQUITY, str(current_equity))
                        logger.info(f"Initialized Base Equity: {current_equity:.2f} AUD")
                    else:
                        logger.warning("Total Equity is 0. Strategies not deployed?")
                    
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue
                
                initial_equity = Decimal(initial_equity_str)
                
                # Check Drawdown
                threshold = initial_equity * DRAWDOWN_LIMIT_PCT
                
                if current_equity < threshold:
                    logger.critical(
                        f"HARD STOP TRIGGERED! Equity {current_equity:.2f} < {threshold:.2f} "
                        f"(Initial: {initial_equity:.2f})"
                    )
                    
                    # ACTIVATE KILL SWITCH
                    await safety.activate_emergency_stop()
                    
                    # Clean up / Disconnect (Safety Manager handles its own redis usually, 
                    # but safety.activate_emergency_stop() connects internally if needed)
                    # We should also update Redis to prevent flap if needed, 
                    # but the check 'is_active' handles that.
                    
                else:
                    logger.debug(f"Equity Safe: {current_equity:.2f} (Limit: {threshold:.2f})")

        except Exception as e:
            logger.error(f"Error in Watcher Loop: {e}")
            # Don't crash the loop
            
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_equity())
    except KeyboardInterrupt:
        logger.info("Hard Stop Watcher Stopped.")
