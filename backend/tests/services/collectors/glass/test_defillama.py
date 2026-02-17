"""
Tests for DeFiLlama collector (Glass Ledger).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.collectors.glass.defillama import DeFiLlamaCollector


@pytest.fixture
def defillama_collector():
    """Create a DeFiLlama collector instance for testing."""
    return DeFiLlamaCollector()


@pytest.fixture
def sample_protocol_data():
    """Sample protocol data from DeFiLlama API."""
    return {
        "tvl": [
            {"totalLiquidityUSD": 25000000000.0}
        ]
    }


@pytest.fixture
def sample_fees_data():
    """Sample fees data from DeFiLlama API."""
    return {
        "total24h": 5000000.0,
        "totalRevenue24h": 2500000.0,
    }


class TestDeFiLlamaCollector:
    """Test suite for DeFiLlama collector."""

    def test_initialization(self, defillama_collector):
        """Test collector initialization."""
        assert defillama_collector.name == "defillama_api"
        assert defillama_collector.ledger == "glass"
        assert defillama_collector.base_url == "https://api.llama.fi"
        assert len(defillama_collector.MONITORED_PROTOCOLS) >= 20

    @pytest.mark.asyncio
    async def test_collect_success(
        self, defillama_collector, sample_protocol_data, sample_fees_data
    ):
        """Test successful data collection."""
        # Mock the fetch_json method
        async def mock_fetch_json(endpoint):
            if "/protocol/" in endpoint:
                return sample_protocol_data
            elif "/summary/fees/" in endpoint:
                return sample_fees_data
            return {}

        defillama_collector.fetch_json = AsyncMock(side_effect=mock_fetch_json)

        # Temporarily reduce protocols for testing
        original_protocols = defillama_collector.MONITORED_PROTOCOLS
        defillama_collector.MONITORED_PROTOCOLS = ["lido", "aave"]

        try:
            data = await defillama_collector.collect()

            assert len(data) == 2
            assert all(isinstance(item, dict) for item in data)
            assert all("protocol" in item for item in data)
            assert all("tvl_usd" in item for item in data)
            assert all("collected_at" in item for item in data)
        finally:
            defillama_collector.MONITORED_PROTOCOLS = original_protocols

    @pytest.mark.asyncio
    async def test_collect_handles_missing_fees(
        self, defillama_collector, sample_protocol_data
    ):
        """Test handling of protocols without fees data."""
        async def mock_fetch_json(endpoint):
            if "/protocol/" in endpoint:
                return sample_protocol_data
            elif "/summary/fees/" in endpoint:
                raise Exception("No fees data")
            return {}

        defillama_collector.fetch_json = AsyncMock(side_effect=mock_fetch_json)
        defillama_collector.MONITORED_PROTOCOLS = ["lido"]

        data = await defillama_collector.collect()

        assert len(data) == 1
        assert data[0]["fees_24h"] is None
        assert data[0]["revenue_24h"] is None

    @pytest.mark.asyncio
    async def test_validate_data_success(self, defillama_collector):
        """Test data validation with valid data."""
        raw_data = [
            {
                "protocol": "lido",
                "tvl_usd": 25000000000.0,
                "fees_24h": 5000000.0,
                "revenue_24h": 2500000.0,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "protocol": "aave",
                "tvl_usd": 10000000000.0,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        validated = await defillama_collector.validate_data(raw_data)

        assert len(validated) == 2
        assert validated[0]["protocol"] == "lido"
        assert validated[1]["protocol"] == "aave"

    @pytest.mark.asyncio
    async def test_validate_data_removes_invalid(self, defillama_collector):
        """Test that validation removes invalid data."""
        raw_data = [
            {
                "protocol": "valid",
                "tvl_usd": 1000000.0,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "protocol": "missing_tvl",
                "tvl_usd": None,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "protocol": "negative_tvl",
                "tvl_usd": -1000000.0,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing protocol name
                "tvl_usd": 1000000.0,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        validated = await defillama_collector.validate_data(raw_data)

        assert len(validated) == 1
        assert validated[0]["protocol"] == "valid"

    @pytest.mark.asyncio
    async def test_store_data(self, defillama_collector):
        """Test storing data to database."""
        mock_session = MagicMock()

        data = [
            {
                "protocol": "lido",
                "tvl_usd": 25000000000.0,
                "fees_24h": 5000000.0,
                "revenue_24h": 2500000.0,
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        count = await defillama_collector.store_data(data, mock_session)

        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_store_data_handles_errors(self, defillama_collector):
        """Test that store continues after individual record errors."""
        mock_session = MagicMock()
        # Make add fail for the first record
        mock_session.add.side_effect = [Exception("DB error"), None]

        data = [
            {
                "protocol": "failing",
                "tvl_usd": 1000000.0,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "protocol": "succeeding",
                "tvl_usd": 2000000.0,
                "fees_24h": None,
                "revenue_24h": None,
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        count = await defillama_collector.store_data(data, mock_session)

        # Should still store 1 record despite 1 failure
        assert count == 1
        assert mock_session.commit.call_count == 1
