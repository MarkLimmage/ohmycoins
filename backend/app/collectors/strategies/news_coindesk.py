import logging
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.collectors.strategies.keyword_taxonomy import (
    aggregate_sentiment,
    extract_context,
    extract_currencies,
    match_keywords,
)
from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import NewsItem, NewsKeywordMatch

logger = logging.getLogger(__name__)


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
                async with session.get(
                    url,
                    headers={"User-Agent": "OhMyCoins/1.0"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        url = config.get("rss_url", "https://www.coindesk.com/arc/outboundfeeds/rss/")
        limit = config.get("max_items", 10)

        results: list[Any] = []
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"User-Agent": "OhMyCoins/1.0"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response.raise_for_status()
                content = await response.text()

        # Use BeautifulSoup with xml parser
        soup = BeautifulSoup(content, "xml")
        items = soup.find_all("item")

        for item in items[:limit]:
            title = item.title.text if item.title else "No Title"
            link = item.link.text if item.link else ""
            pub_date_text = item.pubDate.text if item.pubDate else ""
            description = item.description.text if item.description else ""

            # Parse published date from RFC 2822 format
            published_at = None
            if pub_date_text:
                try:
                    published_at = parsedate_to_datetime(pub_date_text)
                except Exception:
                    pass

            results.append(
                NewsItem(
                    title=title,
                    link=link,
                    published_at=published_at,
                    summary=description if description else None,
                    source="CoinDesk",
                )
            )

            # Keyword enrichment
            news_item = results[-1]
            search_text = f"{news_item.title} {news_item.summary or ''}"
            matches = match_keywords(search_text)
            if matches:
                currencies = extract_currencies(search_text)
                for kw in matches:
                    results.append(
                        NewsKeywordMatch(
                            news_item_link=news_item.link,
                            keyword=kw.keyword,
                            category=kw.category,
                            direction=kw.direction,
                            impact=kw.impact,
                            currencies=currencies,
                            match_context=extract_context(search_text, kw.keyword),
                            temporal_signal=kw.temporal_signal,
                            source_collector="news_coindesk",
                        )
                    )
                news_item.sentiment_score, news_item.sentiment_label = (
                    aggregate_sentiment(matches)
                )

        return results


# Auto-register at module import
CollectorRegistry.register(CoinDeskCollector)
