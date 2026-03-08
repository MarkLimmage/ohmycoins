"""Tests for auto-triggering enrichment in the strategy adapter."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models import NewsItem
from app.services.collectors.strategy_adapter import StrategyAdapterCollector


class MockCollector:
    """Mock collector for testing."""

    @property
    def name(self) -> str:
        return "mock_collector"

    @property
    def description(self) -> str:
        return "Mock collector for tests"

    def get_config_schema(self) -> dict:
        return {}

    def validate_config(self, config: dict) -> bool:
        return True

    async def test_connection(self, config: dict) -> bool:
        return True

    async def collect(self, config: dict) -> list:
        return [
            NewsItem(
                title="Test news",
                link="https://example.com/test",
                summary="Test summary",
                source="Mock",
            )
        ]


@pytest.mark.asyncio
async def test_enrichment_auto_triggers_on_newsitem_storage(session) -> None:
    """Test that enrichment triggers when news items are stored."""
    mock_strategy = MockCollector()
    adapter = StrategyAdapterCollector(mock_strategy, ledger_name="human")

    # Patch the enrichment pipeline to track calls
    with patch("app.services.collectors.strategy_adapter.EnrichmentPipeline") as mock_pipeline_class:
        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.run = AsyncMock()

        # Store a news item
        items = [
            NewsItem(
                title="Test",
                link="https://example.com/unique1",
                summary="Test",
                source="Test",
            )
        ]

        count = await adapter.store_data(items, session)

        assert count == 1
        # Enrichment pipeline should have been instantiated
        mock_pipeline_class.assert_called_once()
        # Run should have been called
        mock_pipeline.run.assert_called_once()


@pytest.mark.asyncio
async def test_enrichment_failure_does_not_crash_collection(session) -> None:
    """Test that enrichment failure doesn't crash the collector."""
    mock_strategy = MockCollector()
    adapter = StrategyAdapterCollector(mock_strategy, ledger_name="human")

    # Patch the enrichment to fail
    with patch("app.services.collectors.strategy_adapter.EnrichmentPipeline") as mock_pipeline_class:
        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.run = AsyncMock(side_effect=ValueError("Pipeline failed"))

        # Store a news item
        items = [
            NewsItem(
                title="Test",
                link="https://example.com/unique2",
                summary="Test",
                source="Test",
            )
        ]

        # Should not raise an exception
        count = await adapter.store_data(items, session)

        assert count == 1


@pytest.mark.asyncio
async def test_enrichment_only_runs_on_newsitems(session) -> None:
    """Test that enrichment only triggers for NewsItem objects."""

    class NonNewsCollector:
        @property
        def name(self) -> str:
            return "non_news"

        async def collect(self, config: dict) -> list:
            return [{"data": "not a model"}]

    adapter = StrategyAdapterCollector(NonNewsCollector(), ledger_name="glass")

    with patch("app.services.collectors.strategy_adapter.EnrichmentPipeline") as mock_pipeline_class:
        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.run = AsyncMock()

        # Store non-NewsItem data
        count = await adapter.store_data([{"data": "not a model"}], session)

        assert count == 0
        # Enrichment should not have been called
        mock_pipeline.run.assert_not_called()


@pytest.mark.asyncio
async def test_enrichment_skips_empty_storage(session) -> None:
    """Test that enrichment doesn't run if no items are stored."""
    mock_strategy = MockCollector()
    adapter = StrategyAdapterCollector(mock_strategy, ledger_name="human")

    with patch("app.services.collectors.strategy_adapter.EnrichmentPipeline") as mock_pipeline_class:
        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline

        # Store empty list
        count = await adapter.store_data([], session)

        assert count == 0
        # Enrichment should not have been called
        mock_pipeline_class.assert_not_called()
