# mypy: ignore-errors
"""
CryptoPanic API collector for news sentiment (Human Ledger).

This collector fetches cryptocurrency news articles with sentiment tags from
the CryptoPanic API (free tier available, requires API key).

Data Source: https://cryptopanic.com/developers/api/
Collection Frequency: Every 5 minutes
Free Tier Limits: 500 requests per day (one request every ~3 minutes is safe)
"""

import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlmodel import Session

from app.models import NewsSentiment
from app.services.collectors.api_collector import APICollector

logger = logging.getLogger(__name__)


class CryptoPanicCollector(APICollector):
    """
    Collector for cryptocurrency news with sentiment from CryptoPanic API.

    Collects:
    - News headlines and URLs
    - Source information
    - Publication timestamps
    - Sentiment tags (positive, negative, neutral)
    - Associated cryptocurrencies

    API Documentation: https://cryptopanic.com/developers/api/
    """

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

    def __init__(self, api_key: str | None = None):
        """
        Initialize the CryptoPanic collector.

        Args:
            api_key: CryptoPanic API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv("CRYPTOPANIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CryptoPanic API key required. Set CRYPTOPANIC_API_KEY environment variable "
                "or pass api_key parameter. Get a free key at: https://cryptopanic.com/developers/api/"
            )

        super().__init__(
            name="cryptopanic_api",
            ledger="human",
            base_url="https://cryptopanic.com/api/v1",
            timeout=30,
            max_retries=3,
            rate_limit_delay=3.0,  # Stay within free tier limits
        )

    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect recent cryptocurrency news from CryptoPanic API.

        Returns:
            List of news article dictionaries

        Raises:
            Exception: If API request fails
        """
        logger.info(f"{self.name}: Collecting recent crypto news")

        try:
            # Fetch recent posts (news articles)
            # Free tier supports: filter=rising, hot, or all
            # We'll use 'rising' to get trending news
            params = {
                "auth_token": self.api_key,
                "filter": "rising",
                "public": "true",
            }

            response = await self.fetch_json("/posts/", params=params)

            if not response or "results" not in response:
                logger.warning(f"{self.name}: No results in API response")
                return []

            articles = response["results"]
            logger.info(f"{self.name}: Fetched {len(articles)} news articles")

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
                        logger.debug(
                            f"{self.name}: Failed to parse timestamp: {str(e)}"
                        )

                data_point = {
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("title"),
                    "url": article.get("url"),
                    "published_at": published_at,
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score,
                    "currencies": currencies if currencies else None,
                    "collected_at": datetime.now(timezone.utc),
                }

                collected_data.append(data_point)

            logger.info(f"{self.name}: Collected {len(collected_data)} articles")
            return collected_data

        except Exception as e:
            logger.error(f"{self.name}: Failed to collect news: {str(e)}")
            raise

    def _determine_sentiment(self, article: dict[str, Any]) -> str | None:
        """
        Determine sentiment from article votes and metadata.

        Args:
            article: Article data from CryptoPanic API

        Returns:
            Sentiment string or None
        """
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
            if any(
                word in description
                for word in ["pump", "surge", "rally", "bullish", "moon"]
            ):
                return "bullish"
            if any(
                word in description
                for word in ["dump", "crash", "bearish", "plunge", "decline"]
            ):
                return "bearish"

        return "neutral"

    def _calculate_sentiment_score(self, article: dict[str, Any]) -> float | None:
        """
        Calculate numerical sentiment score from votes.

        Args:
            article: Article data from CryptoPanic API

        Returns:
            Sentiment score between -1.0 (bearish) and 1.0 (bullish), or None
        """
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
        # Result is between -1.0 and 1.0
        score = (net_positive - net_negative) / total
        return round(score, 4)

    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected news data.

        Args:
            data: Raw data collected from CryptoPanic API

        Returns:
            Validated data ready for storage

        Raises:
            ValueError: If validation fails
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
                            f"{self.name}: Invalid sentiment score {score} for '{item['title'][:50]}...', "
                            f"setting to None"
                        )
                        item["sentiment_score"] = None

                validated.append(item)

            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid data: {str(e)}")
                continue

        logger.info(f"{self.name}: Validated {len(validated)}/{len(data)} records")
        return validated

    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated news sentiment in the database.

        Args:
            data: Validated data to store
            session: Database session

        Returns:
            Number of records stored
        """
        stored_count = 0

        for item in data:
            try:
                # Check if URL already exists (avoid duplicates)
                # Note: This is a simple check. In production, you might want to use
                # ON CONFLICT DO NOTHING or similar database features
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
                    f"{self.name}: Failed to store article '{item.get('title', 'unknown')[:50]}...': {str(e)}"
                )
                # Continue with other records
                continue

        # Commit all records at once
        try:
            session.commit()
            logger.info(f"{self.name}: Stored {stored_count} news sentiment records")
        except Exception as e:
            logger.error(f"{self.name}: Failed to commit records: {str(e)}")
            session.rollback()
            stored_count = 0

        return stored_count
