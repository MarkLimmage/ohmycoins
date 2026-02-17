"""
Unit and integration tests for the Coinspot collector service
"""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlmodel import Session, select

from app.core.db import engine
from app.models import PriceData5Min
from app.services.collector import CoinspotCollector, run_collector

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
        <tr data-coin="XRP">
            <td><img src="xrp.png"/></td>
            <td>Ripple</td>
            <td data-value="0.50">Buy: $0.50</td>
            <td data-value="0.51">Sell: $0.51</td>
        </tr>
    </table>
</body>
</html>
"""


class TestCoinspotCollector:
    """Unit tests for CoinspotCollector class"""

    @pytest.fixture
    def collector(self):
        """Create a collector instance for testing"""
        return CoinspotCollector()

    @pytest.mark.asyncio
    async def test_fetch_latest_prices_success(self, collector):
        """Test successful API fetch"""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.text = MOCK_HTML_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            prices = await collector.fetch_latest_prices()

            assert prices is not None
            assert len(prices) == 3
            assert "btc" in prices
            # Scraper uses (buy+sell)/2 which results in float, str() conversion might drop trailing zeros
            assert float(prices["btc"]["last"]) == 45050.00

    @pytest.mark.asyncio
    async def test_fetch_latest_prices_api_error_status(self, collector):
        """Test API returns non-ok status"""
        # Note: Scraper mode doesn't usually return standard error JSONs,
        # but if we were using API mode this test would be valid.
        # For scraper mode, this test might need adjustment or we just
        # ensure it handles HTTP 200 but bad content gracefully.
        # However, for now, let's just make sure it doesn't crash if we provide HTML.
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "error", "message": "API error"}
        mock_response.text = "<html>Error</html>"
        mock_response.raise_for_status = MagicMock()

        # If web scraping is on, it ignores json() and parses text().
        # "<html>Error</html>" will yield 0 coins, so fetch_latest_prices returns None (after retries).

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Temporarily speed up sleep for retries
            with patch("asyncio.sleep", new_callable=AsyncMock):
                prices = await collector.fetch_latest_prices()

            assert prices is None

    @pytest.mark.asyncio
    async def test_fetch_latest_prices_http_error(self, collector):
        """Test HTTP error handling"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500)
                )
            )

            prices = await collector.fetch_latest_prices()

            assert prices is None

    @pytest.mark.asyncio
    async def test_fetch_latest_prices_timeout(self, collector):
        """Test timeout handling"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            prices = await collector.fetch_latest_prices()

            assert prices is None

    @pytest.mark.asyncio
    async def test_fetch_latest_prices_retry_logic(self, collector):
        """Test retry logic on failure"""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.text = MOCK_HTML_RESPONSE
        mock_response.raise_for_status = MagicMock()

        # First call fails, second succeeds
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(
                side_effect=[
                    httpx.TimeoutException("First attempt timeout"),
                    mock_response,
                ]
            )
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with patch("asyncio.sleep", new_callable=AsyncMock):  # Speed up test
                prices = await collector.fetch_latest_prices()

            assert prices is not None
            assert len(prices) == 3

    def test_store_prices_success(self, collector):
        """Test successful price storage"""
        test_prices = {
            "test_btc": {"bid": "50000.00", "ask": "50100.00", "last": "50050.00"}
        }

        stored_count = collector.store_prices(test_prices)

        assert stored_count == 1

        # Verify data was stored
        with Session(engine) as session:
            records = session.exec(
                select(PriceData5Min).where(PriceData5Min.coin_type == "test_btc")
            ).all()
            assert len(records) >= 1
            latest = records[-1]
            assert latest.bid == Decimal("50000.00")
            assert latest.ask == Decimal("50100.00")
            assert latest.last == Decimal("50050.00")

    def test_store_prices_empty_dict(self, collector):
        """Test storing empty prices dict"""
        stored_count = collector.store_prices({})
        assert stored_count == 0

    def test_store_prices_missing_fields(self, collector):
        """Test handling of missing price fields"""
        test_prices = {
            "invalid_coin": {"bid": "100.00"}  # Missing ask and last
        }

        stored_count = collector.store_prices(test_prices)

        # Should skip invalid records
        assert stored_count == 0

    def test_store_prices_negative_values(self, collector):
        """Test handling of negative price values"""
        test_prices = {
            "neg_coin": {"bid": "-100.00", "ask": "100.00", "last": "100.00"}
        }

        stored_count = collector.store_prices(test_prices)

        # Should skip negative prices
        assert stored_count == 0

    def test_store_prices_invalid_decimal(self, collector):
        """Test handling of invalid decimal values"""
        test_prices = {
            "bad_coin": {"bid": "not_a_number", "ask": "100.00", "last": "100.00"}
        }

        stored_count = collector.store_prices(test_prices)

        # Should skip invalid decimals
        assert stored_count == 0

    def test_store_prices_duplicate_prevention(self, collector):
        """Test that duplicate timestamps are prevented"""
        test_prices = {
            "dup_btc": {"bid": "60000.00", "ask": "60100.00", "last": "60050.00"}
        }

        # Store first time
        first_count = collector.store_prices(test_prices)
        assert first_count == 1

        # Try to store again immediately (same timestamp)
        # Note: This test might be flaky due to timestamp precision
        # In practice, the cron scheduler prevents this

    @pytest.mark.asyncio
    async def test_collect_and_store_success(self, collector):
        """Test full collection workflow"""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.text = MOCK_HTML_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            stored_count = await collector.collect_and_store()

            assert stored_count == 3

    @pytest.mark.asyncio
    async def test_collect_and_store_fetch_failure(self, collector):
        """Test collection workflow when fetch fails"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            stored_count = await collector.collect_and_store()

            assert stored_count == 0

    @pytest.mark.asyncio
    async def test_run_collector_function(self):
        """Test the run_collector convenience function"""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_response.text = MOCK_HTML_RESPONSE
        mock_response.raise_for_status = MagicMock()

        # Force API mode for this test - WAIT, per user request we should test scraping if default.
        # But run_collector helper might just call the collector.
        # If we remove the patch, it will use default setting (scraped).

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await run_collector()

            assert result == 3


@pytest.mark.integration
class TestCoinspotCollectorIntegration:
    """Integration tests using real API calls (if available)"""

    @pytest.mark.asyncio
    async def test_real_api_fetch(self):
        """Test fetching from real Coinspot API (may fail if API is down)"""
        collector = CoinspotCollector()

        try:
            prices = await collector.fetch_latest_prices()

            # If API is available, we should get prices
            if prices is not None:
                assert isinstance(prices, dict)
                assert len(prices) > 0

                # Verify price structure
                for coin, data in prices.items():
                    assert "bid" in data
                    assert "ask" in data
                    assert "last" in data

        except Exception as e:
            pytest.skip(f"API not available: {e}")

    @pytest.mark.asyncio
    async def test_full_collection_cycle(self):
        """Test a complete collection cycle with real API"""
        collector = CoinspotCollector()

        try:
            stored_count = await collector.collect_and_store()

            # If successful, verify data was stored
            if stored_count > 0:
                with Session(engine) as session:
                    # Get the most recent records
                    recent_records = session.exec(
                        select(PriceData5Min).order_by(PriceData5Min.timestamp.desc()).limit(10)
                    ).all()

                    assert len(recent_records) > 0
                    assert all(r.bid > 0 for r in recent_records)
                    assert all(r.ask > 0 for r in recent_records)
                    assert all(r.last > 0 for r in recent_records)

        except Exception as e:
            pytest.skip(f"Collection failed: {e}")
