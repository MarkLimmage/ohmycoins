"""
Integration tests for Newscatcher collector (Human Ledger).

Tests validate API integration, data collection, validation, and storage.
"""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.collectors.human.newscatcher import NewscatcherCollector


@pytest.fixture
def newscatcher_collector():
    """Create a Newscatcher collector instance for testing."""
    # Use test API key if available, otherwise mock will be used
    api_key = os.getenv("NEWSCATCHER_API_KEY", "test_api_key")
    return NewscatcherCollector(api_key=api_key)


@pytest.fixture
def sample_newscatcher_response():
    """Sample response from Newscatcher API."""
    return {
        "status": "ok",
        "total_hits": 2,
        "articles": [
            {
                "title": "Bitcoin Reaches New Heights in Q1 2026",
                "summary": "Bitcoin continues its bullish trend with strong institutional support.",
                "link": "https://cryptonews.example.com/bitcoin-heights",
                "clean_url": "cryptonews.example.com",
                "published_date": "2026-01-18T12:00:00Z",
                "sentiment": "positive",
            },
            {
                "title": "Ethereum Gas Fees Spark Community Debate",
                "summary": "Rising transaction costs concern Ethereum users.",
                "link": "https://blockchain.example.com/eth-fees",
                "clean_url": "blockchain.example.com",
                "published_date": "2026-01-18T11:30:00Z",
                "sentiment": "neutral",
            },
        ],
    }


class TestNewscatcherCollectorIntegration:
    """Integration test suite for Newscatcher collector."""

    def test_initialization(self, newscatcher_collector):
        """Test collector initialization with API key."""
        assert newscatcher_collector.name == "newscatcher_api"
        assert newscatcher_collector.ledger == "human"
        assert newscatcher_collector.base_url == "https://v3-api.newscatcherapi.com/api"
        assert newscatcher_collector.api_key is not None

    def test_initialization_without_api_key(self):
        """Test collector initializes gracefully without API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Should initialize without raising, with API key availability set to False
            collector = NewscatcherCollector(api_key=None)
            assert collector.name == "newscatcher_api"
            assert not collector._api_key_available

    @pytest.mark.asyncio
    async def test_collect_without_api_key(self):
        """Test collection gracefully skips when API key is unavailable."""
        with patch.dict(os.environ, {}, clear=True):
            collector = NewscatcherCollector(api_key=None)
            data = await collector.collect()
            assert data == []
            assert not collector._api_key_available

    @pytest.mark.asyncio
    async def test_collect_success(self, newscatcher_collector, sample_newscatcher_response):
        """Test successful data collection from Newscatcher API."""
        # Mock the fetch_json method
        newscatcher_collector.fetch_json = AsyncMock(return_value=sample_newscatcher_response)

        data = await newscatcher_collector.collect()

        assert len(data) == 2
        assert all(isinstance(item, dict) for item in data)

        # Verify first article
        article1 = data[0]
        assert article1["title"] == "Bitcoin Reaches New Heights in Q1 2026"
        assert article1["url"] == "https://cryptonews.example.com/bitcoin-heights"
        assert article1["source"] == "cryptonews.example.com"
        assert article1["sentiment"] == "bullish"  # Mapped from "positive"
        assert article1["summary"] == "Bitcoin continues its bullish trend with strong institutional support."

        # Verify second article
        article2 = data[1]
        assert article2["title"] == "Ethereum Gas Fees Spark Community Debate"
        assert article2["sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_collect_handles_empty_response(self, newscatcher_collector):
        """Test collection handles empty API response gracefully."""
        newscatcher_collector.fetch_json = AsyncMock(return_value={"articles": []})

        data = await newscatcher_collector.collect()

        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_collect_handles_no_articles_key(self, newscatcher_collector):
        """Test collection handles missing articles key in response."""
        newscatcher_collector.fetch_json = AsyncMock(return_value={"status": "ok"})

        data = await newscatcher_collector.collect()

        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_validate_data_success(self, newscatcher_collector):
        """Test data validation accepts valid data."""
        valid_data = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "source": "example.com",
                "sentiment": "neutral",
                "collected_at": datetime.now(timezone.utc),
            }
        ]

        validated = await newscatcher_collector.validate_data(valid_data)

        assert len(validated) == 1
        assert validated[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_validate_data_filters_invalid(self, newscatcher_collector):
        """Test data validation filters out invalid records."""
        invalid_data = [
            {"title": "Valid Article", "url": "https://example.com/valid"},
            {"title": "", "url": "https://example.com/no-title"},  # Missing title
            {"title": "No URL Article", "url": None},  # Missing URL
        ]

        validated = await newscatcher_collector.validate_data(invalid_data)

        assert len(validated) == 1  # Only first one should pass
        assert validated[0]["title"] == "Valid Article"
