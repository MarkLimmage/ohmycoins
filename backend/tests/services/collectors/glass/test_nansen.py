"""
Integration tests for Nansen collector (Glass Ledger).

Tests validate API integration, data collection, validation, and smart money tracking.
"""

import os
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.collectors.glass.nansen import NansenCollector


@pytest.fixture
def nansen_collector():
    """Create a Nansen collector instance for testing."""
    # Use test API key if available, otherwise mock will be used
    api_key = os.getenv("NANSEN_API_KEY", "test_api_key")
    return NansenCollector(api_key=api_key)


@pytest.fixture
def sample_nansen_response():
    """Sample response from Nansen API for smart money flows."""
    return {
        "netFlowUsd": 15000000.50,
        "buyingWallets": [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x567890abcdef1234567890abcdef1234567890ab",
        ],
        "sellingWallets": [
            "0xfedcba0987654321fedcba0987654321fedcba09",
        ],
    }


class TestNansenCollectorIntegration:
    """Integration test suite for Nansen collector."""

    def test_initialization(self, nansen_collector):
        """Test collector initialization with API key."""
        assert nansen_collector.name == "nansen_api"
        assert nansen_collector.ledger == "glass"
        assert nansen_collector.base_url == "https://api.nansen.ai/v1"
        assert nansen_collector.api_key is not None
        assert len(nansen_collector.TRACKED_TOKENS) >= 5

    def test_initialization_without_api_key(self):
        """Test collector initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Nansen API key required"):
                NansenCollector(api_key=None)

    @pytest.mark.asyncio
    async def test_collect_success(self, nansen_collector, sample_nansen_response):
        """Test successful data collection from Nansen API."""
        # Mock the fetch_json method
        nansen_collector.fetch_json = AsyncMock(return_value=sample_nansen_response)

        # Temporarily reduce tokens for testing
        original_tokens = nansen_collector.TRACKED_TOKENS
        nansen_collector.TRACKED_TOKENS = ["ETH", "BTC"]

        try:
            data = await nansen_collector.collect()

            assert len(data) == 2  # One for each tracked token
            assert all(isinstance(item, dict) for item in data)

            # Verify first token data
            eth_data = data[0]
            assert eth_data["token"] == "ETH"
            assert eth_data["net_flow_usd"] == Decimal("15000000.50")
            assert eth_data["buying_wallet_count"] == 3
            assert eth_data["selling_wallet_count"] == 1
            assert len(eth_data["buying_wallets"]) <= 10  # Top 10 only
            assert len(eth_data["selling_wallets"]) <= 10

        finally:
            nansen_collector.TRACKED_TOKENS = original_tokens

    @pytest.mark.asyncio
    async def test_collect_handles_empty_response(self, nansen_collector):
        """Test collection handles empty API response gracefully."""
        nansen_collector.fetch_json = AsyncMock(return_value={})
        nansen_collector.TRACKED_TOKENS = ["ETH"]

        data = await nansen_collector.collect()

        # Empty response is skipped (logged as warning)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_collect_handles_api_error_for_single_token(self, nansen_collector):
        """Test collection continues when one token fails."""
        call_count = {"count": 0}

        async def mock_fetch_with_error(*_args, **_kwargs):
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise Exception("API error for first token")
            return {
                "netFlowUsd": 5000000.0,
                "buyingWallets": ["0xabc"],
                "sellingWallets": [],
            }

        nansen_collector.fetch_json = AsyncMock(side_effect=mock_fetch_with_error)
        nansen_collector.TRACKED_TOKENS = ["ETH", "BTC"]

        data = await nansen_collector.collect()

        # Should have collected second token despite first failing
        assert len(data) == 1
        assert data[0]["token"] == "BTC"

    @pytest.mark.asyncio
    async def test_validate_data_success(self, nansen_collector):
        """Test data validation accepts valid data."""
        valid_data = [
            {
                "token": "ETH",
                "net_flow_usd": Decimal("1000000.0"),
                "buying_wallet_count": 5,
                "selling_wallet_count": 2,
                "collected_at": datetime.now(timezone.utc),
            }
        ]

        validated = await nansen_collector.validate_data(valid_data)

        assert len(validated) == 1
        assert validated[0]["token"] == "ETH"

    @pytest.mark.asyncio
    async def test_validate_data_filters_invalid(self, nansen_collector):
        """Test data validation filters out invalid records."""
        invalid_data = [
            {"token": "ETH", "net_flow_usd": Decimal("1000"), "buying_wallet_count": 5, "selling_wallet_count": 2},
            {"token": "", "net_flow_usd": Decimal("1000")},  # Missing token
            {"token": "BTC", "net_flow_usd": "invalid"},  # Invalid net_flow
            {"token": "DAI", "net_flow_usd": Decimal("500"), "buying_wallet_count": -1},  # Invalid count
        ]

        validated = await nansen_collector.validate_data(invalid_data)

        assert len(validated) == 1  # Only first one should pass
        assert validated[0]["token"] == "ETH"
