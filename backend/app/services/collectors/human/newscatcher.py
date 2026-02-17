# mypy: ignore-errors
"""
Newscatcher API collector for cryptocurrency news (Human Ledger).

This collector fetches cryptocurrency news articles from the Newscatcher API,
which aggregates news from 60,000+ sources worldwide with built-in sentiment analysis.

Data Source: https://www.newscatcherapi.com/docs
Collection Frequency: Every 5 minutes
Pricing: $10/month (1000 requests/month on Basic plan)
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session

from app.models import NewsSentiment
from app.services.collectors.api_collector import APICollector

logger = logging.getLogger(__name__)


class NewscatcherCollector(APICollector):
    """
    Collector for cryptocurrency news from Newscatcher API.

    Collects:
    - News headlines and summaries
    - Source information (clean URLs)
    - Publication timestamps
    - Built-in sentiment analysis
    - Article links

    API Documentation: https://www.newscatcherapi.com/docs
    """

    # Sentiment mapping from Newscatcher to our schema
    SENTIMENT_MAP = {
        "positive": "bullish",
        "negative": "bearish",
        "neutral": "neutral",
    }

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Newscatcher collector.

        Args:
            api_key: Newscatcher API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv("NEWSCATCHER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Newscatcher API key required. Set NEWSCATCHER_API_KEY environment variable "
                "or pass api_key parameter. Get a key at: https://www.newscatcherapi.com/"
            )

        super().__init__(
            name="newscatcher_api",
            ledger="human",
            base_url="https://v3-api.newscatcherapi.com/api",
            timeout=30,
            max_retries=3,
            rate_limit_delay=3.0,  # Stay within rate limits
        )

    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect recent cryptocurrency news from Newscatcher API.

        Returns:
            List of news article dictionaries

        Raises:
            Exception: If API request fails
        """
        logger.info(f"{self.name}: Collecting recent crypto news")

        try:
            # Search for cryptocurrency news from the last 24 hours
            from_date = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

            params = {
                "q": "cryptocurrency OR bitcoin OR ethereum OR crypto",
                "lang": "en",
                "from": from_date,
                "sort_by": "relevancy",
                "page_size": 50,  # Max allowed
            }

            # Use custom headers for API key authentication
            headers = {
                "x-api-key": self.api_key,
            }

            response = await self.fetch_json("/search", params=params, headers=headers)

            if not response or "articles" not in response:
                logger.warning(f"{self.name}: No articles in API response")
                return []

            articles = response["articles"]
            logger.info(f"{self.name}: Fetched {len(articles)} news articles")

            # Transform API response to our schema
            collected_data = []
            for article in articles:
                # Map sentiment
                sentiment = None
                if article.get("sentiment"):
                    sentiment = self.SENTIMENT_MAP.get(
                        article["sentiment"].lower(),
                        "neutral"
                    )

                # Parse publication timestamp
                published_at = None
                if "published_date" in article and article["published_date"]:
                    try:
                        published_at = datetime.fromisoformat(
                            article["published_date"].replace("Z", "+00:00")
                        )
                    except Exception as e:
                        logger.debug(f"{self.name}: Failed to parse timestamp: {str(e)}")

                data_point = {
                    "title": article.get("title", ""),
                    "source": article.get("clean_url"),  # Domain name as source
                    "url": article.get("link"),
                    "published_at": published_at,
                    "sentiment": sentiment,
                    "sentiment_score": None,  # Newscatcher provides categorical, not numerical
                    "currencies": None,  # Not explicitly provided by Newscatcher
                    "collected_at": datetime.now(timezone.utc),
                    "summary": article.get("summary"),  # Additional field
                }

                collected_data.append(data_point)

            logger.info(f"{self.name}: Collected {len(collected_data)} articles")
            return collected_data

        except Exception as e:
            logger.error(f"{self.name}: Failed to collect news: {str(e)}")
            raise

    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected news data.

        Args:
            data: Raw data collected from Newscatcher API

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
                    logger.warning(f"{self.name}: Missing URL for '{item['title'][:50]}...', skipping")
                    continue

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
                news_sentiment = NewsSentiment(
                    title=item["title"],
                    source=item.get("source"),
                    url=item.get("url"),
                    published_at=item.get("published_at"),
                    sentiment=item.get("sentiment"),
                    sentiment_score=None,  # Newscatcher doesn't provide numerical scores
                    currencies=item.get("currencies"),
                    collected_at=item["collected_at"],
                )

                session.add(news_sentiment)
                stored_count += 1

            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to store article '{item.get('title', 'unknown')[:50]}...': {str(e)}"
                )
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
