from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class BacktestConfig(BaseModel):
    """Configuration for a backtest run"""

    strategy_name: str
    coin_type: str
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Decimal("10000.0")
    parameters: dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class BacktestResult(BaseModel):
    """Results of a backtest run"""

    strategy_name: str
    coin_type: str
    total_return: float
    total_return_percent: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)
