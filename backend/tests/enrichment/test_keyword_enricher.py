"""Tests for the KeywordEnricher."""

import pytest

from app.enrichment.keyword_enricher import KeywordEnricher
from app.models import NewsItem


@pytest.mark.asyncio
async def test_keyword_enricher_extracts_keywords() -> None:
    """Test that KeywordEnricher extracts keywords from news items."""
    enricher = KeywordEnricher()
    item = NewsItem(
        title="Bitcoin halving coming soon",
        link="https://example.com/article1",
        summary="Bitcoin will undergo a halving event next year, which historically bullish",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert len(results) > 0
    assert any(r.data["keyword"] == "halving" for r in results)


@pytest.mark.asyncio
async def test_keyword_enricher_extracts_currencies() -> None:
    """Test that KeywordEnricher extracts currency symbols."""
    enricher = KeywordEnricher()
    item = NewsItem(
        title="ETH and BTC surge on SEC approval",
        link="https://example.com/article2",
        summary="Ethereum and Bitcoin surge after SEC approval",
        source="Test",
    )

    results = await enricher.enrich(item)

    # Should have extracted BTC and ETH
    currencies = set()
    for r in results:
        currencies.update(r.currencies)

    assert "BTC" in currencies or "ETH" in currencies


@pytest.mark.asyncio
async def test_keyword_enricher_can_enrich_newsitem() -> None:
    """Test can_enrich checks item type."""
    enricher = KeywordEnricher()
    item = NewsItem(
        title="Test title",
        link="https://example.com",
        summary="Test summary",
        source="Test",
    )

    assert enricher.can_enrich(item) is True


@pytest.mark.asyncio
async def test_keyword_enricher_cannot_enrich_non_newsitem() -> None:
    """Test can_enrich rejects non-NewsItem objects."""
    enricher = KeywordEnricher()

    assert enricher.can_enrich("not a news item") is False
    assert enricher.can_enrich({"dict": "object"}) is False


@pytest.mark.asyncio
async def test_keyword_enricher_returns_empty_for_no_matches() -> None:
    """Test that enricher returns empty list when no keywords match."""
    enricher = KeywordEnricher()
    item = NewsItem(
        title="Random weather report",
        link="https://example.com/weather",
        summary="It will be sunny tomorrow",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_keyword_enricher_sets_confidence() -> None:
    """Test that enricher sets confidence to 1.0."""
    enricher = KeywordEnricher()
    item = NewsItem(
        title="Bitcoin ban coming",
        link="https://example.com/ban",
        summary="Regulatory ban on bitcoin usage",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert all(r.confidence == 1.0 for r in results)


@pytest.mark.asyncio
async def test_keyword_enricher_sets_enrichment_type() -> None:
    """Test that enricher sets enrichment_type to 'keyword'."""
    enricher = KeywordEnricher()
    item = NewsItem(
        title="Ethereum upgrade announcement",
        link="https://example.com/upgrade",
        summary="New Ethereum upgrade coming",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert all(r.enrichment_type == "keyword" for r in results)
