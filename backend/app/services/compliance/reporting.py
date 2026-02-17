# mypy: ignore-errors
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExecutionEvent(BaseModel):
    """
    Represents a single fill or relevant market event during execution.
    """
    timestamp: datetime
    event_type: str  # e.g., "fill", "market_update"
    price: Decimal
    volume: Decimal = Decimal("0")

class ExecutionReport(BaseModel):
    """
    Post-trade analysis report containing execution metrics.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trade_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: Decimal
    arrival_mid_price: Decimal
    avg_fill_price: Decimal
    slippage_bps: float
    market_impact_bps: float | None = None
    execution_timeline: list[ExecutionEvent] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SlippageCalculator:
    """
    Calculates execution quality metrics.
    """

    @staticmethod
    def calculate_slippage_bps(avg_fill_price: Decimal, arrival_mid_price: Decimal) -> float:
        """
        Calculates slippage in Basis Points (bps).
        Formula: ((Avg Fill Price - Arrival Mid Price) / Arrival Mid Price) * 10000
        
        Args:
            avg_fill_price: The weighted average price of all fills.
            arrival_mid_price: The market mid-price when the parent order arrived.
        
        Returns:
            float: Slippage in basis points.
        """
        if arrival_mid_price == 0:
            return 0.0

        slippage = (avg_fill_price - arrival_mid_price) / arrival_mid_price
        return float(slippage * 10000)

    @staticmethod
    def generate_report(
        trade_id: str,
        symbol: str,
        side: str,
        quantity: Decimal,
        arrival_mid_price: Decimal,
        execution_events: list[ExecutionEvent]
    ) -> ExecutionReport:
        """
        Generates a full execution report from a list of execution events.
        """

        fill_events = [e for e in execution_events if e.event_type == "fill"]
        total_volume = sum(e.volume for e in fill_events)

        if total_volume == 0:
             # If no fills, assume avg_fill_price is 0 or same as arrival (no trade)?
             # Ideally this shouldn't happen for a "completed" trade report.
             avg_fill_price = Decimal(0)
        else:
             avg_fill_price = sum(e.price * e.volume for e in fill_events) / total_volume

        slippage_bps = SlippageCalculator.calculate_slippage_bps(avg_fill_price, arrival_mid_price)

        return ExecutionReport(
            id=f"rep-{uuid.uuid4()}",
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            arrival_mid_price=arrival_mid_price,
            avg_fill_price=avg_fill_price,
            slippage_bps=slippage_bps,
            execution_timeline=execution_events
        )
