"""Tests for CryptoSlate collector keyword enrichment."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.collectors.strategies.news_cryptoslate import (
    CryptoSlateCollector,
    _aggregate_sentiment,
)
from app.collectors.strategies.keyword_taxonomy import KeywordEntry
from app.models import NewsItem, NewsKeywordMatch

# Sample RSS XML with keyword-rich content
SAMPLE_RSS_WITH_KEYWORDS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
  <title>Fed Announces Rate Cut Amid Bitcoin ETF Approval</title>
  <link>https://cryptoslate.com/fed-rate-cut-btc-etf</link>
  <pubDate>Mon, 03 Mar 2026 12:00:00 +0000</pubDate>
  <description>The Federal Reserve announced a rate cut today as Bitcoin ETF gets approved.</description>
</item>
<item>
  <title>New Partnership Drives Ethereum Adoption</title>
  <link>https://cryptoslate.com/eth-partnership-adoption</link>
  <pubDate>Mon, 03 Mar 2026 11:00:00 +0000</pubDate>
  <description>A major partnership is driving Ethereum adoption across DeFi.</description>
</item>
<item>
  <title>Weather Report: Sunny Skies Ahead</title>
  <link>https://cryptoslate.com/weather-report</link>
  <pubDate>Mon, 03 Mar 2026 10:00:00 +0000</pubDate>
  <description>Nothing crypto related here at all.</description>
</item>
</channel>
</rss>"""


@pytest.mark.asyncio
async def test_collect_returns_newsitem_and_keyword_matches() -> None:
    collector = CryptoSlateCollector()

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = AsyncMock(return_value=SAMPLE_RSS_WITH_KEYWORDS)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        results = await collector.collect({})

    # Should have NewsItem and NewsKeywordMatch instances
    news_items = [r for r in results if isinstance(r, NewsItem)]
    keyword_matches = [r for r in results if isinstance(r, NewsKeywordMatch)]

    assert len(news_items) == 3
    assert len(keyword_matches) > 0

    # First article should have matches for Fed, rate cut, ETF, approval
    first_item_matches = [
        m for m in keyword_matches
        if m.news_item_link == "https://cryptoslate.com/fed-rate-cut-btc-etf"
    ]
    matched_keywords = [m.keyword for m in first_item_matches]
    assert "Federal Reserve" in matched_keywords
    assert "rate cut" in matched_keywords
    assert "ETF" in matched_keywords
    assert "approval" in matched_keywords


@pytest.mark.asyncio
async def test_collect_no_keywords_for_generic_text() -> None:
    collector = CryptoSlateCollector()

    generic_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
    <item>
      <title>Nothing Special Here</title>
      <link>https://cryptoslate.com/nothing</link>
      <pubDate>Mon, 03 Mar 2026 12:00:00 +0000</pubDate>
      <description>Just a regular article about cooking recipes.</description>
    </item>
    </channel></rss>"""

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = AsyncMock(return_value=generic_rss)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        results = await collector.collect({})

    keyword_matches = [r for r in results if isinstance(r, NewsKeywordMatch)]
    assert len(keyword_matches) == 0


@pytest.mark.asyncio
async def test_sentiment_populated_on_newsitem() -> None:
    collector = CryptoSlateCollector()

    rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
    <item>
      <title>Fed Rate Cut Boosts Bitcoin</title>
      <link>https://cryptoslate.com/fed-boost</link>
      <pubDate>Mon, 03 Mar 2026 12:00:00 +0000</pubDate>
      <description>Rate cut is bullish for crypto markets.</description>
    </item>
    </channel></rss>"""

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = AsyncMock(return_value=rss)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        results = await collector.collect({})

    news_items = [r for r in results if isinstance(r, NewsItem)]
    assert len(news_items) == 1
    item = news_items[0]
    assert item.sentiment_score is not None
    assert item.sentiment_label is not None
    assert item.sentiment_label in ("bullish", "bearish", "neutral")


def test_aggregate_sentiment_bullish() -> None:
    import re
    matches = [
        KeywordEntry("rate cut", re.compile(r""), "liquidity", "bullish", "high", "immediate"),
        KeywordEntry("ETF", re.compile(r""), "regulatory", "bullish", "high", "short_term"),
    ]
    score, label = _aggregate_sentiment(matches)
    assert score > 0.1
    assert label == "bullish"


def test_aggregate_sentiment_bearish() -> None:
    import re
    matches = [
        KeywordEntry("hack", re.compile(r""), "fundamental", "bearish", "high", "immediate"),
        KeywordEntry("exploit", re.compile(r""), "fundamental", "bearish", "high", "immediate"),
    ]
    score, label = _aggregate_sentiment(matches)
    assert score < -0.1
    assert label == "bearish"


def test_aggregate_sentiment_neutral() -> None:
    import re
    matches = [
        KeywordEntry("Fed", re.compile(r""), "liquidity", "neutral", "high", "immediate"),
    ]
    score, label = _aggregate_sentiment(matches)
    assert score == 0.0
    assert label == "neutral"


def test_aggregate_sentiment_mixed() -> None:
    import re
    matches = [
        KeywordEntry("rate cut", re.compile(r""), "liquidity", "bullish", "high", "immediate"),
        KeywordEntry("recession", re.compile(r""), "macro", "bearish", "high", "long_term"),
    ]
    score, label = _aggregate_sentiment(matches)
    assert label == "neutral"  # equal bullish/bearish cancel out
