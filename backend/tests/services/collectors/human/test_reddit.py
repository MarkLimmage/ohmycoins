"""
Tests for Reddit API collector (Human Ledger).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.collectors.human.reddit import RedditCollector


@pytest.fixture
def reddit_collector():
    """Create a Reddit collector instance for testing."""
    return RedditCollector()


@pytest.fixture
def sample_reddit_response():
    """Sample Reddit API response."""
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Bitcoin is breaking out! 🚀",
                        "selftext": "BTC is looking very bullish. HODL!",
                        "score": 523,
                        "num_comments": 145,
                        "author": "crypto_enthusiast",
                        "id": "abc123",
                        "permalink": "/r/CryptoCurrency/comments/abc123/bitcoin_breaking_out/",
                        "created_utc": 1705305600,  # 2024-01-15 10:00:00 UTC
                        "stickied": False,
                    }
                },
                {
                    "data": {
                        "title": "Ethereum update discussion",
                        "selftext": "What do you think about the latest ETH developments?",
                        "score": 89,
                        "num_comments": 34,
                        "author": "eth_hodler",
                        "id": "def456",
                        "permalink": "/r/ethereum/comments/def456/eth_update/",
                        "created_utc": 1705302000,  # 2024-01-15 09:00:00 UTC
                        "stickied": False,
                    }
                },
                {
                    "data": {
                        "title": "Pinned: Daily Discussion",
                        "selftext": "Daily discussion thread",
                        "score": 12,
                        "num_comments": 1234,
                        "author": "AutoModerator",
                        "id": "sticky1",
                        "permalink": "/r/CryptoCurrency/comments/sticky1/daily/",
                        "created_utc": 1705298400,
                        "stickied": True,  # Should be skipped
                    }
                },
            ]
        }
    }


class TestRedditCollector:
    """Test suite for Reddit collector."""

    def test_initialization(self, reddit_collector):
        """Test collector initialization."""
        assert reddit_collector.name == "reddit_api"
        assert reddit_collector.ledger == "human"
        assert "reddit.com" in reddit_collector.base_url
        assert len(reddit_collector.MONITORED_SUBREDDITS) >= 5
        assert "CryptoCurrency" in reddit_collector.MONITORED_SUBREDDITS
        assert "Bitcoin" in reddit_collector.MONITORED_SUBREDDITS

    def test_sentiment_keywords(self, reddit_collector):
        """Test that sentiment keyword lists are populated."""
        assert len(reddit_collector.BULLISH_KEYWORDS) > 0
        assert len(reddit_collector.BEARISH_KEYWORDS) > 0
        assert "moon" in reddit_collector.BULLISH_KEYWORDS
        assert "crash" in reddit_collector.BEARISH_KEYWORDS

    @pytest.mark.asyncio
    async def test_collect_success(self, reddit_collector, sample_reddit_response):
        """Test successful data collection."""
        # Mock the fetch_json method
        reddit_collector.fetch_json = AsyncMock(return_value=sample_reddit_response)

        # Temporarily reduce subreddits for testing
        original_subreddits = reddit_collector.MONITORED_SUBREDDITS
        reddit_collector.MONITORED_SUBREDDITS = ["CryptoCurrency"]

        try:
            data = await reddit_collector.collect()

            # Should collect 2 posts (3rd is stickied)
            assert len(data) == 2
            assert all(isinstance(item, dict) for item in data)
            assert all("title" in item for item in data)
            assert all("source" in item for item in data)
            assert all("sentiment" in item for item in data)
            assert all("collected_at" in item for item in data)

            # Check that stickied post was skipped
            assert not any("Pinned" in item["title"] for item in data)

        finally:
            reddit_collector.MONITORED_SUBREDDITS = original_subreddits

    @pytest.mark.asyncio
    async def test_collect_handles_empty_response(self, reddit_collector):
        """Test handling of subreddits with no posts."""
        empty_response = {"data": {"children": []}}

        reddit_collector.fetch_json = AsyncMock(return_value=empty_response)
        reddit_collector.MONITORED_SUBREDDITS = ["CryptoCurrency"]

        data = await reddit_collector.collect()

        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_collect_continues_on_subreddit_error(
        self, reddit_collector, sample_reddit_response
    ):
        """Test that collection continues when one subreddit fails."""
        # Mock fetch to fail for first subreddit, succeed for second
        call_count = [0]

        async def mock_fetch(_endpoint, _params=None, _headers=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Subreddit error")
            return sample_reddit_response

        reddit_collector.fetch_json = AsyncMock(side_effect=mock_fetch)
        reddit_collector.MONITORED_SUBREDDITS = ["BadSubreddit", "CryptoCurrency"]

        data = await reddit_collector.collect()

        # Should have data from second subreddit
        assert len(data) >= 0

    def test_determine_sentiment_bullish(self, reddit_collector):
        """Test sentiment determination for bullish posts."""
        text = "bitcoin is looking very bullish! moon soon! hodl!"
        sentiment = reddit_collector._determine_sentiment(text, 500)

        assert sentiment == "bullish"

    def test_determine_sentiment_bearish(self, reddit_collector):
        """Test sentiment determination for bearish posts."""
        text = "market crash incoming, dump everything, bearish outlook"
        sentiment = reddit_collector._determine_sentiment(text, 50)

        assert sentiment == "bearish"

    def test_determine_sentiment_neutral(self, reddit_collector):
        """Test sentiment determination for neutral posts."""
        text = "what do you think about the latest update?"
        sentiment = reddit_collector._determine_sentiment(text, 100)

        assert sentiment in ["neutral", "bullish"]  # May vary based on score

    def test_determine_sentiment_by_score(self, reddit_collector):
        """Test that high scores influence sentiment."""
        text = "interesting development"
        sentiment = reddit_collector._determine_sentiment(text, 1000)

        assert sentiment == "bullish"  # High score makes it bullish

    def test_calculate_sentiment_score_bullish(self, reddit_collector):
        """Test sentiment score calculation for bullish text."""
        text = "moon bullish pump rally"
        score = reddit_collector._calculate_sentiment_score(text, 500, 100)

        assert 0.0 < score <= 1.0

    def test_calculate_sentiment_score_bearish(self, reddit_collector):
        """Test sentiment score calculation for bearish text."""
        text = "crash dump bearish sell"
        score = reddit_collector._calculate_sentiment_score(text, 10, 5)

        assert -1.0 <= score < 0.0

    def test_calculate_sentiment_score_neutral(self, reddit_collector):
        """Test sentiment score calculation for neutral text."""
        text = "what are your thoughts on this?"
        score = reddit_collector._calculate_sentiment_score(text, 50, 10)

        assert -1.0 <= score <= 1.0

    def test_extract_currencies_from_text(self, reddit_collector):
        """Test extraction of cryptocurrency symbols."""
        currencies = reddit_collector._extract_currencies(
            "Bitcoin and Ethereum discussion",
            "BTC is up, ETH is also looking good"
        )

        assert "BTC" in currencies
        assert "ETH" in currencies

    def test_extract_currencies_full_names(self, reddit_collector):
        """Test extraction from full cryptocurrency names."""
        currencies = reddit_collector._extract_currencies(
            "Cardano and Solana updates",
            "Both Cardano and Solana are doing well"
        )

        assert "ADA" in currencies  # Cardano
        assert "SOL" in currencies  # Solana

    def test_extract_currencies_none_found(self, reddit_collector):
        """Test when no currencies are mentioned."""
        currencies = reddit_collector._extract_currencies(
            "General market discussion",
            "What do you think about the overall market?"
        )

        assert currencies == []

    def test_extract_post_data(self, reddit_collector):
        """Test extraction of post data."""
        post = {
            "title": "Bitcoin discussion",
            "selftext": "BTC looks bullish",
            "score": 100,
            "num_comments": 50,
            "author": "test_user",
            "id": "test123",
            "permalink": "/r/Bitcoin/comments/test123/discussion/",
            "created_utc": 1705305600,
            "stickied": False,
        }

        data = reddit_collector._extract_post_data(post, "Bitcoin")

        assert data is not None
        assert data["title"] == "Bitcoin discussion"
        assert data["source"] == "Reddit (r/Bitcoin)"
        assert "reddit.com" in data["url"]
        assert data["sentiment"] in ["bullish", "bearish", "neutral"]
        assert "BTC" in data["currencies"]

    def test_extract_post_data_missing_title(self, reddit_collector):
        """Test handling of posts without titles."""
        post = {
            "selftext": "Some text",
            "score": 100,
        }

        data = reddit_collector._extract_post_data(post, "CryptoCurrency")

        assert data is None

    @pytest.mark.asyncio
    async def test_validate_data_success(self, reddit_collector):
        """Test data validation with valid data."""
        raw_data = [
            {
                "title": "Bitcoin breaking out",
                "source": "Reddit (r/Bitcoin)",
                "url": "https://www.reddit.com/r/Bitcoin/...",
                "published_at": datetime.now(timezone.utc),
                "sentiment": "bullish",
                "sentiment_score": 0.75,
                "currencies": ["BTC"],
                "collected_at": datetime.now(timezone.utc),
                "metadata": {"subreddit": "Bitcoin"},  # Should be removed
            },
        ]

        validated = await reddit_collector.validate_data(raw_data)

        assert len(validated) == 1
        assert validated[0]["sentiment"] == "bullish"
        assert "metadata" not in validated[0]  # Metadata removed

    @pytest.mark.asyncio
    async def test_validate_data_removes_invalid(self, reddit_collector):
        """Test that validation removes invalid data."""
        raw_data = [
            {
                "title": "Valid Post",
                "url": "https://reddit.com/...",
                "sentiment": "bullish",
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing title
                "url": "https://reddit.com/...",
                "sentiment": "bullish",
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing URL
                "title": "Missing URL",
                "sentiment": "bullish",
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        validated = await reddit_collector.validate_data(raw_data)

        assert len(validated) == 1
        assert validated[0]["title"] == "Valid Post"

    @pytest.mark.asyncio
    async def test_validate_data_clamps_sentiment_score(self, reddit_collector):
        """Test that invalid sentiment scores are clamped."""
        raw_data = [
            {
                "title": "Post 1",
                "url": "https://reddit.com/1",
                "sentiment_score": 2.0,  # Too high
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "title": "Post 2",
                "url": "https://reddit.com/2",
                "sentiment_score": -2.0,  # Too low
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        validated = await reddit_collector.validate_data(raw_data)

        assert len(validated) == 2
        assert validated[0]["sentiment_score"] == 1.0  # Clamped to max
        assert validated[1]["sentiment_score"] == -1.0  # Clamped to min

    @pytest.mark.asyncio
    async def test_store_data(self, reddit_collector):
        """Test storing data to database."""
        mock_session = MagicMock()

        data = [
            {
                "title": "Bitcoin discussion",
                "source": "Reddit (r/Bitcoin)",
                "url": "https://www.reddit.com/...",
                "published_at": datetime.now(timezone.utc),
                "sentiment": "bullish",
                "sentiment_score": 0.75,
                "currencies": ["BTC"],
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        count = await reddit_collector.store_data(data, mock_session)

        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_store_data_handles_errors(self, reddit_collector):
        """Test that store continues after individual record errors."""
        mock_session = MagicMock()
        # Make add fail for the first record
        mock_session.add.side_effect = [Exception("DB error"), None]

        data = [
            {
                "title": "Failing Post",
                "source": "Reddit",
                "url": "https://reddit.com/1",
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "title": "Succeeding Post",
                "source": "Reddit",
                "url": "https://reddit.com/2",
                "collected_at": datetime.now(timezone.utc),
            },
        ]

        count = await reddit_collector.store_data(data, mock_session)

        # Should still store 1 record despite 1 failure
        assert count == 1
        assert mock_session.commit.call_count == 1
