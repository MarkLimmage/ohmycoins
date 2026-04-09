"""
CryptoPanic API collector plugin for community-voted crypto news sentiment.

This collector fetches important, community-voted news items from CryptoPanic,
mapping vote data directly to sentiment scores without requiring downstream
LLM enrichment.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.core.config import settings
from app.models import SocialSentiment

logger = logging.getLogger(__name__)

DEFAULT_CURRENCIES = "BTC,ETH,SOL,AVAX,LINK,AAVE,UNI,DOT,ADA,MATIC"


class CryptoPanicCollector(ICollector):
    """Collector for community-voted crypto news from CryptoPanic."""

    API_BASE = "https://cryptopanic.com/api/developer/v4/posts/"

    @property
    def name(self) -> str:
        return "human_cryptopanic"

    @property
    def description(self) -> str:
        return "Community-voted crypto news sentiment from CryptoPanic"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "currencies": {
                    "type": "string",
                    "description": "Comma-separated currency codes to track",
                    "default": DEFAULT_CURRENCIES,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "currencies" in config:
            if not isinstance(config["currencies"], str):
                logger.error(
                    "Invalid config: 'currencies' must be a comma-separated string"
                )
                return False
        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to CryptoPanic API."""
        if not settings.CRYPTOPANIC_API_KEY:
            logger.warning("CRYPTOPANIC_API_KEY not set — cannot connect")
            return False
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "auth_token": settings.CRYPTOPANIC_API_KEY,
                    "filter": "important",
                    "kind": "news",
                    "public": "true",
                    "currencies": "BTC",
                }
                async with session.get(
                    self.API_BASE,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test CryptoPanic connection: {e}")
            return False

    @staticmethod
    def _derive_sentiment(votes: dict[str, Any]) -> str:
        """Derive sentiment from community votes."""
        positive = votes.get("positive", 0) or 0
        negative = votes.get("negative", 0) or 0
        if positive > negative * 2:
            return "positive"
        if negative > positive * 2:
            return "negative"
        return "neutral"

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect community-voted important news from CryptoPanic."""
        if not settings.CRYPTOPANIC_API_KEY:
            logger.warning("CRYPTOPANIC_API_KEY not set — skipping collection")
            return []

        currencies = config.get("currencies", DEFAULT_CURRENCIES)

        params = {
            "auth_token": settings.CRYPTOPANIC_API_KEY,
            "currencies": currencies,
            "filter": "important",
            "kind": "news",
            "public": "true",
        }

        logger.info(f"Collecting CryptoPanic news for currencies: {currencies}")

        all_items: list[SocialSentiment] = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.API_BASE,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"CryptoPanic API returned status {resp.status}")
                        return []
                    data = await resp.json()

            results = data.get("results", [])
            logger.info(f"Fetched {len(results)} items from CryptoPanic")

            for result in results:
                try:
                    title = result.get("title")
                    if not title:
                        continue

                    # Parse publication timestamp
                    published_at = None
                    pub_str = result.get("published_at")
                    if pub_str:
                        try:
                            published_at = datetime.fromisoformat(
                                pub_str.replace("Z", "+00:00")
                            )
                        except Exception:
                            pass

                    # Extract currencies
                    currency_list = [
                        c["code"] for c in result.get("currencies", []) if c.get("code")
                    ]

                    # Extract votes
                    votes = result.get("votes", {})
                    positive = votes.get("positive", 0) or 0
                    negative = votes.get("negative", 0) or 0
                    net_score = positive - negative
                    sentiment = self._derive_sentiment(votes)
                    comment_count = votes.get("comments", 0)

                    # Source outlet name as author
                    source = result.get("source", {})
                    author = source.get("title") if isinstance(source, dict) else None

                    data_point = SocialSentiment(
                        platform="cryptopanic",
                        content=title,
                        body=None,
                        author=author,
                        score=net_score,
                        sentiment=sentiment,
                        currencies=currency_list or None,
                        posted_at=published_at,
                        collected_at=datetime.now(timezone.utc),
                        comment_count=comment_count,
                        top_comments=votes,  # Store full votes dict as JSONB
                    )
                    all_items.append(data_point)

                except Exception as e:
                    logger.debug(f"Failed to parse CryptoPanic item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to collect CryptoPanic data: {e}")
            return []

        logger.info(f"Collected {len(all_items)} CryptoPanic items")
        return all_items


CollectorRegistry.register(CryptoPanicCollector)
