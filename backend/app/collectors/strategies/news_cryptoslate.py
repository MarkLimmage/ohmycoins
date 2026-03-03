import logging
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import NewsItem

logger = logging.getLogger(__name__)


class CryptoSlateCollector(ICollector):
    RSS_URL = "https://cryptoslate.com/feed/"
    SOURCE_NAME = "CryptoSlate"

    @property
    def name(self) -> str:
        return "news_cryptoslate"

    @property
    def description(self) -> str:
        return "Collects crypto news from CryptoSlate via RSS feed."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rss_url": {"type": "string", "default": self.RSS_URL},
                "max_items": {"type": "integer", "default": 20},
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("rss_url", self.RSS_URL)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "OhMyCoins/1.0"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        url = config.get("rss_url", self.RSS_URL)
        limit = config.get("max_items", 20)

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

        results: list[Any] = []
        for item in items[:limit]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            description = item.find("description")

            # Parse published date from RFC 2822 format
            published_at = None
            if pub_date:
                try:
                    published_at = parsedate_to_datetime(pub_date.get_text(strip=True))
                except Exception:
                    pass

            results.append(
                NewsItem(
                    title=title.get_text(strip=True) if title else "No Title",
                    link=link.get_text(strip=True) if link else "",
                    published_at=published_at,
                    summary=description.get_text(strip=True)[:500]
                    if description
                    else None,
                    source=self.SOURCE_NAME,
                )
            )

        return results


CollectorRegistry.register(CryptoSlateCollector)
