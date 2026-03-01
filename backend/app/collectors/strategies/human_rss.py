import logging
from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import NewsItem

logger = logging.getLogger(__name__)


class HumanRSSCollector(ICollector):
    @property
    def name(self) -> str:
        return "HumanRSSCollector"

    @property
    def description(self) -> str:
        return "Ingests news headlines from RSS feeds (e.g., CoinDesk, Cointelegraph)."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feed_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [
                        "https://www.coindesk.com/arc/outboundfeeds/rss/",
                        "https://cointelegraph.com/rss",
                    ],
                },
                "mock_mode": {"type": "boolean", "default": False},
            },
            "required": ["feed_urls"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "feed_urls" not in config or not isinstance(config["feed_urls"], list):
            return False
        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        if config.get("mock_mode", False):
            return True

        # Simple test: try to fetch the first feed
        feed_urls = config.get("feed_urls", [])
        if not feed_urls:
            return False

        try:
            url = feed_urls[0]
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "OhMyCoins/1.0"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return False
                    text = await resp.text()
                    soup = BeautifulSoup(text, "xml")
                    items = soup.find_all("item")
                    return len(items) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        results = []
        if config.get("mock_mode", False):
            # Mock data
            results.append(
                NewsItem(
                    title="Bitcoin hits $100k (Mock)",
                    link="https://example.com/btc-100k",
                    published_at=datetime.now(),
                    summary="Bitcoin has finally reached the moon.",
                    source="MockSource",
                    collected_at=datetime.now(),
                )
            )
            results.append(
                NewsItem(
                    title="Ethereum gas fees drop (Mock)",
                    link="https://example.com/eth-gas",
                    published_at=datetime.now(),
                    summary="Gas is cheap now.",
                    source="MockSource",
                    collected_at=datetime.now(),
                )
            )
            return results

        feed_urls = config.get("feed_urls", [])

        for url in feed_urls:
            try:
                logger.info(f"Fetching RSS feed: {url}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        headers={"User-Agent": "OhMyCoins/1.0"},
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        resp.raise_for_status()
                        text = await resp.text()

                soup = BeautifulSoup(text, "xml")
                items = soup.find_all("item")

                if not items:
                    logger.warning(f"No items found for {url}")
                    continue

                source_name = "Unknown"
                if "coindesk" in url:
                    source_name = "CoinDesk"
                elif "cointelegraph" in url:
                    source_name = "Cointelegraph"

                for item in items[:10]:  # Limit to 10 most recent
                    title_tag = item.find("title")
                    link_tag = item.find("link")
                    pub_date_tag = item.find("pubDate")
                    description_tag = item.find("description")

                    title = title_tag.get_text(strip=True) if title_tag else "No Title"
                    link = link_tag.get_text(strip=True) if link_tag else ""
                    pub_date_str = (
                        pub_date_tag.get_text(strip=True) if pub_date_tag else None
                    )
                    summary = (
                        description_tag.get_text(strip=True)
                        if description_tag
                        else None
                    )

                    # Parse published date (simple handling)
                    published_at = None
                    if pub_date_str:
                        try:
                            # Try to parse RFC 2822 format
                            from email.utils import parsedate_to_datetime

                            published_at = parsedate_to_datetime(pub_date_str)
                        except Exception:
                            published_at = None

                    # Create NewsItem
                    item_obj = NewsItem(
                        title=title,
                        link=link,
                        published_at=published_at,
                        summary=summary,
                        source=source_name,
                        collected_at=datetime.now(),
                    )
                    results.append(item_obj)

            except Exception as e:
                logger.error(f"Error fetching feed {url}: {e}")

        return results


# Register strategy
CollectorRegistry.register(HumanRSSCollector)
