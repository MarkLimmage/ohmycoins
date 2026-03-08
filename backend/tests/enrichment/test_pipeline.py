"""Tests for the EnrichmentPipeline."""

from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from app.enrichment.base import EnrichmentResult, IEnricher
from app.enrichment.pipeline import EnrichmentPipeline
from app.models import NewsItem


class MockEnricher(IEnricher):
    """Mock enricher for testing."""

    def __init__(self, name_: str = "test_enricher", should_fail: bool = False):
        self._name = name_
        self.should_fail = should_fail
        self.enriched_items: list[NewsItem] = []

    @property
    def name(self) -> str:
        return self._name

    def can_enrich(self, item: object) -> bool:
        return isinstance(item, NewsItem)

    async def enrich(self, item: object) -> list[EnrichmentResult]:
        if not isinstance(item, NewsItem):
            return []

        self.enriched_items.append(item)

        if self.should_fail:
            raise ValueError("Mock failure")

        return [
            EnrichmentResult(
                enricher_name=self._name,
                enrichment_type="test",
                data={"test": "data"},
                currencies=["BTC"],
                confidence=0.95,
            )
        ]


@pytest.mark.asyncio
async def test_pipeline_runs_enrichers(session: Session) -> None:
    """Test that pipeline runs all enrichers."""
    enricher1 = MockEnricher("enricher1")
    enricher2 = MockEnricher("enricher2")
    pipeline = EnrichmentPipeline([enricher1, enricher2])

    item = NewsItem(
        title="Test",
        link="https://example.com/test",
        summary="Test",
        source="Test",
    )

    run = await pipeline.run([item], session)

    assert run.items_processed == 1
    assert run.items_enriched == 1
    assert len(enricher1.enriched_items) == 1
    assert len(enricher2.enriched_items) == 1


@pytest.mark.asyncio
async def test_pipeline_handles_enricher_failure(session: Session) -> None:
    """Test that pipeline continues when one enricher fails."""
    enricher1 = MockEnricher("enricher1", should_fail=True)
    enricher2 = MockEnricher("enricher2")
    pipeline = EnrichmentPipeline([enricher1, enricher2])

    item = NewsItem(
        title="Test",
        link="https://example.com/test",
        summary="Test",
        source="Test",
    )

    run = await pipeline.run([item], session)

    # enricher2 should still have processed the item
    assert len(enricher2.enriched_items) == 1
    assert run.status == "completed"


@pytest.mark.asyncio
async def test_pipeline_creates_enrichment_run(session: Session) -> None:
    """Test that pipeline creates an EnrichmentRun record."""
    enricher = MockEnricher("test")
    pipeline = EnrichmentPipeline([enricher])

    item = NewsItem(
        title="Test",
        link="https://example.com/test",
        summary="Test",
        source="Test",
    )

    run = await pipeline.run([item], session)

    assert run.enricher_name == "pipeline"
    assert run.items_processed == 1
    assert run.items_enriched == 1
    assert run.status == "completed"
    assert run.trigger == "auto"


@pytest.mark.asyncio
async def test_pipeline_skip_unenrichable_items(session: Session) -> None:
    """Test that pipeline skips items that cannot be enriched."""
    enricher = MockEnricher("test")

    # Override can_enrich to reject all items
    enricher.can_enrich = lambda x: False  # type: ignore[assignment]

    pipeline = EnrichmentPipeline([enricher])

    item = NewsItem(
        title="Test",
        link="https://example.com/test",
        summary="Test",
        source="Test",
    )

    run = await pipeline.run([item], session)

    assert run.items_processed == 1
    assert run.items_enriched == 0
    assert run.items_skipped == 1


@pytest.mark.asyncio
async def test_pipeline_trigger_parameter(session: Session) -> None:
    """Test that pipeline records the trigger parameter."""
    enricher = MockEnricher("test")
    pipeline = EnrichmentPipeline([enricher])

    item = NewsItem(
        title="Test",
        link="https://example.com/test",
        summary="Test",
        source="Test",
    )

    run = await pipeline.run([item], session, trigger="manual")

    assert run.trigger == "manual"


@pytest.mark.asyncio
async def test_pipeline_processes_multiple_items(session: Session) -> None:
    """Test that pipeline processes multiple items."""
    enricher = MockEnricher("test")
    pipeline = EnrichmentPipeline([enricher])

    items = [
        NewsItem(
            title=f"Test {i}",
            link=f"https://example.com/test{i}",
            summary="Test",
            source="Test",
        )
        for i in range(5)
    ]

    run = await pipeline.run(items, session)

    assert run.items_processed == 5
    assert run.items_enriched == 5
    assert len(enricher.enriched_items) == 5
