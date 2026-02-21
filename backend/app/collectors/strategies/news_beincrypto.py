import logging
from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry


class BeInCryptoCollector(ICollector):
    @property
    def name(self) -> str:
        return "news_beincrypto"

    @property
    def description(self) -> str:
        return "Scrapes crypto news from BeInCrypto."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "default": "https://beincrypto.com/news/",
                    "title": "Base URL",
                },
                "max_items": {"type": "integer", "default": 10, "title": "Max Items"},
            },
            "required": ["base_url"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "base_url" in config

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("base_url", "https://beincrypto.com/news/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        # This implementation is inspired by scraping generic BeInCrypto news HTML structure
        url = config.get("base_url", "https://beincrypto.com/news/")
        limit = config.get("max_items", 10)
        results = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                async with session.get(url, headers=headers, timeout=30) as response:
                    content = await response.text()

                soup = BeautifulSoup(content, "html.parser")

                # Look for article cards - structure changes often, generalize a bit
                articles = soup.find_all("article")
                if not articles:
                    # Check div based structure if article tags not used
                    articles = soup.find_all("div", class_="story")

                for article in articles[:limit]:
                    try:
                        link_tag = article.find("a", href=True)
                        if not link_tag:
                            continue

                        href = link_tag["href"]
                        if not isinstance(href, str):
                            continue
                        if not href.startswith("http"):
                            href = "https://beincrypto.com" + href

                        # Extract title
                        title_tag = (
                            article.find("h3")
                            or article.find("h2")
                            or article.find("h4")
                        )
                        title = (
                            title_tag.get_text(strip=True)
                            if title_tag
                            else "Unknown Title"
                        )

                        # Extract summary if available on listing
                        summary = ""
                        p_tag = article.find("p")
                        if p_tag:
                            summary = p_tag.get_text(strip=True)

                        # Extract time
                        time_tag = article.find("time")
                        published = (
                            time_tag["datetime"]
                            if time_tag and time_tag.has_attr("datetime")
                            else None
                        )

                        # If details missing, create from listing only to avoid heavy detail scraping for now
                        # but we can fetch detail if we want fuller content.
                        results.append(
                            {
                                "title": title,
                                "link": href,
                                "published": published,
                                "summary": summary,
                                "source": "BeInCrypto",
                                "collected_at": datetime.utcnow().isoformat(),
                            }
                        )

                    except Exception as e:
                        logging.error(f"Error parsing BeInCrypto article: {e}")
                        continue

        except Exception as e:
            logging.error(f"Error collecting from BeInCrypto: {e}")

        return results


CollectorRegistry.register(BeInCryptoCollector)
