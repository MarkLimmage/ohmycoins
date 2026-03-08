"""Tests for NewsEnrichment model and JSONB operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlmodel import Session, select

from app.models import NewsEnrichment, NewsItem


@pytest.fixture
def sample_news_item(session: Session) -> NewsItem:
    """Create a sample news item for testing."""
    item = NewsItem(
        link=f"https://example.com/news/{uuid.uuid4()}",
        title="Test Article",
        source="TestSource",
        collected_at=datetime.now(timezone.utc),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def test_create_news_enrichment(session: Session, sample_news_item: NewsItem) -> None:
    """Test creating a NewsEnrichment record."""
    enrichment = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={"test_key": "test_value"},
        currencies=["BTC", "ETH"],
        confidence=0.95,
    )
    session.add(enrichment)
    session.commit()
    session.refresh(enrichment)

    assert enrichment.id is not None
    assert enrichment.enricher_name == "test_enricher"
    assert enrichment.data["test_key"] == "test_value"
    assert enrichment.currencies == ["BTC", "ETH"]
    assert enrichment.confidence == 0.95


def test_unique_constraint_on_enrichment(
    session: Session, sample_news_item: NewsItem
) -> None:
    """Test that unique constraint prevents duplicate enrichments."""
    enrichment1 = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={"key": "value1"},
        confidence=0.9,
    )
    session.add(enrichment1)
    session.commit()

    enrichment2 = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={"key": "value2"},
        confidence=0.8,
    )
    session.add(enrichment2)

    with pytest.raises(Exception):
        session.commit()


def test_jsonb_data_storage(session: Session, sample_news_item: NewsItem) -> None:
    """Test JSONB data storage and retrieval."""
    complex_data = {
        "nested": {"key": "value"},
        "array": [1, 2, 3],
        "string": "test",
        "number": 42,
        "boolean": True,
        "null": None,
    }

    enrichment = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data=complex_data,
        confidence=0.9,
    )
    session.add(enrichment)
    session.commit()

    # Query and verify
    result = session.exec(
        select(NewsEnrichment).where(
            NewsEnrichment.news_item_link == sample_news_item.link
        )
    ).first()

    assert result is not None
    assert result.data == complex_data
    assert result.data["nested"]["key"] == "value"
    assert result.data["array"] == [1, 2, 3]


def test_array_currencies_storage(session: Session, sample_news_item: NewsItem) -> None:
    """Test ARRAY column for currencies."""
    enrichment = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={},
        currencies=["BTC", "ETH", "SOL", "ADA"],
        confidence=0.9,
    )
    session.add(enrichment)
    session.commit()

    result = session.exec(
        select(NewsEnrichment).where(
            NewsEnrichment.news_item_link == sample_news_item.link
        )
    ).first()

    assert result is not None
    assert result.currencies == ["BTC", "ETH", "SOL", "ADA"]


def test_gin_index_on_data(session: Session, sample_news_item: NewsItem) -> None:
    """Test that GIN index exists on data column."""
    enrichment = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={"searchable": "value"},
        confidence=0.9,
    )
    session.add(enrichment)
    session.commit()

    # Verify GIN index exists
    result = session.exec(
        text("SELECT indexname FROM pg_indexes WHERE tablename = 'news_enrichment'")
    ).all()

    index_names = [r[0] for r in result]
    assert any("ix_enrichment_data" in name for name in index_names)


def test_gin_index_on_currencies(session: Session, sample_news_item: NewsItem) -> None:
    """Test that GIN index exists on currencies column."""
    enrichment = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={},
        currencies=["BTC"],
        confidence=0.9,
    )
    session.add(enrichment)
    session.commit()

    # Verify GIN index exists
    result = session.exec(
        text("SELECT indexname FROM pg_indexes WHERE tablename = 'news_enrichment'")
    ).all()

    index_names = [r[0] for r in result]
    assert any("ix_enrichment_currencies" in name for name in index_names)


def test_enrichment_timestamp(session: Session, sample_news_item: NewsItem) -> None:
    """Test that enriched_at timestamp is set automatically."""
    before = datetime.now(timezone.utc)
    enrichment = NewsEnrichment(
        news_item_link=sample_news_item.link,
        enricher_name="test_enricher",
        enrichment_type="test",
        data={},
        confidence=0.9,
    )
    session.add(enrichment)
    session.commit()
    session.refresh(enrichment)
    after = datetime.now(timezone.utc)

    assert enrichment.enriched_at is not None
    assert before <= enrichment.enriched_at <= after


def test_confidence_range(session: Session) -> None:
    """Test that confidence values are stored correctly."""
    # Create multiple news items
    items = []
    for i in range(4):
        item = NewsItem(
            link=f"https://example.com/news/{uuid.uuid4()}",
            title=f"Test Article {i}",
            source="TestSource",
            collected_at=datetime.now(timezone.utc),
        )
        session.add(item)
        items.append(item)
    session.commit()

    # Add enrichments with different confidence values
    for i, confidence_val in enumerate([0.0, 0.5, 0.75, 1.0]):
        enrichment = NewsEnrichment(
            news_item_link=items[i].link,
            enricher_name="test_enricher",
            enrichment_type="test",
            data={},
            confidence=confidence_val,
        )
        session.add(enrichment)

    session.commit()

    results = session.exec(
        select(NewsEnrichment).where(
            NewsEnrichment.enricher_name == "test_enricher"
        )
    ).all()

    confidences = [r.confidence for r in results]
    assert 0.0 in confidences
    assert 1.0 in confidences
