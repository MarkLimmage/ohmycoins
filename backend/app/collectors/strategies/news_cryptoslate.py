import logging
from datetime import datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry


class CryptoSlateCollector(ICollector):
    @property
    def name(self) -> str:
        return "news_cryptoslate"

    @property
    def description(self) -> str:
        return "Scrapes crypto news from CryptoSlate."

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "default": "https://cryptoslate.com/",
                    "title": "Base URL",
                },
                "max_items": {"type": "integer", "default": 10, "title": "Max Items"},
            },
            "required": ["base_url"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        return "base_url" in config

    async def test_connection(self, config: dict[str, Any]) -> bool:
        url = config.get("base_url", "https://cryptoslate.com/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        url = config.get("base_url", "https://cryptoslate.com/")
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
                links = []

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if isinstance(href, str) and href.startswith(
                        "https://cryptoslate.com/"
                    ):
                        # Exclude non-news
                        if not any(
                            x in href
                            for x in [
                                "/coins/",
                                "/people/",
                                "/companies/",
                                "/category/",
                                "/tag/",
                                "/feed/",
                            ]
                        ):
                            if href.count("-") > 2:  # Likely a slug
                                if href not in links:
                                    links.append(href)
                                    if len(links) >= limit:
                                        break

                for article_url in links:
                    try:
                        async with session.get(
                            article_url, headers=headers, timeout=10
                        ) as detail_res:
                            if detail_res.status != 200:
                                continue
                            detail_html = await detail_res.text()

                        detail_soup = BeautifulSoup(detail_html, "html.parser")

                        title_tag = detail_soup.find(
                            "h1", class_="post-title"
                        ) or detail_soup.find("h1")
                        title = (
                            title_tag.get_text(strip=True)
                            if title_tag
                            else "Unknown Title"
                        )

                        summary = ""
                        # CryptoSlate often puts summary in first p
                        content_div = detail_soup.find(
                            "div", class_="post3-content"
                        ) or detail_soup.find("div", class_="post-body")
                        if content_div:
                            p = content_div.find("p")
                            if p:
                                summary = p.get_text(strip=True)

                        # Published time often in meta
                        published = None
                        meta_date = detail_soup.find(
                            "meta", property="article:published_time"
                        )
                        if meta_date:
                            published = meta_date["content"]

                        results.append(
                            {
                                "title": title,
                                "link": article_url,
                                "published": published,
                                "summary": summary,
                                "source": "CryptoSlate",
                                "collected_at": datetime.utcnow().isoformat(),
                            }
                        )

                    except Exception as e:
                        logging.error(
                            f"Error scraping CryptoSlate article {article_url}: {e}"
                        )
                        continue

        except Exception as e:
            logging.error(f"Error collecting from CryptoSlate: {e}")

        return results


CollectorRegistry.register(CryptoSlateCollector)
