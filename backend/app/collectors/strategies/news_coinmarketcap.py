import logging
from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry


class CoinMarketCapCollector(ICollector):
    @property
    def name(self) -> str:
        return "news_coinmarketcap"

    @property
    def description(self) -> str:
        return "Scrapes crypto headlines from CoinMarketCap."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "default": "https://coinmarketcap.com/headlines/news/",
                    "title": "Base URL",
                },
                "max_items": {"type": "integer", "default": 10, "title": "Max Items"},
            },
            "required": ["base_url"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "base_url" in config

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("base_url", "https://coinmarketcap.com/headlines/news/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        # This implementation attempts to grab from the news page
        url = config.get("base_url", "https://coinmarketcap.com/headlines/news/")
        limit = config.get("max_items", 10)
        results: list[dict[str, Any]] = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                async with session.get(url, headers=headers, timeout=30) as response:
                    # Note: CoinMarketCap is heavily dynamic (SPA/React).
                    # BeautifulSoup might not see all content if it loads via JS.
                    # We will try best effort for static SSR content, but often APIs are better choices here.
                    # For this "scraper" plugin we will just grab what we can from the static page.
                    html_content = await response.text()

                soup = BeautifulSoup(html_content, "html.parser")
                # Usually look for 'uikit-row' or similar article containers
                # This selector is a guess based on typical structures, might need adjustment
                articles = soup.find_all("div", class_=lambda x: x and "news-item" in x)

                if not articles:
                    # Fallback to finding links inside main container
                    main = soup.find("main")
                    if main:
                        articles = main.find_all("a", href=True)

                count = 0
                for item in articles:
                    if count >= limit:
                        break
                    try:
                        href = item.get("href", "")
                        if not href or not isinstance(href, str):
                            continue

                        if "/headlines/news/" in href:
                            title = item.get_text(strip=True)
                            if not title:
                                continue  # Skip empty links

                            if not href.startswith("http"):
                                href = "https://coinmarketcap.com" + href

                            # dedup
                            if any(r["link"] == href for r in results):
                                continue

                            results.append(
                                {
                                    "title": title,
                                    "link": href,
                                    "source": "CoinMarketCap",
                                    "collected_at": datetime.utcnow().isoformat(),
                                }
                            )
                            count += 1

                    except Exception as e:
                        logging.error(f"Error parsing item: {e}")
                        continue

        except Exception as e:
            logging.error(f"Error collecting from CoinMarketCap: {e}")

        return results


CollectorRegistry.register(CoinMarketCapCollector)
