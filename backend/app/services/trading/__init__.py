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
from app.services.trading.algorithm_executor import (
    AlgorithmExecutor,
    get_algorithm_executor,
    AlgorithmExecutionError,
)
from app.services.trading.scheduler import (
    AlgorithmScheduler,
    get_algorithm_scheduler,
    start_algorithm_scheduler,
    stop_algorithm_scheduler,
    AlgorithmSchedulerError,
)
from app.services.trading.safety import (
    SafetyManager,
    get_safety_manager,
    SafetyViolationError,
)
from app.services.trading.recorder import (
    TradeRecorder,
    get_trade_recorder,
    TradeRecordingError,
)

__all__ = [
    # Weeks 1-2: Core trading infrastructure
    "CoinspotTradingClient",
    "OrderExecutor",
    "OrderQueue",
    "get_order_queue",
    "PositionManager",
    "get_position_manager",
    # Weeks 3-4: Algorithm execution and management
    "AlgorithmExecutor",
    "get_algorithm_executor",
    "AlgorithmExecutionError",
    "AlgorithmScheduler",
    "get_algorithm_scheduler",
    "start_algorithm_scheduler",
    "stop_algorithm_scheduler",
    "AlgorithmSchedulerError",
    "SafetyManager",
    "get_safety_manager",
    "SafetyViolationError",
    "TradeRecorder",
    "get_trade_recorder",
    "TradeRecordingError",
]
