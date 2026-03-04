"""Tests for CryptoPanic collector improvements: volume weighting and importance boost."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.collectors.strategies.news_cryptopanic import NewsCryptoPanic


SAMPLE_API_RESPONSE = {
    "results": [
        {
            "title": "Bitcoin Surges Past 100K",
            "url": "https://example.com/btc-100k",
            "source": {"title": "CoinDesk"},
            "published_at": "2026-03-04T10:00:00Z",
            "votes": {
                "positive": 150,
                "negative": 20,
                "liked": 50,
                "disliked": 10,
                "important": 5,
            },
            "currencies": [{"code": "BTC", "title": "Bitcoin"}],
            "metadata": {"description": "Bitcoin hits a new all-time high."},
        },
        {
            "title": "Minor Altcoin Update",
            "url": "https://example.com/altcoin",
            "source": {"title": "CryptoSlate"},
            "published_at": "2026-03-04T09:00:00Z",
            "votes": {
                "positive": 1,
                "negative": 0,
                "liked": 1,
                "disliked": 0,
                "important": 0,
            },
            "currencies": [],
            "metadata": {},
        },
        {
            "title": "Regulatory Crackdown Looms",
            "url": "https://example.com/reg-crackdown",
            "source": {"title": "Reuters"},
            "published_at": "2026-03-04T08:00:00Z",
            "votes": {
                "positive": 0,
                "negative": 0,
                "liked": 0,
                "disliked": 0,
                "important": 10,
            },
            "currencies": [],
            "metadata": {},
        },
        {
            "title": "New Token Launch",
            "url": "https://example.com/new-token",
            "source": {"title": "CoinTelegraph"},
            "published_at": "2026-03-04T07:00:00Z",
            "votes": {},
            "currencies": [],
            "metadata": {"description": "A crash in token price plunge."},
        },
    ],
}


@pytest.mark.asyncio
async def test_total_votes_stored() -> None:
    """Test that total_votes is calculated and stored on NewsSentiment."""
    collector = NewsCryptoPanic()

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=SAMPLE_API_RESPONSE)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "app.collectors.strategies.news_cryptopanic.aiohttp.ClientSession",
            return_value=mock_session,
        ),
        patch.dict(os.environ, {"CRYPTOPANIC_API_KEY": "test-key"}),
    ):
        results = await collector.collect({})

    assert len(results) == 4
    # First article: 150+20+50+10+5 = 235 total votes
    assert results[0].total_votes == 235
    # Second article: 1+0+1+0+0 = 2 total votes
    assert results[1].total_votes == 2
    # Third article: 0+0+0+0+10 = 10 (only important votes)
    assert results[2].total_votes == 10
    # Fourth article: empty votes dict
    assert results[3].total_votes == 0


def test_importance_boost_on_score() -> None:
    """Test that important votes boost the magnitude of sentiment_score."""
    collector = NewsCryptoPanic()

    article_with_importance = {
        "votes": {
            "positive": 150,
            "negative": 20,
            "liked": 50,
            "disliked": 10,
            "important": 5,
        },
    }
    score_with = collector._calculate_sentiment_score(article_with_importance)

    article_without = {
        "votes": {
            "positive": 150,
            "negative": 20,
            "liked": 50,
            "disliked": 10,
            "important": 0,
        },
    }
    score_without = collector._calculate_sentiment_score(article_without)

    assert score_with is not None
    assert score_without is not None
    assert abs(score_with) > abs(score_without)


def test_importance_boost_capped() -> None:
    """Test that importance boost is capped at 50%."""
    collector = NewsCryptoPanic()

    article = {
        "votes": {
            "positive": 10,
            "negative": 0,
            "liked": 0,
            "disliked": 0,
            "important": 100,
        },
    }
    score = collector._calculate_sentiment_score(article)
    assert score is not None
    assert score <= 1.0


def test_important_only_returns_neutral_sentiment() -> None:
    """Test that articles with only 'important' votes return 'neutral' sentiment."""
    collector = NewsCryptoPanic()

    article = {
        "votes": {
            "positive": 0,
            "negative": 0,
            "liked": 0,
            "disliked": 0,
            "important": 10,
        },
        "metadata": {},
    }
    sentiment = collector._determine_sentiment(article)
    assert sentiment == "neutral"


def test_zero_votes_score() -> None:
    """Test score is 0.0 when no directional votes exist."""
    collector = NewsCryptoPanic()

    article = {
        "votes": {
            "positive": 0,
            "negative": 0,
            "liked": 0,
            "disliked": 0,
            "important": 5,
        },
    }
    score = collector._calculate_sentiment_score(article)
    assert score == 0.0


def test_no_votes_returns_none() -> None:
    """Test score is None when votes dict is empty."""
    collector = NewsCryptoPanic()
    score = collector._calculate_sentiment_score({"votes": {}})
    assert score is None


def test_keyword_fallback_still_works() -> None:
    """Test that keyword fallback in _determine_sentiment still works."""
    collector = NewsCryptoPanic()

    bullish_article = {
        "votes": {},
        "metadata": {"description": "Bitcoin rally continues with surge."},
    }
    assert collector._determine_sentiment(bullish_article) == "bullish"

    bearish_article = {
        "votes": {},
        "metadata": {"description": "Market crash leads to massive plunge."},
    }
    assert collector._determine_sentiment(bearish_article) == "bearish"
