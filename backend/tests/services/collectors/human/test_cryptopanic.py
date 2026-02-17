"""
Integration tests for CryptoPanic collector (Human Ledger).

Tests validate API integration, data collection, validation, and storage.
"""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.collectors.human.cryptopanic import CryptoPanicCollector


@pytest.fixture
def cryptopanic_collector():
    """Create a CryptoPanic collector instance for testing."""
    # Use test API key if available, otherwise mock will be used
    api_key = os.getenv("CRYPTOPANIC_API_KEY", "test_api_key")
    return CryptoPanicCollector(api_key=api_key)


@pytest.fixture
def sample_cryptopanic_response():
    """Sample response from CryptoPanic API."""
    return {
        "count": 2,
        "results": [
            {
                "id": 12345,
                "title": "Bitcoin Surges to New All-Time High",
                "url": "https://example.com/bitcoin-news",
                "source": {"title": "CryptoNews"},
                "published_at": "2026-01-18T10:00:00Z",
                "votes": {
                    "positive": 15,
                    "negative": 2,
                    "important": 5,
                    "liked": 8,
                    "disliked": 1,
                },
                "currencies": [
                    {"code": "BTC", "title": "Bitcoin"},
                ],
                "metadata": {"description": "Bitcoin rally continues"},
            },
            {
                "id": 12346,
                "title": "Ethereum Network Upgrade Delayed",
                "url": "https://example.com/ethereum-news",
                "source": {"title": "BlockchainToday"},
                "published_at": "2026-01-18T09:30:00Z",
                "votes": {
                    "positive": 3,
                    "negative": 12,
                    "important": 2,
                    "liked": 1,
                    "disliked": 8,
                },
                "currencies": [
                    {"code": "ETH", "title": "Ethereum"},
                ],
                "metadata": {"description": "Network crash concerns"},
            },
        ],
    }


class TestCryptoPanicCollectorIntegration:
    """Integration test suite for CryptoPanic collector."""

    def test_initialization(self, cryptopanic_collector):
        """Test collector initialization with API key."""
        assert cryptopanic_collector.name == "cryptopanic_api"
        assert cryptopanic_collector.ledger == "human"
        assert cryptopanic_collector.base_url == "https://cryptopanic.com/api/v1"
        assert cryptopanic_collector.api_key is not None

    def test_initialization_without_api_key(self):
        """Test collector initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="CryptoPanic API key required"):
                CryptoPanicCollector(api_key=None)

    @pytest.mark.asyncio
    async def test_collect_success(self, cryptopanic_collector, sample_cryptopanic_response):
        """Test successful data collection from CryptoPanic API."""
        # Mock the fetch_json method
        cryptopanic_collector.fetch_json = AsyncMock(return_value=sample_cryptopanic_response)

        data = await cryptopanic_collector.collect()

        assert len(data) == 2
        assert all(isinstance(item, dict) for item in data)

        # Verify first article (bullish sentiment)
        article1 = data[0]
        assert article1["title"] == "Bitcoin Surges to New All-Time High"
        assert article1["url"] == "https://example.com/bitcoin-news"
        assert article1["source"] == "CryptoNews"
        assert article1["sentiment"] == "bullish"
        assert article1["sentiment_score"] > 0
        assert "BTC" in article1["currencies"]

        # Verify second article (bearish sentiment)
        article2 = data[1]
        assert article2["title"] == "Ethereum Network Upgrade Delayed"
        assert article2["sentiment"] == "bearish"
        assert article2["sentiment_score"] < 0
        assert "ETH" in article2["currencies"]

    @pytest.mark.asyncio
    async def test_collect_handles_empty_response(self, cryptopanic_collector):
        """Test collection handles empty API response gracefully."""
        cryptopanic_collector.fetch_json = AsyncMock(return_value={"results": []})

        data = await cryptopanic_collector.collect()

        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_validate_data_success(self, cryptopanic_collector):
        """Test data validation accepts valid data."""
        valid_data = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "TestSource",
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "collected_at": datetime.now(timezone.utc),
            }
        ]

        validated = await cryptopanic_collector.validate_data(valid_data)

        assert len(validated) == 1
        assert validated[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_validate_data_filters_invalid(self, cryptopanic_collector):
        """Test data validation filters out invalid records."""
        invalid_data = [
            {"title": "Valid Article", "url": "https://example.com/valid"},
            {"title": "", "url": "https://example.com/no-title"},  # Missing title
            {"title": "No URL Article", "url": None},  # Missing URL
            {"title": "Invalid Score", "url": "https://example.com/test", "sentiment_score": 5.0},  # Out of range
        ]

        validated = await cryptopanic_collector.validate_data(invalid_data)

        # First and last records should pass (last has invalid score set to None)
        assert len(validated) == 2
        assert validated[0]["title"] == "Valid Article"
        assert validated[1]["title"] == "Invalid Score"
        assert validated[1]["sentiment_score"] is None  # Invalid score set to None
