"""Tests for the signal query tool."""

import uuid
from datetime import datetime, timezone

from app.models import NewsEnrichment, NewsItem
from app.services.agent.tools.signal_query import query_market_signals
from app.core.db import engine
from sqlmodel import Session


def test_query_market_signals_returns_summary() -> None:
    """Test that query_market_signals returns correct summary."""
    unique_id = str(uuid.uuid4())
    link = f"https://example.com/btc-{unique_id}"

    with Session(engine) as session:
        # Create news item
        news_item = NewsItem(
            title="Bitcoin surge",
            link=link,
            summary="Bitcoin rising",
            source="TestSource",
        )
        session.add(news_item)
        session.commit()

        # Create signals
        for i, direction in enumerate(["bullish", "bullish", "bearish"]):
            enrichment = NewsEnrichment(
                news_item_link=link,
                enricher_name=f"tool_test_{i}_{unique_id}",
                enrichment_type="sentiment",
                data={"direction": direction},
                currencies=["BTC"],
                confidence=0.8,
                enriched_at=datetime.now(timezone.utc),
            )
            session.add(enrichment)
        session.commit()

        # Query signals
        result = query_market_signals("BTC", hours=24)

        assert result["coin"] == "BTC"
        assert result["period_hours"] == 24
        # Should have at least our 3 signals
        assert result["total_signals"] >= 3
        assert result["bullish_count"] >= 2
        assert result["bearish_count"] >= 1


def test_query_market_signals_empty_results() -> None:
    """Test that empty results return valid response."""
    unique_id = str(uuid.uuid4())[:8]
    test_coin = f"NOEXIST{unique_id}"
    result = query_market_signals(test_coin, hours=24)

    assert result["coin"] == test_coin.upper()
    assert result["total_signals"] == 0
    assert result["bullish_count"] == 0
    assert result["bearish_count"] == 0
    assert result["neutral_count"] == 0
    assert result["sentiment_score"] == 0.0
    assert result["avg_confidence"] == 0.0
    assert result["recent_signals"] == []


def test_query_market_signals_case_insensitive() -> None:
    """Test that coin matching is case-insensitive."""
    unique_id = str(uuid.uuid4())
    link = f"https://example.com/eth-{unique_id}"

    with Session(engine) as session:
        news_item = NewsItem(
            title="Ethereum test",
            link=link,
            summary="Test",
            source="TestSource",
        )
        session.add(news_item)
        session.commit()

        enrichment = NewsEnrichment(
            news_item_link=link,
            enricher_name=f"case_test_{unique_id}",
            enrichment_type="sentiment",
            data={"direction": "bullish"},
            currencies=["eth"],  # lowercase
            confidence=0.85,
            enriched_at=datetime.now(timezone.utc),
        )
        session.add(enrichment)
        session.commit()

        # Query with uppercase
        result = query_market_signals("ETH", hours=24)

        assert result["coin"] == "ETH"
        # Should have at least our enrichment
        assert result["total_signals"] >= 1
        assert result["bullish_count"] >= 1
