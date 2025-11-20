"""
Trading services for Oh My Coins

This package provides live trading capabilities using the Coinspot API.
"""

from app.services.trading.client import CoinspotTradingClient
from app.services.trading.executor import OrderExecutor, OrderQueue, get_order_queue
from app.services.trading.positions import PositionManager, get_position_manager

__all__ = [
    "CoinspotTradingClient",
    "OrderExecutor",
    "OrderQueue",
    "get_order_queue",
    "PositionManager",
    "get_position_manager",
]
