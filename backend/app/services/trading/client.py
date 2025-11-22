"""
Coinspot Trading API Client

This module provides a client for executing trades on the Coinspot exchange.
It handles buy/sell orders, order status, and balance queries.
"""
import logging
from typing import Any
from decimal import Decimal

import aiohttp

from app.services.coinspot_auth import CoinspotAuthenticator
from app.services.trading.exceptions import CoinspotTradingError, CoinspotAPIError

logger = logging.getLogger(__name__)


class CoinspotTradingClient:
    """
    Client for interacting with Coinspot trading API
    
    Provides methods for:
    - Market buy/sell orders
    - Order status queries
    - Balance queries
    - Order management
    """
    
    BASE_URL = "https://www.coinspot.com.au/api/v2"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Coinspot trading client
        
        Args:
            api_key: Coinspot API key
            api_secret: Coinspot API secret
        """
        self.authenticator = CoinspotAuthenticator(api_key, api_secret)
        self._session: aiohttp.ClientSession | None = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _make_request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Make an authenticated request to Coinspot API
        
        Args:
            endpoint: API endpoint (e.g., '/my/buy')
            data: Request data
            
        Returns:
            API response as dictionary
            
        Raises:
            CoinspotAPIError: If API returns an error
        """
        if not self._session:
            raise CoinspotTradingError("Client must be used as async context manager")
        
        headers, payload = self.authenticator.prepare_request(data)
        url = f"{self.BASE_URL}{endpoint}"
        
        logger.debug(f"Making request to {url}")
        
        try:
            async with self._session.post(url, headers=headers, json=payload) as response:
                response_data = await response.json()
                
                # Check for API errors
                if response_data.get('status') != 'ok':
                    error_msg = response_data.get('message', 'Unknown error')
                    logger.error(f"Coinspot API error: {error_msg}")
                    raise CoinspotAPIError(f"API error: {error_msg}")
                
                return response_data
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error making request to {url}: {e}")
            raise CoinspotTradingError(f"HTTP error: {e}")
    
    async def market_buy(
        self,
        coin_type: str,
        amount_aud: Decimal
    ) -> dict[str, Any]:
        """
        Execute a market buy order
        
        Args:
            coin_type: Cryptocurrency to buy (e.g., 'BTC', 'ETH')
            amount_aud: Amount in AUD to spend
            
        Returns:
            Order response with id, market, rate, coin, amount, total
            
        Raises:
            CoinspotAPIError: If API returns an error
        """
        data = {
            'cointype': coin_type,
            'amount': str(amount_aud)
        }
        
        logger.info(f"Placing market buy order: {amount_aud} AUD worth of {coin_type}")
        response = await self._make_request('/my/buy', data)
        
        logger.info(f"Buy order placed successfully: {response.get('id')}")
        return response
    
    async def market_sell(
        self,
        coin_type: str,
        amount: Decimal
    ) -> dict[str, Any]:
        """
        Execute a market sell order
        
        Args:
            coin_type: Cryptocurrency to sell (e.g., 'BTC', 'ETH')
            amount: Amount of cryptocurrency to sell
            
        Returns:
            Order response with id, market, rate, coin, amount, total
            
        Raises:
            CoinspotAPIError: If API returns an error
        """
        data = {
            'cointype': coin_type,
            'amount': str(amount)
        }
        
        logger.info(f"Placing market sell order: {amount} {coin_type}")
        response = await self._make_request('/my/sell', data)
        
        logger.info(f"Sell order placed successfully: {response.get('id')}")
        return response
    
    async def get_orders(
        self,
        coin_type: str | None = None
    ) -> dict[str, Any]:
        """
        Get open and completed orders
        
        Args:
            coin_type: Filter by coin type (optional)
            
        Returns:
            Dictionary with 'buyorders' and 'sellorders' lists
        """
        data = {}
        if coin_type:
            data['cointype'] = coin_type
        
        logger.debug(f"Fetching orders for {coin_type or 'all coins'}")
        response = await self._make_request('/my/orders', data)
        
        return response
    
    async def get_order_history(
        self,
        coin_type: str | None = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """
        Get order history
        
        Args:
            coin_type: Filter by coin type (optional)
            limit: Maximum number of orders to return (default 100)
            
        Returns:
            Dictionary with 'buyorders' and 'sellorders' lists
        """
        data = {}
        if coin_type:
            data['cointype'] = coin_type
        if limit:
            data['limit'] = limit
        
        logger.debug(f"Fetching order history for {coin_type or 'all coins'}, limit={limit}")
        response = await self._make_request('/my/orders/history', data)
        
        return response
    
    async def cancel_buy_order(self, order_id: str) -> dict[str, Any]:
        """
        Cancel a buy order
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            Cancellation response
        """
        data = {'id': order_id}
        
        logger.info(f"Cancelling buy order: {order_id}")
        response = await self._make_request('/my/buy/cancel', data)
        
        logger.info(f"Buy order cancelled successfully: {order_id}")
        return response
    
    async def cancel_sell_order(self, order_id: str) -> dict[str, Any]:
        """
        Cancel a sell order
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            Cancellation response
        """
        data = {'id': order_id}
        
        logger.info(f"Cancelling sell order: {order_id}")
        response = await self._make_request('/my/sell/cancel', data)
        
        logger.info(f"Sell order cancelled successfully: {order_id}")
        return response
    
    async def get_balances(self) -> dict[str, Any]:
        """
        Get account balances for all coins
        
        Returns:
            Dictionary with balance information for each coin
        """
        logger.debug("Fetching account balances")
        response = await self._make_request('/my/balances')
        
        return response
    
    async def get_balance(self, coin_type: str) -> dict[str, Any]:
        """
        Get balance for a specific coin
        
        Args:
            coin_type: Coin to get balance for (e.g., 'BTC')
            
        Returns:
            Balance information for the specified coin
        """
        data = {'cointype': coin_type}
        
        logger.debug(f"Fetching balance for {coin_type}")
        response = await self._make_request('/my/balance', data)
        
        return response
