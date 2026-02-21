from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry


class CoinDeskCollector(ICollector):
    @property
    def name(self) -> str:
        return "news_coindesk"

    @property
    def description(self) -> str:
        return "Collects latest crypto news from CoinDesk RSS feed."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "rss_url": {
                    "type": "string",
                    "default": "https://www.coindesk.com/arc/outboundfeeds/rss/",
                    "title": "RSS Feed URL",
                },
                "max_items": {
                    "type": "integer",
                    "default": 10,
                    "title": "Max Items per Run",
                },
            },
            "required": ["rss_url"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "rss_url" in config and isinstance(config["rss_url"], str)

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("rss_url", "https://www.coindesk.com/arc/outboundfeeds/rss/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        url = config.get("rss_url", "https://www.coindesk.com/arc/outboundfeeds/rss/")
        limit = config.get("max_items", 10)

        results = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    content = await response.text()

            # Use BeautifulSoup with xml parser
            soup = BeautifulSoup(content, "xml")
            items = soup.find_all("item")

            for item in items[:limit]:
                title = item.title.text if item.title else "No Title"
                link = item.link.text if item.link else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                description = item.description.text if item.description else ""

                results.append(
                    {
                        "title": title,
                        "link": link,
                        "published": pub_date,
                        "summary": description,
                        "source": "CoinDesk",
                        "collected_at": datetime.utcnow().isoformat(),
                    }
                )

        except Exception as e:
            # In a real plugin we might log this error properly
            # print(f"Error collecting from CoinDesk: {e}")
            pass

        return results


# Auto-register at module import
CollectorRegistry.register(CoinDeskCollector)
