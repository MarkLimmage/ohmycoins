import logging
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry


class CryptoPanicCollector(ICollector):
    @property
    def name(self) -> str:
        return "news_cryptopanic"

    @property
    def description(self) -> str:
        return "Aggregated crypto news from CryptoPanic."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "default": "https://cryptopanic.com/news/",
                    "title": "Base URL",
                },
                "max_items": {"type": "integer", "default": 10, "title": "Max Items"},
            },
            "required": ["base_url"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "base_url" in config

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("base_url", "https://cryptopanic.com/news/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        url = config.get("base_url", "https://cryptopanic.com/news/")
        limit = config.get("max_items", 10)
        results = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }

                async with session.get(url, headers=headers, timeout=30) as response:
                    content = await response.text()

                soup = BeautifulSoup(content, "html.parser")
                news_items = soup.find_all("div", class_="news-row")

                for item in news_items[:limit]:
                    try:
                        title_tag = item.find("span", class_="title-text")
                        if not title_tag:
                            continue

                        title = title_tag.get_text(strip=True)

                        # Link is usually buried in an anchor
                        link_tag = item.find("a", class_="news-cell-main")
                        # CryptoPanic often redirects, so the link might be internal /news/123/click/
                        # For now we'll take what we can get.
                        link = ""
                        if link_tag and link_tag.has_attr("href"):
                            href_val = link_tag["href"]
                            if isinstance(href_val, str):
                                link = urljoin("https://cryptopanic.com", href_val)

                        # Source description
                        source_tag = item.find("span", class_="si-source-name")
                        source_domain = (
                            source_tag.get_text(strip=True)
                            if source_tag
                            else "CryptoPanic"
                        )

                        # Time
                        time_tag = item.find("time")
                        published = (
                            time_tag["datetime"]
                            if time_tag and time_tag.has_attr("datetime")
                            else None
                        )

                        results.append(
                            {
                                "title": title,
                                "link": link,
                                "published": published,
                                "summary": f"Source: {source_domain}",
                                "source": "CryptoPanic",
                                "collected_at": datetime.utcnow().isoformat(),
                            }
                        )

                    except Exception as e:
                        logging.error(f"Error parsing item in CryptoPanic: {e}")
                        continue

        except Exception as e:
            logging.error(f"Error collecting from CryptoPanic: {e}")

        return results


CollectorRegistry.register(CryptoPanicCollector)
