import logging
from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry


class NewsBTCCollector(ICollector):
    @property
    def name(self) -> str:
        return "news_newsbtc"

    @property
    def description(self) -> str:
        return "Scrapes crypto news from NewsBTC."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "default": "https://www.newsbtc.com/news/",
                    "title": "Base URL",
                },
                "max_items": {"type": "integer", "default": 10, "title": "Max Items"},
            },
            "required": ["base_url"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "base_url" in config

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("base_url", "https://www.newsbtc.com/news/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        url = config.get("base_url", "https://www.newsbtc.com/news/")
        limit = config.get("max_items", 10)
        results = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                async with session.get(url, headers=headers, timeout=30) as response:
                    html_content = await response.text()

                soup = BeautifulSoup(html_content, "html.parser")
                article_list = soup.find("div", class_="td-ss-main-content")

                if article_list:
                    articles = article_list.find_all("div", class_="td-block-span6")
                    for article in articles[:limit]:
                        try:
                            item = article.find("div", class_="td-module-thumb")
                            if not item:
                                continue

                            a_tag = item.find("a")
                            if not a_tag:
                                continue

                            href_val = a_tag.get("href", "")
                            title_val = a_tag.get("title", "")

                            if not isinstance(href_val, str) or not isinstance(
                                title_val, str
                            ):
                                continue

                            href = href_val
                            title = title_val

                            img = item.find("img")
                            image_url = (
                                img["data-src"]
                                if img and img.has_attr("data-src")
                                else None
                            )

                            summary = ""
                            excerpt = article.find("div", class_="td-excerpt")
                            if excerpt:
                                summary = excerpt.get_text(strip=True)

                            date_tag = article.find("time")
                            published = date_tag["datetime"] if date_tag else None

                            results.append(
                                {
                                    "title": title,
                                    "link": href,
                                    "published": published,
                                    "summary": summary,
                                    "source": "NewsBTC",
                                    "image_url": image_url,
                                    "collected_at": datetime.utcnow().isoformat(),
                                }
                            )
                        except Exception as e:
                            logging.error(f"Error parsing NewsBTC article: {e}")
                            continue

        except Exception as e:
            logging.error(f"Error collecting from NewsBTC: {e}")

        return results


CollectorRegistry.register(NewsBTCCollector)
