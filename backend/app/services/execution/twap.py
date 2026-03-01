from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .base import ExecutionStrategy


class TWAPStrategy(ExecutionStrategy):
    """
    Time-Weighted Average Price (TWAP) Strategy.
    Splits an order into even chunks executed at regular intervals over a specified duration.

    Parameters required in order.parameters:
    - duration_minutes (int): Total duration of the execution.
    - interval_minutes (int): Time between child orders.
      OR
    - number_of_slices (int): Number of child orders.
    """

    def generate_schedule(self) -> list[tuple[datetime, Decimal]]:
        params = self.order.parameters
        total_quantity = self.order.total_quantity
        start_time = datetime.now(timezone.utc)  # Default to starting now

        if "start_time" in params:
            # parsing start_time not implemented for brevity, assuming datetime object or ISO string if coming from API
            # For now, let's stick to simple relative start
            pass

        duration_minutes = params.get("duration_minutes", 60)

        # Determine number of slices
        if "number_of_slices" in params:
            num_slices = params["number_of_slices"]
            interval_minutes = duration_minutes / num_slices
        else:
            interval_minutes = params.get("interval_minutes", 5)
            if interval_minutes <= 0:
                interval_minutes = 5
            num_slices = int(duration_minutes / interval_minutes)

        if num_slices <= 0:
            num_slices = 1
            slice_quantity = total_quantity
        else:
            # We use quantize later, keeping high precision for now or typical 8 decimals
            slice_quantity = total_quantity / Decimal(num_slices)

        schedule = []
        current_time = start_time
        interval_delta = timedelta(minutes=interval_minutes)

        for _ in range(num_slices):
            schedule.append((current_time, slice_quantity))
            current_time += interval_delta

        return schedule
