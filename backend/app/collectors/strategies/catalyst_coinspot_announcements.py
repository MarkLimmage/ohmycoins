"""
CoinSpot announcements collector plugin for exchange events (Catalyst Ledger).

This collector scrapes CoinSpot's announcements/news page to detect:
- New token listings (the "CoinSpot Effect")
- Exchange maintenance announcements
- Trading updates
- Platform changes
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import CatalystEvents

logger = logging.getLogger(__name__)


class CatalystCoinSpotAnnouncements(ICollector):
    """Collector for CoinSpot exchange announcements and events."""

    # Event type mapping with impact scores
    EVENT_TYPES = {
        "listing": {
            "keywords": ["new", "listing", "added", "launch", "available", "list"],
            "impact": 9,
            "event_type": "exchange_listing",
        },
        "maintenance": {
            "keywords": ["maintenance", "downtime", "scheduled", "upgrade"],
            "impact": 4,
            "event_type": "exchange_maintenance",
        },
        "trading": {
            "keywords": ["trading", "market", "pair", "delisting", "halt"],
            "impact": 6,
            "event_type": "exchange_trading",
        },
        "feature": {
            "keywords": ["feature", "update", "improvement", "new feature"],
            "impact": 3,
            "event_type": "exchange_feature",
        },
    }

    @property
    def name(self) -> str:
        return "catalyst_coinspot_announcements"

    @property
    def description(self) -> str:
        return "CoinSpot exchange announcements and events"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "CoinSpot announcements page URL",
                    "default": "https://coinspot.zendesk.com/hc/en-us/categories/115000579994-Announcements",
                },
                "max_articles": {
                    "type": "integer",
                    "description": "Maximum articles to fetch",
                    "default": 50,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "url" in config:
            if not isinstance(config["url"], str):
                logger.error("Invalid config: 'url' must be a string")
                return False

        if "max_articles" in config:
            try:
                int(config["max_articles"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'max_articles' must be an integer")
                return False

        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to CoinSpot announcements page."""
        url = config.get(
            "url",
            "https://coinspot.zendesk.com/hc/en-us/categories/115000579994-Announcements",
        )

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test CoinSpot connection: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect CoinSpot announcements."""
        url = config.get(
            "url",
            "https://coinspot.zendesk.com/hc/en-us/categories/115000579994-Announcements",
        )
        max_articles = config.get("max_articles", 50)

        logger.info("Scraping CoinSpot announcements")

        announcements = []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }

                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to fetch page: status {resp.status}")
                        return []

                    content = await resp.text()

            # Parse HTML
            soup = BeautifulSoup(content, "html.parser")

            # Find article list items (Zendesk structure)
            article_items = soup.find_all("li", class_="article-list-item")

            if not article_items:
                # Fallback: try alternate selectors
                article_items = soup.find_all("a", class_="article-list-link")

            logger.info(f"Found {len(article_items)} announcements")

            for item in article_items[:max_articles]:
                try:
                    # Extract title
                    title_elem = item.find("h2") or item.find("span", class_="title")
                    if not title_elem:
                        title_elem = item
                    title = title_elem.get_text(strip=True)

                    if not title:
                        continue

                    # Extract URL
                    link_elem = item.find("a")
                    url_extracted: str | None = None
                    if link_elem and link_elem.has_attr("href"):
                        href = str(link_elem["href"])
                        if not href.startswith("http"):
                            url_extracted = f"https://coinspot.zendesk.com{href}"
                        else:
                            url_extracted = href

                    # Classify event type
                    event_type, impact_score = self._classify_event(title)

                    # Extract cryptocurrencies from title
                    currencies = self._extract_currencies(title)

                    # Create CatalystEvents instance
                    data_point = CatalystEvents(
                        event_type=event_type,
                        title=title,
                        description=None,
                        source="CoinSpot",
                        currencies=currencies if currencies else None,
                        impact_score=impact_score,
                        detected_at=datetime.now(timezone.utc),
                        url=url_extracted,
                        collected_at=datetime.now(timezone.utc),
                    )

                    announcements.append(data_point)
                    logger.debug(f"Collected announcement: {title}")

                except Exception as e:
                    logger.debug(f"Failed to parse announcement: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to scrape CoinSpot announcements: {e}")
            return []

        logger.info(f"Collected {len(announcements)} announcements")
        return announcements

    def _classify_event(self, title: str) -> tuple[str, int]:
        """Classify event type and return impact score."""
        title_lower = title.lower()

        for _event_key, event_info in self.EVENT_TYPES.items():
            keywords: list[str] = event_info["keywords"]  # type: ignore
            for keyword in keywords:
                if keyword in title_lower:
                    event_type: str = event_info["event_type"]  # type: ignore
                    impact: int = event_info["impact"]  # type: ignore
                    return (event_type, impact)

        # Default to feature
        return ("exchange_feature", 3)

    def _extract_currencies(self, text: str) -> list[str]:
        """Extract cryptocurrency symbols from text."""
        # Common crypto symbols and full names
        patterns = [
            (r"\bBTC\b", "BTC"),
            (r"\bETH\b", "ETH"),
            (r"\bBitcoin\b", "BTC"),
            (r"\bEthereum\b", "ETH"),
            (r"\bADA\b", "ADA"),
            (r"\bDOGE\b", "DOGE"),
            (r"\bXRP\b", "XRP"),
            (r"\bSOL\b", "SOL"),
            (r"\bAVAX\b", "AVAX"),
            (r"\bPOLYGON\b", "POLYGON"),
            (r"\bARB\b", "ARB"),
            (r"\bOP\b", "OP"),
            (r"\bLINK\b", "LINK"),
            (r"\bUNI\b", "UNI"),
            (r"\bAAVE\b", "AAVE"),
            (r"\bCRV\b", "CRV"),
            (r"\bUSDC\b", "USDC"),
            (r"\bUSDT\b", "USDT"),
            (r"\bDAI\b", "DAI"),
        ]

        found_cryptos = []
        for pattern, symbol in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_cryptos.append(symbol)

        return list(set(found_cryptos))  # Remove duplicates


CollectorRegistry.register(CatalystCoinSpotAnnouncements)
