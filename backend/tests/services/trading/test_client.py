"""
Tests for Coinspot Trading Client
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.trading.client import (
    CoinspotTradingClient,
    CoinspotAPIError,
    CoinspotTradingError
)


class TestCoinspotTradingClient:
    """Test suite for CoinspotTradingClient"""
    
    @pytest.fixture
    def api_credentials(self):
        """Sample API credentials"""
        return {
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret'
        }
    
    @pytest.fixture
    def client(self, api_credentials):
        """Create a trading client instance"""
        return CoinspotTradingClient(
            api_key=api_credentials['api_key'],
            api_secret=api_credentials['api_secret']
        )
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, api_credentials):
        """Test client initializes correctly"""
        client = CoinspotTradingClient(
            api_key=api_credentials['api_key'],
            api_secret=api_credentials['api_secret']
        )
        
        assert client.authenticator is not None
        assert client.authenticator.api_key == api_credentials['api_key']
        assert client.authenticator.api_secret == api_credentials['api_secret']
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test client works as async context manager"""
        async with client as c:
            assert c._session is not None
        
        assert client._session is None
    
    @pytest.mark.asyncio
    async def test_make_request_without_context_manager(self, client):
        """Test making request without context manager raises error"""
        with pytest.raises(CoinspotTradingError, match="context manager"):
            await client._make_request('/test')
    
    @pytest.mark.asyncio
    async def test_market_buy_success(self, client):
        """Test successful market buy order"""
        mock_response = {
            'status': 'ok',
            'id': '12345',
            'market': 'BTC/AUD',
            'rate': '50000.00',
            'coin': '0.02',
            'amount': '1000.00',
            'total': '1000.00'
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.market_buy('BTC', Decimal('1000.00'))
                
                assert result == mock_response
                mock_request.assert_called_once_with(
                    '/my/buy',
                    {'cointype': 'BTC', 'amount': '1000.00'}
                )
    
    @pytest.mark.asyncio
    async def test_market_sell_success(self, client):
        """Test successful market sell order"""
        mock_response = {
            'status': 'ok',
            'id': '67890',
            'market': 'ETH/AUD',
            'rate': '3000.00',
            'coin': '0.5',
            'amount': '1500.00',
            'total': '1500.00'
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.market_sell('ETH', Decimal('0.5'))
                
                assert result == mock_response
                mock_request.assert_called_once_with(
                    '/my/sell',
                    {'cointype': 'ETH', 'amount': '0.5'}
                )
    
    @pytest.mark.asyncio
    async def test_get_orders_all_coins(self, client):
        """Test getting orders for all coins"""
        mock_response = {
            'status': 'ok',
            'buyorders': [],
            'sellorders': []
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.get_orders()
                
                assert result == mock_response
                mock_request.assert_called_once_with('/my/orders', {})
    
    @pytest.mark.asyncio
    async def test_get_orders_specific_coin(self, client):
        """Test getting orders for specific coin"""
        mock_response = {
            'status': 'ok',
            'buyorders': [{'id': '123', 'coin': 'BTC'}],
            'sellorders': []
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.get_orders('BTC')
                
                assert result == mock_response
                mock_request.assert_called_once_with('/my/orders', {'cointype': 'BTC'})
    
    @pytest.mark.asyncio
    async def test_get_order_history(self, client):
        """Test getting order history"""
        mock_response = {
            'status': 'ok',
            'buyorders': [],
            'sellorders': []
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.get_order_history('BTC', limit=50)
                
                assert result == mock_response
                mock_request.assert_called_once_with(
                    '/my/orders/history',
                    {'cointype': 'BTC', 'limit': 50}
                )
    
    @pytest.mark.asyncio
    async def test_cancel_buy_order(self, client):
        """Test cancelling a buy order"""
        mock_response = {'status': 'ok'}
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.cancel_buy_order('12345')
                
                assert result == mock_response
                mock_request.assert_called_once_with('/my/buy/cancel', {'id': '12345'})
    
    @pytest.mark.asyncio
    async def test_cancel_sell_order(self, client):
        """Test cancelling a sell order"""
        mock_response = {'status': 'ok'}
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.cancel_sell_order('67890')
                
                assert result == mock_response
                mock_request.assert_called_once_with('/my/sell/cancel', {'id': '67890'})
    
    @pytest.mark.asyncio
    async def test_get_balances(self, client):
        """Test getting all balances"""
        mock_response = {
            'status': 'ok',
            'balances': {
                'BTC': {'balance': '0.5', 'audvalue': '25000.00'},
                'ETH': {'balance': '2.0', 'audvalue': '6000.00'}
            }
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.get_balances()
                
                assert result == mock_response
                mock_request.assert_called_once_with('/my/balances')
    
    @pytest.mark.asyncio
    async def test_get_balance_specific_coin(self, client):
        """Test getting balance for specific coin"""
        mock_response = {
            'status': 'ok',
            'balance': '0.5',
            'audvalue': '25000.00'
        }
        
        async with client:
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response
                
                result = await client.get_balance('BTC')
                
                assert result == mock_response
                mock_request.assert_called_once_with('/my/balance', {'cointype': 'BTC'})
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, client):
        """Test API error is raised when status is not ok"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            'status': 'error',
            'message': 'Insufficient funds'
        })
        # Make post() return a context manager
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        # Use MagicMock (not AsyncMock) for the callable to return context manager directly
        mock_session.post = MagicMock(return_value=mock_response)
        
        async with client:
            client._session = mock_session
            
            with pytest.raises(CoinspotAPIError, match="Insufficient funds"):
                await client.market_buy('BTC', Decimal('1000000'))
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, client):
        """Test HTTP errors are handled"""
        import aiohttp
        
        # Create async context manager mock that raises error on enter
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection error"))
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = AsyncMock()
        # Use MagicMock (not AsyncMock) for the callable to return context manager directly
        mock_session.post = MagicMock(return_value=mock_cm)
        
        async with client:
            client._session = mock_session
            
            with pytest.raises(CoinspotTradingError, match="HTTP error"):
                await client.market_buy('BTC', Decimal('1000'))
