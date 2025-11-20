"""
Trading services for Oh My Coins

This package provides live trading capabilities using the Coinspot API.
"""

from app.services.trading.client import CoinspotTradingClient

__all__ = ["CoinspotTradingClient"]
