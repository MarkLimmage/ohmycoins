# mypy: ignore-errors
"""
Reddit API collector for community sentiment (Human Ledger).

This collector fetches cryptocurrency discussions from Reddit to gauge
community sentiment and trending topics.

Data Source: Reddit JSON API (https://www.reddit.com/dev/api)
Collection Frequency: Every 15 minutes
Cost: Free (public API, no authentication required for public data)

Monitored Subreddits:
- r/CryptoCurrency (general crypto discussion)
- r/Bitcoin (Bitcoin specific)
- r/ethereum (Ethereum specific)
- r/CryptoMarkets (market discussion)
- r/altcoin (altcoin discussion)

Note: Using Reddit's JSON API which doesn't require authentication
for reading public posts. For authenticated API access, use PRAW library.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.models import NewsSentiment
from app.services.collectors.api_collector import APICollector

logger = logging.getLogger(__name__)


class RedditCollector(APICollector):
    """
    Collector for cryptocurrency discussions from Reddit.

    Collects:
    - Hot/trending posts from crypto subreddits
    - Post titles, scores, comments
    - Submission timestamps
    - Mentioned cryptocurrencies

    Uses Reddit's public JSON API for reading public posts.
    """

    # Subreddits to monitor
    MONITORED_SUBREDDITS = [
        "CryptoCurrency",
        "Bitcoin",
        "ethereum",
        "CryptoMarkets",
        "altcoin",
    ]

    # Sentiment keywords for basic sentiment analysis
    BULLISH_KEYWORDS = [
        "moon", "bullish", "pump", "rally", "surge", "breakout",
        "buy", "long", "hold", "hodl", "gem", "undervalued",
        "adoption", "institutional", "partnership", "breakthrough",
    ]

    BEARISH_KEYWORDS = [
        "crash", "dump", "bearish", "short", "sell", "drop",
        "decline", "plunge", "collapse", "scam", "rug", "bear",
        "overvalued", "bubble", "dead", "fail",
    ]

    def __init__(self):
        """Initialize the Reddit collector."""
        super().__init__(
            name="reddit_api",
            ledger="human",
            base_url="https://www.reddit.com",
            timeout=30,
            max_retries=3,
            rate_limit_delay=2.0,  # Be respectful to Reddit's API
        )

        # Reddit requires a custom User-Agent
        self.user_agent = "OhMyCoins/1.0 (https://github.com/MarkLimmage/ohmycoins)"

    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect hot/trending posts from monitored subreddits.

        Returns:
            List of post data dictionaries

        Raises:
            Exception: If API request fails
        """
        logger.info(
            f"{self.name}: Collecting posts from {len(self.MONITORED_SUBREDDITS)} subreddits"
        )

        all_posts = []

        for subreddit in self.MONITORED_SUBREDDITS:
            try:
                # Fetch hot posts from subreddit using JSON API
                # Reddit's JSON API: /r/subreddit/hot.json
                headers = {
                    "User-Agent": self.user_agent,
                }

                params = {
                    "limit": 25,  # Get top 25 hot posts
                    "raw_json": 1,  # Get unescaped JSON
                }

                response = await self.fetch_json(
                    f"/r/{subreddit}/hot.json",
                    params=params,
                    headers=headers
                )

                if not response or "data" not in response:
                    logger.warning(f"{self.name}: No data for r/{subreddit}")
                    continue

                posts = response["data"].get("children", [])

                for post_wrapper in posts:
                    post = post_wrapper.get("data", {})

                    # Skip stickied/pinned posts (usually mod announcements)
                    if post.get("stickied", False):
                        continue

                    # Extract post data
                    post_data = self._extract_post_data(post, subreddit)

                    if post_data:
                        all_posts.append(post_data)
                        logger.debug(
                            f"{self.name}: Found post in r/{subreddit}: "
                            f"{post_data['title'][:50]}..."
                        )

                logger.info(
                    f"{self.name}: Collected {len(posts)} posts from r/{subreddit}"
                )

            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to collect from r/{subreddit}: {str(e)}"
                )
                # Continue with other subreddits
                continue

        logger.info(f"{self.name}: Collected {len(all_posts)} posts total")
        return all_posts

    def _extract_post_data(self, post: dict[str, Any], subreddit: str) -> dict[str, Any] | None:
        """
        Extract structured data from a Reddit post.

        Args:
            post: Reddit post data from API
            subreddit: Name of the subreddit

        Returns:
            Dictionary with post data or None if extraction fails
        """
        try:
            title = post.get("title", "")
            if not title:
                return None

            # Get post metadata
            score = post.get("score", 0)
            num_comments = post.get("num_comments", 0)
            author = post.get("author", "[deleted]")
            post_id = post.get("id", "")
            permalink = post.get("permalink", "")

            # Build full URL
            url = f"https://www.reddit.com{permalink}" if permalink else None

            # Parse timestamp
            created_utc = post.get("created_utc")
            published_at = None
            if created_utc:
                try:
                    published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                except Exception as e:
                    logger.debug(f"{self.name}: Failed to parse timestamp: {str(e)}")

            # Combine title and selftext for sentiment analysis
            selftext = post.get("selftext", "")
            full_text = f"{title} {selftext}".lower()

            # Determine sentiment
            sentiment = self._determine_sentiment(full_text, score)
            sentiment_score = self._calculate_sentiment_score(full_text, score, num_comments)

            # Extract mentioned cryptocurrencies
            currencies = self._extract_currencies(title, selftext)

            return {
                "title": title,
                "source": f"Reddit (r/{subreddit})",
                "url": url,
                "published_at": published_at,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "currencies": currencies if currencies else None,
                "collected_at": datetime.now(timezone.utc),
                # Store additional metadata for potential future use
                "metadata": {
                    "subreddit": subreddit,
                    "author": author,
                    "score": score,
                    "num_comments": num_comments,
                    "post_id": post_id,
                }
            }

        except Exception as e:
            logger.debug(f"{self.name}: Failed to extract post data: {str(e)}")
            return None

    def _determine_sentiment(self, text: str, score: int) -> str:
        """
        Determine sentiment from post text and score.

        Args:
            text: Post text (title + body, lowercased)
            score: Post score (upvotes - downvotes)

        Returns:
            Sentiment string: "bullish", "bearish", or "neutral"
        """
        bullish_count = sum(1 for keyword in self.BULLISH_KEYWORDS if keyword in text)
        bearish_count = sum(1 for keyword in self.BEARISH_KEYWORDS if keyword in text)

        # Consider both keyword counts and post score
        if bullish_count > bearish_count:
            if score >= 100:  # Highly upvoted bullish post
                return "bullish"
            elif bullish_count >= 2:  # Multiple bullish keywords
                return "bullish"
        elif bearish_count > bullish_count:
            if bearish_count >= 2:  # Multiple bearish keywords
                return "bearish"

        # Check score as fallback
        if score >= 500:
            return "bullish"  # Very popular posts tend to be bullish
        elif score < 0:
            return "bearish"  # Downvoted posts are negative

        return "neutral"

    def _calculate_sentiment_score(
        self, text: str, score: int, num_comments: int
    ) -> float:
        """
        Calculate numerical sentiment score.

        Args:
            text: Post text (lowercased)
            score: Post score
            num_comments: Number of comments

        Returns:
            Sentiment score between -1.0 (bearish) and 1.0 (bullish)
        """
        # Count sentiment keywords
        bullish_count = sum(1 for keyword in self.BULLISH_KEYWORDS if keyword in text)
        bearish_count = sum(1 for keyword in self.BEARISH_KEYWORDS if keyword in text)

        # Calculate keyword-based component (-1 to 1)
        keyword_total = bullish_count + bearish_count
        if keyword_total > 0:
            keyword_score = (bullish_count - bearish_count) / keyword_total
        else:
            keyword_score = 0.0

        # Calculate engagement-based component (0 to 1)
        # Higher scores and more comments indicate positive engagement
        engagement_score = 0.0
        if score > 0:
            # Normalize score (logarithmic scale)
            import math
            engagement_score = min(math.log10(score + 1) / 4.0, 1.0)  # Max at 10k score

        # Combine: 70% keywords, 30% engagement
        combined_score = (keyword_score * 0.7) + (engagement_score * 0.3)

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, combined_score))

    def _extract_currencies(self, title: str, text: str) -> list[str]:
        """
        Extract mentioned cryptocurrency symbols from text.

        Args:
            title: Post title
            text: Post body

        Returns:
            List of currency symbols
        """
        content = f"{title} {text}".upper()
        currencies = []

        # Common cryptocurrency symbols and full names
        crypto_patterns = {
            "BTC": ["BTC", "BITCOIN", r"\bXBT\b"],
            "ETH": ["ETH", "ETHEREUM"],
            "XRP": ["XRP", "RIPPLE"],
            "ADA": ["ADA", "CARDANO"],
            "SOL": ["SOL", "SOLANA"],
            "DOT": ["DOT", "POLKADOT"],
            "DOGE": ["DOGE", "DOGECOIN"],
            "MATIC": ["MATIC", "POLYGON"],
            "SHIB": ["SHIB", "SHIBA"],
            "AVAX": ["AVAX", "AVALANCHE"],
            "UNI": ["UNI", "UNISWAP"],
            "LINK": ["LINK", "CHAINLINK"],
            "LTC": ["LTC", "LITECOIN"],
            "BCH": ["BCH", "BITCOIN CASH"],
            "ATOM": ["ATOM", "COSMOS"],
            "ALGO": ["ALGO", "ALGORAND"],
        }

        for symbol, patterns in crypto_patterns.items():
            for pattern in patterns:
                if re.search(rf"\b{pattern}\b", content):
                    if symbol not in currencies:
                        currencies.append(symbol)
                    break

        return currencies

    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected Reddit post data.

        Args:
            data: Raw data collected from Reddit API

        Returns:
            Validated data ready for storage
        """
        validated = []

        for item in data:
            try:
                # Validate required fields
                if not item.get("title"):
                    logger.warning(f"{self.name}: Missing title, skipping")
                    continue

                if not item.get("url"):
                    logger.warning(
                        f"{self.name}: Missing URL for '{item['title'][:50]}...', skipping"
                    )
                    continue

                # Validate sentiment score if present
                if item.get("sentiment_score") is not None:
                    score = float(item["sentiment_score"])
                    if score < -1.0 or score > 1.0:
                        logger.warning(
                            f"{self.name}: Invalid sentiment score {score}, clamping"
                        )
                        item["sentiment_score"] = max(-1.0, min(1.0, score))

                # Remove metadata from stored data (it's not in the schema)
                if "metadata" in item:
                    del item["metadata"]

                validated.append(item)

            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid data: {str(e)}")
                continue

        logger.info(f"{self.name}: Validated {len(validated)}/{len(data)} records")
        return validated

    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated Reddit posts in the database.

        Args:
            data: Validated data to store
            session: Database session

        Returns:
            Number of records stored
        """
        stored_count = 0

        for item in data:
            try:
                from decimal import Decimal

                news_sentiment = NewsSentiment(
                    title=item["title"],
                    source=item.get("source"),
                    url=item.get("url"),
                    published_at=item.get("published_at"),
                    sentiment=item.get("sentiment"),
                    sentiment_score=(
                        Decimal(str(item["sentiment_score"]))
                        if item.get("sentiment_score") is not None
                        else None
                    ),
                    currencies=item.get("currencies"),
                    collected_at=item["collected_at"],
                )

                session.add(news_sentiment)
                stored_count += 1

            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to store post "
                    f"'{item.get('title', 'unknown')[:50]}...': {str(e)}"
                )
                # Continue with other records
                continue

        # Commit all records at once
        try:
            session.commit()
            logger.info(f"{self.name}: Stored {stored_count} Reddit post records")
        except Exception as e:
            logger.error(f"{self.name}: Failed to commit records: {str(e)}")
            session.rollback()
            stored_count = 0

        return stored_count
