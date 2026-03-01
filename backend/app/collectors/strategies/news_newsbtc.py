import logging
from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry

logger = logging.getLogger(__name__)


class NewsBTCCollector(ICollector):
    RSS_URL = "https://www.newsbtc.com/feed/"
    SOURCE_NAME = "NewsBTC"

    @property
    def name(self) -> str:
        return "news_newsbtc"

    @property
    def description(self) -> str:
        return "Collects crypto news from NewsBTC via RSS feed."

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

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
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

        results: list[dict[str, Any]] = []
        for item in items[:limit]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            description = item.find("description")
            creator = item.find("dc:creator")

            results.append(
                {
                    "title": title.get_text(strip=True) if title else "No Title",
                    "link": link.get_text(strip=True) if link else "",
                    "published": pub_date.get_text(strip=True) if pub_date else "",
                    "summary": description.get_text(strip=True)[:500]
                    if description
                    else "",
                    "source": self.SOURCE_NAME,
                    "author": creator.get_text(strip=True) if creator else None,
                    "collected_at": datetime.utcnow().isoformat(),
                }
            )

        return results


CollectorRegistry.register(NewsBTCCollector)
