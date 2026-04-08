"""
Reddit API collector plugin for community sentiment (Human Ledger).

This collector fetches cryptocurrency discussions from Reddit to gauge
community sentiment and trending topics.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.core.config import HTTP_USER_AGENT
from app.models import SocialSentiment

logger = logging.getLogger(__name__)


class HumanReddit(ICollector):
    """Collector for cryptocurrency discussions from Reddit."""

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
        "moon",
        "bullish",
        "pump",
        "rally",
        "surge",
        "breakout",
        "buy",
        "long",
        "hold",
        "hodl",
        "gem",
        "undervalued",
        "adoption",
        "institutional",
        "partnership",
        "breakthrough",
    ]

    BEARISH_KEYWORDS = [
        "crash",
        "dump",
        "bearish",
        "short",
        "sell",
        "drop",
        "decline",
        "plunge",
        "collapse",
        "scam",
        "rug",
        "bear",
        "overvalued",
        "bubble",
        "dead",
        "fail",
    ]

    @property
    def name(self) -> str:
        return "human_reddit"

    @property
    def description(self) -> str:
        return "Reddit crypto community sentiment from r/CryptoCurrency and related subreddits"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subreddits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Subreddits to monitor",
                    "default": self.MONITORED_SUBREDDITS,
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of posts to fetch per subreddit",
                    "default": 25,
                },
                "rate_limit_delay": {
                    "type": "number",
                    "description": "Delay between requests in seconds",
                    "default": 2.0,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "subreddits" in config:
            if not isinstance(config["subreddits"], list):
                logger.error("Invalid config: 'subreddits' must be a list")
                return False

        if "limit" in config:
            try:
                int(config["limit"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'limit' must be an integer")
                return False

        if "rate_limit_delay" in config:
            try:
                float(config["rate_limit_delay"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'rate_limit_delay' must be a number")
                return False

        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to Reddit API."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": HTTP_USER_AGENT}
                async with session.get(
                    "https://www.reddit.com/r/CryptoCurrency/hot.json",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test Reddit connection: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect hot/trending posts from monitored subreddits."""
        subreddits = config.get("subreddits", self.MONITORED_SUBREDDITS)
        limit = config.get("limit", 25)
        rate_limit_delay = config.get("rate_limit_delay", 2.0)

        logger.info(f"Collecting posts from {len(subreddits)} subreddits")

        all_posts = []
        seen_urls: set[str] = set()

        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": HTTP_USER_AGENT}

            for subreddit in subreddits:
                try:
                    await asyncio.sleep(rate_limit_delay)

                    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                    params = {"limit": limit, "raw_json": 1}

                    async with session.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(
                                f"Failed to fetch r/{subreddit}: status {resp.status}"
                            )
                            continue

                        data = await resp.json()

                    if not data or "data" not in data or "children" not in data["data"]:
                        logger.warning(f"No data returned for r/{subreddit}")
                        continue

                    posts = data["data"]["children"]
                    logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")

                    for post in posts:
                        try:
                            post_data = post.get("data", {})
                            title = post_data.get("title", "")
                            created_utc = post_data.get("created_utc")

                            # Intra-run dedup by permalink
                            permalink = post_data.get("permalink", "")
                            post_url = (
                                f"https://reddit.com{permalink}" if permalink else None
                            )
                            if post_url and post_url in seen_urls:
                                continue
                            if post_url:
                                seen_urls.add(post_url)

                            # Parse publication timestamp
                            published_at = None
                            if created_utc:
                                try:
                                    published_at = datetime.fromtimestamp(
                                        created_utc, tz=timezone.utc
                                    )
                                except Exception:
                                    pass

                            # Analyze sentiment from title
                            sentiment = self._analyze_sentiment(title)

                            # Extract cryptocurrencies mentioned
                            currencies = self._extract_currencies(title)

                            # Create SocialSentiment record
                            data_point = SocialSentiment(
                                platform="reddit",
                                content=title,
                                author=post_data.get("author"),
                                score=post_data.get("score"),
                                sentiment=sentiment,
                                currencies=currencies if currencies else None,
                                posted_at=published_at,
                                collected_at=datetime.now(timezone.utc),
                            )

                            all_posts.append(data_point)

                        except Exception as e:
                            logger.debug(f"Failed to parse Reddit post: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Failed to collect posts from r/{subreddit}: {e}")
                    continue

        logger.info(f"Collected {len(all_posts)} posts total")
        return all_posts

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment from text using keyword matching."""
        text_lower = text.lower()

        bullish_count = sum(
            1 for keyword in self.BULLISH_KEYWORDS if keyword in text_lower
        )
        bearish_count = sum(
            1 for keyword in self.BEARISH_KEYWORDS if keyword in text_lower
        )

        if bullish_count > bearish_count and bullish_count > 0:
            return "bullish"
        elif bearish_count > bullish_count and bearish_count > 0:
            return "bearish"
        else:
            return "neutral"

    def _extract_currencies(self, text: str) -> list[str]:
        """Extract cryptocurrency symbols from text."""
        # Common crypto symbols and full names
        crypto_patterns = [
            (r"\bBTC\b", "BTC"),
            (r"\bBitcoin\b", "BTC"),
            (r"\bETH\b", "ETH"),
            (r"\bEthereum\b", "ETH"),
            (r"\bADA\b", "ADA"),
            (r"\bCardano\b", "ADA"),
            (r"\bDOGE\b", "DOGE"),
            (r"\bXRP\b", "XRP"),
            (r"\bRipple\b", "XRP"),
            (r"\bSOL\b", "SOL"),
            (r"\bSolana\b", "SOL"),
            (r"\bAVAX\b", "AVAX"),
            (r"\bAvalanche\b", "AVAX"),
            (r"\bPOLYGON\b", "POLYGON"),
            (r"\bARB\b", "ARB"),
            (r"\bArbitrum\b", "ARB"),
            (r"\bOP\b", "OP"),
            (r"\bOptimism\b", "OP"),
            (r"\bLINK\b", "LINK"),
            (r"\bChainlink\b", "LINK"),
            (r"\bUNI\b", "UNI"),
            (r"\bUniswap\b", "UNI"),
            (r"\bAAVE\b", "AAVE"),
            (r"\bCRV\b", "CRV"),
            (r"\bCurve\b", "CRV"),
        ]

        found_cryptos = []
        for pattern, symbol in crypto_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_cryptos.append(symbol)

        return list(set(found_cryptos))  # Remove duplicates


CollectorRegistry.register(HumanReddit)
