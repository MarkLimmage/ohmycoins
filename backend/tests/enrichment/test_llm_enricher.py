"""Tests for the LLMEnricher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.enrichment.llm_enricher import LLMEnricher
from app.enrichment.providers.base import ISentimentProvider, SentimentResult
from app.models import NewsItem


@pytest.mark.asyncio
async def test_llm_enricher_calls_provider() -> None:
    """Test that LLMEnricher calls the sentiment provider."""
    mock_provider = MagicMock(spec=ISentimentProvider)
    mock_provider.analyse = AsyncMock(
        return_value=[
            SentimentResult(coin="BTC", direction="bullish", confidence=0.9, rationale="Strong support")
        ]
    )

    enricher = LLMEnricher(mock_provider)
    item = NewsItem(
        title="Bitcoin surge",
        link="https://example.com/btc",
        summary="Bitcoin is surging",
        source="Test",
    )

    results = await enricher.enrich(item)

    mock_provider.analyse.assert_called_once()
    assert len(results) == 1


@pytest.mark.asyncio
async def test_llm_enricher_returns_sentiment_results() -> None:
    """Test that LLMEnricher returns sentiment results."""
    mock_provider = MagicMock(spec=ISentimentProvider)
    mock_provider.analyse = AsyncMock(
        return_value=[
            SentimentResult(coin="ETH", direction="neutral", confidence=0.5, rationale="Awaiting clarity"),
            SentimentResult(coin="BTC", direction="bullish", confidence=0.85, rationale="Strong momentum"),
        ]
    )

    enricher = LLMEnricher(mock_provider)
    item = NewsItem(
        title="Crypto market news",
        link="https://example.com/news",
        summary="Mixed signals in crypto",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert len(results) == 2
    assert results[0].enrichment_type == "sentiment"
    assert results[0].data["coin"] == "ETH"
    assert results[1].data["direction"] == "bullish"


@pytest.mark.asyncio
async def test_llm_enricher_handles_provider_error() -> None:
    """Test that LLMEnricher handles provider errors gracefully."""
    mock_provider = MagicMock(spec=ISentimentProvider)
    mock_provider.analyse = AsyncMock(side_effect=ValueError("No credentials"))

    enricher = LLMEnricher(mock_provider)
    item = NewsItem(
        title="Test",
        link="https://example.com/test",
        summary="Test",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_llm_enricher_can_enrich_newsitem() -> None:
    """Test can_enrich checks item type."""
    mock_provider = MagicMock(spec=ISentimentProvider)
    enricher = LLMEnricher(mock_provider)
    item = NewsItem(
        title="Test",
        link="https://example.com",
        summary="Test",
        source="Test",
    )

    assert enricher.can_enrich(item) is True


@pytest.mark.asyncio
async def test_llm_enricher_enrichment_type_is_sentiment() -> None:
    """Test that enrichment_type is 'sentiment'."""
    mock_provider = MagicMock(spec=ISentimentProvider)
    mock_provider.analyse = AsyncMock(
        return_value=[
            SentimentResult(coin="BTC", direction="bullish", confidence=0.9, rationale="Strong"),
        ]
    )

    enricher = LLMEnricher(mock_provider)
    item = NewsItem(
        title="Bitcoin bull run",
        link="https://example.com/bull",
        summary="Bitcoin is in a bull run",
        source="Test",
    )

    results = await enricher.enrich(item)

    assert all(r.enrichment_type == "sentiment" for r in results)


@pytest.mark.asyncio
async def test_llm_enricher_name() -> None:
    """Test that enricher name is 'llm_sentiment'."""
    mock_provider = MagicMock(spec=ISentimentProvider)
    enricher = LLMEnricher(mock_provider)

    assert enricher.name == "llm_sentiment"
