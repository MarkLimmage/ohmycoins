"""
CryptoPanic API collector plugin for news sentiment (Human Ledger).

This collector fetches cryptocurrency news articles with sentiment tags from
the CryptoPanic API (free tier available, requires API key).
"""

import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import NewsSentiment

logger = logging.getLogger(__name__)


class NewsCryptoPanic(ICollector):
    """Collector for cryptocurrency news with sentiment from CryptoPanic API."""

    # Sentiment mapping from CryptoPanic tags to our schema
    SENTIMENT_MAP = {
        "positive": "bullish",
        "negative": "bearish",
        "neutral": "neutral",
        "important": "important",
        "hot": "trending",
        "saved": "saved",
        "lol": "humor",
    }

    @property
    def name(self) -> str:
        return "news_cryptopanic"

    @property
    def description(self) -> str:
        return "Crypto news with sentiment analysis from CryptoPanic API"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": ["rising", "hot", "all"],
                    "default": "rising",
                    "description": "News filter type",
                }
            },
            "required": [],
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        if "filter" in config:
            if config["filter"] not in ["rising", "hot", "all"]:
                logger.error("Invalid config: 'filter' must be 'rising', 'hot', or 'all'")
                return False
        return True

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test connectivity to CryptoPanic API."""
        api_key = os.getenv("CRYPTOPANIC_API_KEY")
        if not api_key:
            logger.warning("CRYPTOPANIC_API_KEY not set")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "auth_token": api_key,
                    "filter": "rising",
                    "public": "true",
                }
                async with session.get(
                    "https://cryptopanic.com/api/v1/posts/",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test CryptoPanic connection: {e}")
            return False

    async def collect(self, config: Dict[str, Any]) -> List[Any]:
        """Collect recent cryptocurrency news from CryptoPanic API."""
        api_key = os.getenv("CRYPTOPANIC_API_KEY")
        if not api_key:
            logger.warning("CRYPTOPANIC_API_KEY not configured. Skipping collection.")
            return []

        filter_type = config.get("filter", "rising")
        logger.info("Collecting recent crypto news from CryptoPanic")

        try:
            params = {
                "auth_token": api_key,
                "filter": filter_type,
                "public": "true",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://cryptopanic.com/api/v1/posts/",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"API error: {resp.status}")
                        return []

                    response = await resp.json()

            if not response or "results" not in response:
                logger.warning("No results in API response")
                return []

            articles = response["results"]
            logger.info(f"Fetched {len(articles)} news articles")

            # Transform API response to our schema
            collected_data = []
            for article in articles:
                # Extract sentiment from votes
                sentiment = self._determine_sentiment(article)
                sentiment_score = self._calculate_sentiment_score(article)

                # Extract currencies
                currencies = []
                if "currencies" in article and article["currencies"]:
                    currencies = [
                        currency.get("code") or currency.get("title")
                        for currency in article["currencies"]
                        if currency.get("code") or currency.get("title")
                    ]

                # Parse publication timestamp
                published_at = None
                if "published_at" in article and article["published_at"]:
                    try:
                        published_at = datetime.fromisoformat(
                            article["published_at"].replace("Z", "+00:00")
                        )
                    except Exception as e:
                        logger.debug(f"Failed to parse timestamp: {e}")

                data_point = NewsSentiment(
                    title=article.get("title", ""),
                    source=article.get("source", {}).get("title"),
                    url=article.get("url"),
                    published_at=published_at,
                    sentiment=sentiment,
                    sentiment_score=(
                        Decimal(str(sentiment_score))
                        if sentiment_score is not None
                        else None
                    ),
                    currencies=currencies if currencies else None,
                    collected_at=datetime.now(timezone.utc),
                )

                collected_data.append(data_point)

            logger.info(f"Collected {len(collected_data)} articles")
            return collected_data

        except Exception as e:
            logger.error(f"Failed to collect news: {e}")
            return []

    def _determine_sentiment(self, article: Dict[str, Any]) -> str | None:
        """Determine sentiment from article votes and metadata."""
        votes = article.get("votes", {})

        # Check for sentiment votes
        if votes:
            positive = votes.get("positive", 0)
            negative = votes.get("negative", 0)
            important = votes.get("important", 0)
            liked = votes.get("liked", 0)
            disliked = votes.get("disliked", 0)

            # Calculate net sentiment
            net_positive = positive + liked
            net_negative = negative + disliked

            if net_positive > net_negative and net_positive > 0:
                return "bullish"
            elif net_negative > net_positive and net_negative > 0:
                return "bearish"
            elif important > 0:
                return "important"

        # Check metadata for sentiment hints
        metadata = article.get("metadata", {})
        if metadata:
            description = (metadata.get("description") or "").lower()
            if any(word in description for word in ["pump", "surge", "rally", "bullish", "moon"]):
                return "bullish"
            if any(word in description for word in ["dump", "crash", "bearish", "plunge", "decline"]):
                return "bearish"

        return "neutral"

    def _calculate_sentiment_score(self, article: Dict[str, Any]) -> float | None:
        """Calculate numerical sentiment score from votes."""
        votes = article.get("votes", {})

        if not votes:
            return None

        positive = votes.get("positive", 0)
        negative = votes.get("negative", 0)
        liked = votes.get("liked", 0)
        disliked = votes.get("disliked", 0)

        net_positive = positive + liked
        net_negative = negative + disliked
        total = net_positive + net_negative

        if total == 0:
            return 0.0

        # Calculate score: (positive - negative) / total
        score = (net_positive - net_negative) / total
        return float(round(score, 4))


CollectorRegistry.register(NewsCryptoPanic)
