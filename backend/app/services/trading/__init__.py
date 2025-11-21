"""
Trading services for Oh My Coins

This package provides live trading capabilities using the Coinspot API.

Phase 6 Components:
- Weeks 1-2: Trading client, order execution, position management
- Weeks 3-4: Algorithm execution, scheduling, safety, audit trail
"""

from app.services.trading.client import CoinspotTradingClient
from app.services.trading.executor import OrderExecutor, OrderQueue, get_order_queue
from app.services.trading.positions import PositionManager, get_position_manager
from app.services.trading.safety import TradingSafetyManager, get_safety_manager, SafetyViolation
from app.services.trading.recorder import TradeRecorder, get_trade_recorder
from app.services.trading.algorithm_executor import (
    AlgorithmExecutor,
    TradingAlgorithm,
    get_algorithm_executor
)
from app.services.trading.scheduler import ExecutionScheduler, get_execution_scheduler

__all__ = [
    # Weeks 1-2: Core trading infrastructure
    "CoinspotTradingClient",
    "OrderExecutor",
    "OrderQueue",
    "get_order_queue",
    "PositionManager",
    "get_position_manager",
    "TradingSafetyManager",
    "get_safety_manager",
    "SafetyViolation",
    "TradeRecorder",
    "get_trade_recorder",
    "AlgorithmExecutor",
    "TradingAlgorithm",
    "get_algorithm_executor",
    "ExecutionScheduler",
    "get_execution_scheduler",
]
