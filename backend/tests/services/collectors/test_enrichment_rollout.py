"""
Tests for keyword enrichment rollout (Sprint 2.40).

Tests cover:
1. Keyword enrichment for 5 RSS news collectors
2. Sentiment aggregation moved to keyword_taxonomy
3. Sample records mappings for enriched collectors and keywords
"""

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.collectors.strategies.keyword_taxonomy import (
    KeywordEntry,
    aggregate_sentiment,
)
from app.collectors.strategies.news_beincrypto import BeInCryptoCollector
from app.collectors.strategies.news_coindesk import CoinDeskCollector
from app.collectors.strategies.news_cointelegraph import CoinTelegraphCollector
from app.collectors.strategies.news_decrypt import DecryptCollector
from app.collectors.strategies.news_newsbtc import NewsBTCCollector
from app.core.collectors.sample_records import PLUGIN_DATA_MAP
from app.models import (
    NewsItem,
    NewsKeywordMatch,
)


class TestSentimentAggregation:
    """Test sentiment aggregation in keyword_taxonomy."""

    def test_aggregate_sentiment_bullish(self) -> None:
        """Test bullish sentiment aggregation."""
        matches = [
            KeywordEntry(
                keyword="rate cut",
                pattern=re.compile(r"\brate\s+cut\b", re.IGNORECASE),
                category="liquidity",
                direction="bullish",
                impact="high",
                temporal_signal="immediate",
            ),
            KeywordEntry(
                keyword="approval",
                pattern=re.compile(r"\bapprov(?:al|e[ds]|ing)\b", re.IGNORECASE),
                category="regulatory",
                direction="bullish",
                impact="high",
                temporal_signal="immediate",
            ),
        ]
        score, label = aggregate_sentiment(matches)
        assert label == "bullish"
        assert score > 0.1

    def test_aggregate_sentiment_bearish(self) -> None:
        """Test bearish sentiment aggregation."""
        matches = [
            KeywordEntry(
                keyword="ban",
                pattern=re.compile(r"\bbann?(?:ed|s)?\b", re.IGNORECASE),
                category="regulatory",
                direction="bearish",
                impact="high",
                temporal_signal="immediate",
            ),
            KeywordEntry(
                keyword="recession",
                pattern=re.compile(r"\brecession\b", re.IGNORECASE),
                category="macro",
                direction="bearish",
                impact="high",
                temporal_signal="long_term",
            ),
        ]
        score, label = aggregate_sentiment(matches)
        assert label == "bearish"
        assert score < -0.1

    def test_aggregate_sentiment_neutral(self) -> None:
        """Test neutral sentiment aggregation."""
        matches = [
            KeywordEntry(
                keyword="rate cut",
                pattern=re.compile(r"\brate\s+cut\b", re.IGNORECASE),
                category="liquidity",
                direction="bullish",
                impact="high",
                temporal_signal="immediate",
            ),
            KeywordEntry(
                keyword="ban",
                pattern=re.compile(r"\bbann?(?:ed|s)?\b", re.IGNORECASE),
                category="regulatory",
                direction="bearish",
                impact="high",
                temporal_signal="immediate",
            ),
        ]
        score, label = aggregate_sentiment(matches)
        assert label == "neutral"

    def test_aggregate_sentiment_empty(self) -> None:
        """Test sentiment aggregation with no matches."""
        matches: list[KeywordEntry] = []
        score, label = aggregate_sentiment(matches)
        assert score == 0.0
        assert label == "neutral"

    def test_aggregate_sentiment_mixed_impact(self) -> None:
        """Test sentiment aggregation with mixed impact levels."""
        matches = [
            KeywordEntry(
                keyword="upgrade",
                pattern=re.compile(r"\bupgrade\b", re.IGNORECASE),
                category="fundamental",
                direction="bullish",
                impact="medium",
                temporal_signal="short_term",
            ),
            KeywordEntry(
                keyword="partnership",
                pattern=re.compile(r"\bpartnership\b", re.IGNORECASE),
                category="fundamental",
                direction="bullish",
                impact="medium",
                temporal_signal="short_term",
            ),
        ]
        score, label = aggregate_sentiment(matches)
        assert label == "bullish"
        assert score > 0.1


class TestBeInCryptoEnrichment:
    """Test BeInCrypto collector keyword enrichment."""

    @pytest.mark.asyncio
    async def test_beincrypto_with_keywords(self) -> None:
        """Test BeInCrypto enrichment produces interleaved NewsItem + NewsKeywordMatch."""
        collector = BeInCryptoCollector()

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>SEC Approves Bitcoin ETF</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
      <description>The SEC has approved a Bitcoin ETF, marking a major regulatory milestone.</description>
    </item>
  </channel>
</rss>"""

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=rss_xml)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=MagicMock(return_value=mock_response))
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await collector.collect({"max_items": 10})

            # Should have NewsItem + keyword matches
            assert len(result) > 1
            assert isinstance(result[0], NewsItem)
            assert result[0].title == "SEC Approves Bitcoin ETF"
            assert result[0].sentiment_label is not None
            assert result[0].sentiment_score is not None

            # Check for keyword matches
            keyword_matches = [r for r in result if isinstance(r, NewsKeywordMatch)]
            assert len(keyword_matches) > 0
            assert all(m.source_collector == "news_beincrypto" for m in keyword_matches)

    @pytest.mark.asyncio
    async def test_beincrypto_without_keywords(self) -> None:
        """Test BeInCrypto with article that has no matching keywords."""
        collector = BeInCryptoCollector()

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Random Crypto News</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
      <description>Some random news about crypto that does not match keywords.</description>
    </item>
  </channel>
</rss>"""

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=rss_xml)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=MagicMock(return_value=mock_response))
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await collector.collect({"max_items": 10})

            # Should have only NewsItem (no keywords matched)
            assert len(result) == 1
            assert isinstance(result[0], NewsItem)
            assert result[0].title == "Random Crypto News"


class TestCoinTelegraphEnrichment:
    """Test CoinTelegraph collector keyword enrichment."""

    @pytest.mark.asyncio
    async def test_cointelegraph_with_keywords(self) -> None:
        """Test CoinTelegraph enrichment with matching keywords."""
        collector = CoinTelegraphCollector()

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Federal Reserve Rate Hike Impacts Bitcoin</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
      <description>The Federal Reserve announced a rate hike affecting crypto markets.</description>
    </item>
  </channel>
</rss>"""

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=rss_xml)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=MagicMock(return_value=mock_response))
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await collector.collect({"max_items": 10})

            assert len(result) > 1
            news_item = result[0]
            assert isinstance(news_item, NewsItem)
            assert news_item.sentiment_label is not None
            assert all(
                m.source_collector == "news_cointelegraph"
                for m in result[1:]
                if isinstance(m, NewsKeywordMatch)
            )


class TestNewsBTCEnrichment:
    """Test NewsBTC collector keyword enrichment."""

    @pytest.mark.asyncio
    async def test_newsbtc_enrichment(self) -> None:
        """Test NewsBTC enrichment works correctly."""
        collector = NewsBTCCollector()

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Ethereum Halving Coming Soon</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
      <description>Ethereum's next halving event is expected to boost prices.</description>
    </item>
  </channel>
</rss>"""

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=rss_xml)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=MagicMock(return_value=mock_response))
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await collector.collect({"max_items": 10})

            assert len(result) > 1
            assert isinstance(result[0], NewsItem)
            assert result[0].sentiment_label == "bullish"
            keyword_matches = [r for r in result if isinstance(r, NewsKeywordMatch)]
            assert all(m.source_collector == "news_newsbtc" for m in keyword_matches)


class TestDecryptEnrichment:
    """Test Decrypt collector keyword enrichment."""

    @pytest.mark.asyncio
    async def test_decrypt_enrichment(self) -> None:
        """Test Decrypt enrichment works correctly."""
        collector = DecryptCollector()

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Crypto Exchange Hack Detected</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
      <description>A major crypto exchange suffered a security hack.</description>
    </item>
  </channel>
</rss>"""

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=rss_xml)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=MagicMock(return_value=mock_response))
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await collector.collect({"max_items": 10})

            assert len(result) > 1
            assert isinstance(result[0], NewsItem)
            assert result[0].sentiment_label == "bearish"
            keyword_matches = [r for r in result if isinstance(r, NewsKeywordMatch)]
            assert all(m.source_collector == "news_decrypt" for m in keyword_matches)


class TestCoinDeskEnrichment:
    """Test CoinDesk collector keyword enrichment."""

    @pytest.mark.asyncio
    async def test_coindesk_enrichment(self) -> None:
        """Test CoinDesk enrichment works correctly."""
        collector = CoinDeskCollector()

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Partnership Between Aave and Major Bank</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 03 Mar 2026 10:00:00 GMT</pubDate>
      <description>Aave announced a partnership with a major financial institution.</description>
    </item>
  </channel>
</rss>"""

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.text = AsyncMock(return_value=rss_xml)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=MagicMock(return_value=mock_response))
            )
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await collector.collect({"max_items": 10})

            assert len(result) > 1
            assert isinstance(result[0], NewsItem)
            assert result[0].sentiment_label == "bullish"
            keyword_matches = [r for r in result if isinstance(r, NewsKeywordMatch)]
            assert all(m.source_collector == "news_coindesk" for m in keyword_matches)


class TestSampleRecordsMappings:
    """Test sample_records mappings for enriched collectors."""

    def test_beincrypto_enriched_mapping(self) -> None:
        """Test BeInCrypto has enriched mapping."""
        assert "news_beincrypto" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_beincrypto"]
        assert config.data_type_label == "News Items (Enriched)"
        assert "sentiment_label" in config.display_columns
        assert "sentiment_score" in config.display_columns

    def test_cointelegraph_enriched_mapping(self) -> None:
        """Test CoinTelegraph has enriched mapping."""
        assert "news_cointelegraph" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_cointelegraph"]
        assert config.data_type_label == "News Items (Enriched)"
        assert "sentiment_label" in config.display_columns
        assert "sentiment_score" in config.display_columns

    def test_newsbtc_enriched_mapping(self) -> None:
        """Test NewsBTC has enriched mapping."""
        assert "news_newsbtc" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_newsbtc"]
        assert config.data_type_label == "News Items (Enriched)"
        assert "sentiment_label" in config.display_columns
        assert "sentiment_score" in config.display_columns

    def test_decrypt_enriched_mapping(self) -> None:
        """Test Decrypt has enriched mapping."""
        assert "news_decrypt" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_decrypt"]
        assert config.data_type_label == "News Items (Enriched)"
        assert "sentiment_label" in config.display_columns
        assert "sentiment_score" in config.display_columns

    def test_coindesk_enriched_mapping(self) -> None:
        """Test CoinDesk has enriched mapping."""
        assert "news_coindesk" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_coindesk"]
        assert config.data_type_label == "News Items (Enriched)"
        assert "sentiment_label" in config.display_columns
        assert "sentiment_score" in config.display_columns

    def test_keyword_match_mappings(self) -> None:
        """Test keyword match mappings exist for all enriched collectors."""
        keyword_collectors = [
            "news_beincrypto_keywords",
            "news_cointelegraph_keywords",
            "news_newsbtc_keywords",
            "news_decrypt_keywords",
            "news_coindesk_keywords",
        ]

        for collector_name in keyword_collectors:
            assert (
                collector_name in PLUGIN_DATA_MAP
            ), f"Missing mapping for {collector_name}"
            config = PLUGIN_DATA_MAP[collector_name]
            assert config.data_type_label == "Keyword Matches"
            assert "keyword" in config.display_columns
            assert "category" in config.display_columns
            assert "direction" in config.display_columns
            assert "impact" in config.display_columns
            assert "currencies" in config.display_columns

    def test_cryptoslate_enriched_mapping(self) -> None:
        """Test CryptoSlate enriched mapping still exists."""
        assert "news_cryptoslate" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_cryptoslate"]
        assert config.data_type_label == "News Items (Enriched)"
        assert "sentiment_label" in config.display_columns
        assert "sentiment_score" in config.display_columns

    def test_cryptoslate_keywords_mapping(self) -> None:
        """Test CryptoSlate keyword mapping still exists."""
        assert "news_cryptoslate_keywords" in PLUGIN_DATA_MAP
        config = PLUGIN_DATA_MAP["news_cryptoslate_keywords"]
        assert config.data_type_label == "Keyword Matches"
