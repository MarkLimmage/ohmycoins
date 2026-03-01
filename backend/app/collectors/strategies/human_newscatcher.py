"""
Newscatcher API collector plugin for cryptocurrency news (Human Ledger).

This collector fetches cryptocurrency news articles from the Newscatcher API,
which aggregates news from 60,000+ sources worldwide with built-in sentiment analysis.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import NewsSentiment

logger = logging.getLogger(__name__)


class HumanNewscatcher(ICollector):
    """Collector for cryptocurrency news from Newscatcher API."""

    # Sentiment mapping from Newscatcher to our schema
    SENTIMENT_MAP = {
        "positive": "bullish",
        "negative": "bearish",
        "neutral": "neutral",
    }

    @property
    def name(self) -> str:
        return "human_newscatcher"

    @property
    def description(self) -> str:
        return "Aggregated news from 60k+ sources via Newscatcher API"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "hours_back": {
                    "type": "integer",
                    "description": "Hours back to search for news",
                    "default": 24,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum articles to return",
                    "default": 50,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "hours_back" in config:
            try:
                int(config["hours_back"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'hours_back' must be an integer")
                return False

        if "limit" in config:
            try:
                int(config["limit"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'limit' must be an integer")
                return False

        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to Newscatcher API."""
        api_key = os.getenv("NEWSCATCHER_API_KEY")
        if not api_key:
            logger.warning("NEWSCATCHER_API_KEY not set")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": api_key}
                params = {
                    "q": "cryptocurrency",
                    "lang": "en",
                    "limit": 1,
                }
                async with session.get(
                    "https://v3-api.newscatcherapi.com/api/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test Newscatcher connection: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect recent cryptocurrency news from Newscatcher API."""
        api_key = os.getenv("NEWSCATCHER_API_KEY")
        if not api_key:
            logger.warning("NEWSCATCHER_API_KEY not configured. Skipping collection.")
            return []

        hours_back = config.get("hours_back", 24)
        limit = config.get("limit", 50)

        logger.info("Collecting recent crypto news from Newscatcher")

        try:
            from_date = (
                datetime.now(timezone.utc) - timedelta(hours=hours_back)
            ).isoformat()

            params = {
                "q": "cryptocurrency OR bitcoin OR ethereum OR crypto",
                "lang": "en",
                "from": from_date,
                "sort_by": "relevancy",
                "page": 1,
                "limit": limit,
            }

            async with aiohttp.ClientSession() as session:
                headers = {"x-api-key": api_key}

                async with session.get(
                    "https://v3-api.newscatcherapi.com/api/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"API error: {resp.status}")
                        return []

                    response = await resp.json()

            if not response or "articles" not in response:
                logger.warning("No articles in API response")
                return []

            articles = response.get("articles", [])
            logger.info(f"Fetched {len(articles)} news articles")

            # Transform API response to our schema
            collected_data = []
            for article in articles:
                try:
                    title = article.get("title", "")
                    if not title:
                        continue

                    # Get sentiment from Newscatcher's sentiment field
                    sentiment_raw = article.get("sentiment", "neutral")
                    sentiment = self.SENTIMENT_MAP.get(sentiment_raw, "neutral")

                    # Parse publication timestamp
                    published_at = None
                    if "published_date" in article and article["published_date"]:
                        try:
                            published_at = datetime.fromisoformat(
                                article["published_date"].replace("Z", "+00:00")
                            )
                        except Exception:
                            pass

                    # Extract source URL (Newscatcher provides clean URLs)
                    url = article.get("link")

                    # Get source name from the article
                    source = article.get("source", "newscatcher")

                    data_point = NewsSentiment(
                        title=title,
                        source=source,
                        url=url,
                        published_at=published_at,
                        sentiment=sentiment,
                        sentiment_score=None,  # Newscatcher doesn't provide numeric scores
                        currencies=None,  # Could extract, but keep it simple for now
                        collected_at=datetime.now(timezone.utc),
                    )

                    collected_data.append(data_point)

                except Exception as e:
                    logger.debug(f"Failed to parse article: {e}")
                    continue

            logger.info(f"Collected {len(collected_data)} articles")
            return collected_data

        except Exception as e:
            logger.error(f"Failed to collect news: {e}")
            return []


CollectorRegistry.register(HumanNewscatcher)
