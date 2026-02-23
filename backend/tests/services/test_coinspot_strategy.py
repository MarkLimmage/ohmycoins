"""
Unit tests for the CoinspotExchangeCollector strategy
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from app.collectors.strategies.exchange_coinspot import CoinspotExchangeCollector

# Sample API response data
MOCK_API_RESPONSE = {
    "status": "ok",
    "prices": {
        "btc": {"bid": "45000.00", "ask": "45100.00", "last": "45050.00"},
        "eth": {"bid": "3000.00", "ask": "3010.00", "last": "3005.00"},
        "xrp": {"bid": "0.50", "ask": "0.51", "last": "0.505"},
    }
}

# Sample HTML response data for scraping
MOCK_HTML_RESPONSE = """
<html>
<body>
    <table>
        <tr data-coin="BTC">
            <td><img src="btc.png"/></td>
            <td>Bitcoin</td>
            <td data-value="45000.00">Buy: $45,000.00</td>
            <td data-value="45100.00">Sell: $45,100.00</td>
        </tr> 
        <tr data-coin="ETH">
            <td><img src="eth.png"/></td>
            <td>Ethereum</td>
            <td data-value="3000.00">Buy: $3,000.00</td>
            <td data-value="3010.00">Sell: $3,010.00</td>
        </tr>
        <tr data-coin="AUD">
             <!-- AUD Should be skipped -->
        </tr>
    </table>
</body>
</html>
"""

@pytest.mark.asyncio
async def test_collect_public_api():
    collector = CoinspotExchangeCollector()
    config = {"use_web_scraping": False}
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_get.return_value = mock_response
        
        results = await collector.collect(config)
        
        assert len(results) == 3
        # Check first item (BTC)
        btc = next(item for item in results if item.coin_type == "btc")
        assert btc.bid == Decimal("45000.00")
        assert btc.ask == Decimal("45100.00")
        assert btc.last == Decimal("45075.00") # Calculated average in new strategy

@pytest.mark.asyncio
async def test_collect_scraping():
    collector = CoinspotExchangeCollector()
    config = {"use_web_scraping": True}
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_HTML_RESPONSE
        mock_get.return_value = mock_response
        
        results = await collector.collect(config)
        
        assert len(results) == 2 # AUD skipped
        # Check BTC
        btc = next(item for item in results if item.coin_type == "btc")
        assert btc.bid == Decimal("45000.00")
        assert btc.ask == Decimal("45100.00")
        assert btc.last == Decimal("45050.00")

