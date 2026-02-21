from typing import Any, Dict
import pytest
from unittest.mock import AsyncMock, patch
from app.collectors.strategies.market_coinspot import CoinSpotPriceCollector

@pytest.fixture
def collector():
    return CoinSpotPriceCollector()

@pytest.mark.asyncio
async def test_validate_config(collector):
    assert collector.validate_config({"use_web_scraping": True}) is True
    assert collector.validate_config({}) is True

@pytest.mark.asyncio
async def test_test_connection_api_success(collector):
    config = {"use_web_scraping": False}
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await collector.test_connection(config)
        assert result is True

@pytest.mark.asyncio
async def test_test_connection_api_failure(collector):
    config = {"use_web_scraping": False}
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await collector.test_connection(config)
        assert result is False

@pytest.mark.asyncio
async def test_collect_api_success(collector):
    config = {"use_web_scraping": False}
    mock_api_response = {
        "status": "ok",
        "prices": {
            "btc": {"bid": "50000", "ask": "50100", "last": "50050"},
            "eth": {"bid": "3000", "ask": "3010", "last": "3005"}
        }
    }
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_api_response
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await collector.collect(config)
        
        assert len(result) == 2
        btc_item = next(item for item in result if item["coin_type"] == "btc")
        assert btc_item["bid"] == 50000.0
        assert btc_item["ask"] == 50100.0
        assert btc_item["last"] == 50050.0
        assert btc_item["type"] == "price"
        assert btc_item["source"] == "coinspot"

@pytest.mark.asyncio
async def test_collect_scraping_success(collector):
    config = {"use_web_scraping": True}
    mock_html = """
    <html>
        <table>
            <tr data-coin="BTC">
                <td></td>
                <td>Bitcoin</td>
                <td data-value="50000"></td>
                <td data-value="50100"></td>
            </tr>
        </table>
    </html>
    """
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = mock_html
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await collector.collect(config)
        
        assert len(result) == 1
        btc_item = result[0]
        assert btc_item["coin_type"] == "btc"
        assert btc_item["bid"] == 50000.0
        assert btc_item["ask"] == 50100.0
        assert btc_item["last"] == 50050.0 # (50000+50100)/2
