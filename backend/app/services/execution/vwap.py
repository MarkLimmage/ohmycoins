# mypy: ignore-errors
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.db import engine
from app.models import PriceData5Min

from .base import ExecutionStrategy


class VWAPStrategy(ExecutionStrategy):
    """
    Volume-Weighted Average Price (VWAP) Strategy.
    Splits order based on historical volume profile to match market liquidity.

    Parameters:
    - duration_minutes (int): Total duration.
    - interval_minutes (int): Bucket size (default 5).
    """

    def generate_schedule(self) -> list[tuple[datetime, Decimal]]:
        params = self.order.parameters
        total_quantity = self.order.total_quantity
        symbol = self.order.symbol # This corresponds to coin_type in PriceData5Min

        start_time = datetime.now(timezone.utc)
        duration_minutes = params.get("duration_minutes", 60)
        bucket_minutes = params.get("interval_minutes", 5)

        # Snap start_time to next bucket? Or just run from now.
        # For VWAP, we typically want to align with historical bars (e.g. 5 min bars).
        # We'll generate buckets starting from start_time.

        buckets = []
        current_time = start_time
        end_time = start_time + timedelta(minutes=duration_minutes)

        while current_time < end_time:
            buckets.append(current_time)
            current_time += timedelta(minutes=bucket_minutes)

        if not buckets:
            return []

        # Calculate weights based on historical volume
        weights = self._get_volume_profile(symbol, buckets)

        total_weight = sum(weights)
        if total_weight == 0:
            total_weight = Decimal("1")
            weights = [Decimal("1") for _ in weights]

        schedule = []
        for i, bucket_time in enumerate(buckets):
            weight = weights[i] / total_weight
            qty = total_quantity * weight
            schedule.append((bucket_time, qty))

        return schedule

    def _get_volume_profile(self, symbol: str, buckets: list[datetime]) -> list[Decimal]:
        """
        Fetch historical volume for the time-of-day of each bucket.
        """
        # Check if PriceData5Min has 'volume' field.
        # Currently the model might not have volume, in which case we fallback to flat profile.
        if not hasattr(PriceData5Min, "volume"):
            # Log warning theoretically
            return [Decimal("1") for _ in buckets]

        weights = []
        with Session(engine) as session:
            for bucket_time in buckets:
                # Query average volume for this hour/minute
                # This is a simplified profile lookup
                try:
                    statement = (
                        select(func.avg(PriceData5Min.volume)) # getattr to avoid static check error if any
                        .where(PriceData5Min.coin_type == symbol)
                        .where(func.extract('hour', PriceData5Min.timestamp) == bucket_time.hour)
                        .where(func.extract('minute', PriceData5Min.timestamp) == bucket_time.minute)
                    )
                    avg_vol = session.exec(statement).first()
                    weights.append(Decimal(str(avg_vol)) if avg_vol else Decimal("1"))
                except Exception:
                    # If query fails (e.g. column missing in DB even if getattr passed class check), fallback
                    weights.append(Decimal("1"))

        return weights
