# mypy: ignore-errors
import asyncio
import logging
from decimal import Decimal

import redis.asyncio as redis
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import Position, PriceData5Min
from app.services.trading.safety import TradingSafetyManager

logger = logging.getLogger(__name__)

REDIS_KEY_INITIAL_EQUITY = "omc:initial_equity"


class HardStopWatcher:
    def __init__(
        self, check_interval: int = 5, drawdown_limit_pct: Decimal = Decimal("0.95")
    ):
        self.check_interval = check_interval
        self.drawdown_limit_pct = drawdown_limit_pct
        self.redis_client = None

    async def connect_redis(self):
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )

    async def get_latest_prices(self, session: Session) -> dict[str, Decimal]:
        """
        Fetch the latest price for each coin type from PriceData5Min.
        Returns: Dict[coin_type, price]
        """
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

    async def calculate_total_equity(self, session: Session) -> Decimal:
        """
        Calculate the total equity (Positions only) of ALL users.
        """
        total_equity = Decimal("0")

        # Total Position Value
        positions = session.exec(select(Position)).all()
        if not positions:
            return total_equity

        prices = await self.get_latest_prices(session)

        for pos in positions:
            # Use market price if available, else fallback to avg price (safety fallback)
            price = prices.get(pos.coin_type, pos.average_price)
            total_equity += pos.quantity * price

        return total_equity

    async def check_equity(self, session: Session) -> bool:
        """
        Checks equity against hard stop.
        Returns True if Hard Stop Triggered, False otherwise.
        """
        await self.connect_redis()

        safety = TradingSafetyManager(session)

        # Check Global Kill Switch Status first
        is_active = await self.redis_client.get("omc:emergency_stop")
        if is_active == "true":
            logger.debug("Emergency Stop already active.")
            return True  # Already stopped

        current_equity = await self.calculate_total_equity(session)

        # Get Initial Equity
        initial_equity_str = await self.redis_client.get(REDIS_KEY_INITIAL_EQUITY)

        if not initial_equity_str:
            # Initialize
            if current_equity > 0:
                await self.redis_client.set(
                    REDIS_KEY_INITIAL_EQUITY, str(current_equity)
                )
                logger.info(f"Initialized Base Equity: {current_equity:.2f} AUD")
            else:
                logger.warning("Total Equity is 0. Strategies not deployed?")
            return False

        initial_equity = Decimal(initial_equity_str)

        # Check Drawdown
        threshold = initial_equity * self.drawdown_limit_pct

        if current_equity < threshold:
            logger.critical(
                f"HARD STOP TRIGGERED! Equity {current_equity:.2f} < {threshold:.2f} "
                f"(Initial: {initial_equity:.2f})"
            )

            # ACTIVATE KILL SWITCH
            await safety.activate_emergency_stop()
            return True

        else:
            logger.debug(f"Equity Safe: {current_equity:.2f} (Limit: {threshold:.2f})")
            return False

    async def start(self):
        logger.info("Starting Hard Stop Watcher Service...")
        await self.connect_redis()

        while True:
            try:
                with Session(engine) as session:
                    await self.check_equity(session)
            except Exception as e:
                logger.error(f"Error in Watcher Loop: {e}")

            await asyncio.sleep(self.check_interval)
