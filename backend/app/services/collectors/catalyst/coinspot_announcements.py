# mypy: ignore-errors
"""
CoinSpot announcements scraper for exchange events (Catalyst Ledger).

This collector scrapes CoinSpot's announcements/news page to detect:
- New token listings (the "CoinSpot Effect")
- Exchange maintenance announcements
- Trading updates
- Platform changes

Data Source: https://coinspot.zendesk.com/hc/en-us/categories/115000579994-Announcements
Collection Frequency: Every hour (check for new announcements)
Cost: Free (scraping public website)
"""

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any

from playwright.async_api import async_playwright
from sqlmodel import Session, select

from app.models import CatalystEvents
from app.services.collectors.scraper_collector import ScraperCollector

logger = logging.getLogger(__name__)


class CoinSpotAnnouncementsCollector(ScraperCollector):
    """
    Collector for CoinSpot exchange announcements and events.
    
    Collects:
    - New token listings
    - Exchange maintenance notices
    - Trading updates
    - Platform feature announcements
    
    Impact: Token listings on CoinSpot can cause significant price movements
    (the "CoinSpot Effect" for Australian traders)
    """
    
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
    
    def __init__(self):
        """Initialize the CoinSpot announcements collector."""
        # Using the Zendesk help center announcements section as it's more structured
        super().__init__(
            name="coinspot_announcements",
            ledger="catalyst",
            url="https://coinspot.zendesk.com/hc/en-us/categories/115000579994-Announcements",
            use_playwright=True,  # Using Playwright for robust handling
        )
        
        self.timeout = 30
    
    async def scrape_static(self) -> list[dict[str, Any]]:
        """
        Scrape announcements from CoinSpot website using static HTML parsing.
        Required by abstract base class but we use Playwright.
        """
        # Fallback to dynamic if called directly
        return await self.scrape_dynamic()
            
    async def scrape_dynamic(self) -> list[dict[str, Any]]:
        """
        Scrape data from CoinSpot announcements using Playwright.
        
        Returns:
            List of dictionaries containing the scraped data
        
        Raises:
            Exception: If scraping fails
        """
        logger.info(f"{self.name}: Scraping CoinSpot announcements using Playwright")
        
        announcements = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Set a real user agent to avoid being blocked
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                
                # Navigate to the page
                logger.debug(f"{self.name}: Navigating to {self.url}")
                await page.goto(self.url, timeout=self.timeout * 1000)
                
                # Wait for content to load
                try:
                    await page.wait_for_selector("li.article-list-item", timeout=10000)
                except Exception:
                    logger.warning(f"{self.name}: Timeout waiting for article list items")
                    # Try to capture page content anyway
                
                # Extract articles
                articles = await page.query_selector_all("li.article-list-item")
                logger.debug(f"{self.name}: Found {len(articles)} articles")
                
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                for article in articles:
                    try:
                        # Extract title and link
                        link_element = await article.query_selector("a.article-list-link")
                        if not link_element:
                            continue
                            
                        title = await link_element.inner_text()
                        href = await link_element.get_attribute("href")
                        
                        if not title or not href:
                            continue
                            
                        # Complete the URL
                        if href.startswith("/"):
                            url = f"https://coinspot.zendesk.com{href}"
                        else:
                            url = href
                            
                        # Classify event
                        event_info = self._classify_announcement(title, "")
                        
                        # Extract currencies
                        currencies = self._extract_currencies(title, "")
                        
                        # For date, we might need to visit the article or infer from position
                        # For now, let's assume recent since it's on the front page
                        detected_at = datetime.now(timezone.utc)
                        
                        announcement_data = {
                            "event_type": event_info["event_type"],
                            "title": f"CoinSpot: {title}",
                            "description": title,  # Use title as description for list items
                            "source": "CoinSpot",
                            "currencies": currencies if currencies else None,
                            "impact_score": event_info["impact"],
                            "detected_at": detected_at,
                            "url": url,
                            "collected_at": datetime.now(timezone.utc),
                        }
                        
                        announcements.append(announcement_data)
                        logger.debug(
                            f"{self.name}: Found announcement: {title[:50]}..."
                        )
                        
                    except Exception as e:
                        logger.error(f"{self.name}: Error parsing article: {str(e)}")
                        continue
                
                await browser.close()
                
            logger.info(
                f"{self.name}: Scraped {len(announcements)} announcements"
            )
            return announcements
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to scrape announcements: {str(e)}")
            # Don't re-raise, return empty list so other collectors can continue
            return []

    def _classify_announcement(self, title: str, description: str) -> dict[str, Any]:
        """
        Classify announcement type based on content.
        
        Args:
            title: Announcement title
            description: Announcement description
        
        Returns:
            Dictionary with event_type and impact score
        """
        content = f"{title} {description}".lower()
        
        # Check against each event type's keywords
        for event_type, info in self.EVENT_TYPES.items():
            for keyword in info["keywords"]:
                if keyword in content:
                    return {
                        "event_type": info["event_type"],
                        "impact": info["impact"],
                    }
        
        # Default to general announcement
        return {
            "event_type": "exchange_announcement",
            "impact": 5,
        }
    
    def _extract_currencies(self, title: str, description: str) -> list[str]:
        """
        Extract mentioned cryptocurrency symbols from text.
        
        Args:
            title: Announcement title
            description: Announcement description
        
        Returns:
            List of currency symbols
        """
        content = f"{title} {description}".upper()
        currencies = []
        
        # Common cryptocurrency symbols
        # In production, this should come from a comprehensive DB or config
        common_cryptos = [
            "BTC", "ETH", "XRP", "ADA", "DOT", "SOL", "DOGE", "SHIB",
            "MATIC", "UNI", "LINK", "AVAX", "LTC", "BCH", "ATOM",
            "ALGO", "VET", "FTM", "MANA", "SAND", "AXS", "CRO",
            "PEPE", "BONK", "WIF", "SUI", "SEI", "TIA", "PYTH"
        ]
        
        for crypto in common_cryptos:
            # Look for the symbol as a whole word
            if re.search(rf"\b{crypto}\b", content):
                currencies.append(crypto)
                
        # Also look for patterns like "Listing (SYM)"
        matches = re.findall(r'\(([A-Z]{2,6})\)', content)
        for match in matches:
            if match not in currencies and match not in ["NEW", "UPDATE"]:
                currencies.append(match)
        
        return currencies
    
    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected announcement data.
        
        Args:
            data: Raw data scraped from CoinSpot
        
        Returns:
            Validated data ready for storage
        """
        validated = []
        
        for item in data:
            try:
                # Validate required fields
                if not item.get("title"):
                    logger.warning(f"{self.name}: Missing title, skipping")
                    continue
                
                if not item.get("event_type"):
                    logger.warning(f"{self.name}: Missing event_type, skipping")
                    continue
                
                # Validate impact score
                impact_score = item.get("impact_score")
                if impact_score is not None:
                    if not isinstance(impact_score, int) or impact_score < 1 or impact_score > 10:
                        logger.warning(
                            f"{self.name}: Invalid impact score {impact_score}, setting to 5"
                        )
                        item["impact_score"] = 5
                
                validated.append(item)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid announcement data: {str(e)}")
                continue
        
        logger.info(f"{self.name}: Validated {len(validated)}/{len(data)} records")
        return validated
    
    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated announcements in the database.
        
        Args:
            data: Validated data to store
            session: Database session
        
        Returns:
            Number of records stored
        """
        stored_count = 0
        
        for item in data:
            try:
                # Check for duplicates based on URL
                url = item.get("url")
                if url:
                    statement = select(CatalystEvents).where(CatalystEvents.url == url)
                    existing = session.exec(statement).first()
                    if existing:
                        logger.debug(f"{self.name}: Skipping duplicate announcement {url}")
                        continue

                catalyst_event = CatalystEvents(
                    event_type=item["event_type"],
                    title=item["title"],
                    description=item.get("description"),
                    source=item.get("source"),
                    currencies=item.get("currencies"),
                    impact_score=item.get("impact_score"),
                    detected_at=item.get("detected_at"),
                    url=item.get("url"),
                    collected_at=item["collected_at"],
                )
                
                session.add(catalyst_event)
                stored_count += 1
                
            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to store announcement "
                    f"'{item.get('title', 'unknown')[:50]}...': {str(e)}"
                )
                # Continue with other records
                continue
        
        # Commit all records at once
        try:
            session.commit()
            logger.info(f"{self.name}: Stored {stored_count} announcement records")
        except Exception as e:
            logger.error(f"{self.name}: Failed to commit records: {str(e)}")
            session.rollback()
            stored_count = 0
        
        return stored_count
