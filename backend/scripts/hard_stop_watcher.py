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


if __name__ == "__main__":
    try:
        from app.services.trading.watcher import HardStopWatcher
        # We can pass config if needed, but defaults are fine for now
        watcher = HardStopWatcher()
        asyncio.run(watcher.start()) # type: ignore
    except KeyboardInterrupt:
        logger.info("Hard Stop Watcher Stopped.")
