from abc import ABC, abstractmethod
from typing import Any
from decimal import Decimal

class BaseExchange(ABC):
    """
    Abstract base class for exchange clients (e.g. CoinSpot, PaperExchange).
    """

    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry"""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass

    @abstractmethod
    async def market_buy(
        self,
        coin_type: str,
        amount_aud: Decimal
    ) -> dict[str, Any]:
        """Execute a market buy order using AUD amount"""
        pass

    @abstractmethod
    async def market_sell(
        self,
        coin_type: str,
        amount: Decimal
    ) -> dict[str, Any]:
        """Execute a market sell order using Coin amount"""
        pass

    @abstractmethod
    async def limit_buy(
        self,
        coin_type: str,
        amount_aud: Decimal,
        rate: Decimal
    ) -> dict[str, Any]:
        """Execute a limit buy order"""
        pass

    @abstractmethod
    async def limit_sell(
        self,
        coin_type: str,
        amount: Decimal,
        rate: Decimal
    ) -> dict[str, Any]:
        """Execute a limit sell order"""
        pass

    @abstractmethod
    async def get_orders(
        self,
        coin_type: str | None = None
    ) -> dict[str, Any]:
        """Get open and completed orders"""
        pass

    @abstractmethod
    async def get_order_history(
        self,
        coin_type: str | None = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """Get order history"""
        pass

    @abstractmethod
    async def cancel_buy_order(self, order_id: str) -> dict[str, Any]:
        """Cancel a buy order"""
        pass

    @abstractmethod
    async def cancel_sell_order(self, order_id: str) -> dict[str, Any]:
        """Cancel a sell order"""
        pass

    @abstractmethod
    async def get_balances(self) -> dict[str, Any]:
        """Get account balances for all coins"""
        pass
    
    @abstractmethod
    async def get_balance(self, coin_type: str) -> dict[str, Any]:
        """Get balance for a specific coin"""
        pass
