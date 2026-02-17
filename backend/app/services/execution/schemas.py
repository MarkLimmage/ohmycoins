from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionStrategyType(str, Enum):
    TWAP = "TWAP"
    VWAP = "VWAP"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class AlgoOrderStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"

class AlgoOrderBase(BaseModel):
    symbol: str
    side: OrderSide
    total_quantity: Decimal
    strategy: ExecutionStrategyType
    parameters: dict[str, Any] = Field(default_factory=dict)

class AlgoOrderCreate(AlgoOrderBase):
    pass

class AlgoOrder(AlgoOrderBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AlgoOrderStatus = AlgoOrderStatus.PENDING

    filled_quantity: Decimal = Decimal("0")
    average_price: Decimal | None = None

    # Execution details
    child_orders: list[str] = Field(default_factory=list) # List of child order IDs
    next_schedule_index: int = 0

    model_config = ConfigDict(from_attributes=True)
