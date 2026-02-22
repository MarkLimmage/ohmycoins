"""
Simulated Calendar Collector for Catalyst Ledger.

This collector generates realistic market events for development and testing purposes when:
1. Real API access is restricted/paid (e.g., CoinMarketCal, Coindar)
2. Scraping is blocked by Cloudflare (e.g., ForexFactory)
3. Deterministic data is needed for UI development

It simulates:
- Economic Events (CPI, FOMC, Unemployment)
- Crypto Events (Network Upgrades, Halvings)
- Exchange Events (Listings, Maintenance)
"""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session

from app.models import CatalystEvents
from app.services.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class SimulatedCalendarCollector(BaseCollector):
    """
    Simulated event collector for Catalyst Ledger.
    Generates realistic market events for testing and development.
    """

    def __init__(self):
        """Initialize the simulated calendar collector."""
        super().__init__(
            name="simulated_calendar",
            ledger="catalyst",
        )
        self.event_templates = [
            {
                "type": "economic",
                "title": "US CPI Data Release",
                "description": "Consumer Price Index (YoY) data to be released. Forecast: {value}%.",
                "impact": 9,
                "currencies": ["USD", "BTC", "ETH"],
            },
            {
                "type": "economic",
                "title": "FOMC Interest Rate Decision",
                "description": "Federal Reserve unexpected rate decision. New target: {value}%.",
                "impact": 10,
                "currencies": ["USD", "BTC"],
            },
            {
                "type": "upgrade",
                "title": "{coin} Network Upgrade",
                "description": "Major protocol upgrade scheduled for block {value}.",
                "impact": 8,
                "currencies": ["{coin}"],
            },
            {
                "type": "listing",
                "title": "New Listing: {coin}",
                "description": "{coin} will be listed on major exchange.",
                "impact": 7,
                "currencies": ["{coin}"],
            },
            {
                "type": "governance",
                "title": "{coin} Governance Proposal",
                "description": "Proposal #{value} to adjust staking rewards.",
                "impact": 5,
                "currencies": ["{coin}"],
            },
        ]
        self.coins = ["BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "UNI"]

    async def collect(self) -> list[dict[str, Any]]:
        """
        Generate simulated events.

        Returns:
            List of simulated event dictionaries
        """
        logger.info(f"{self.name}: Generating simulated events...")
        
        events = []
        now = datetime.now(timezone.utc)
        
        # Generate 3-5 random events
        num_events = random.randint(3, 5)
        
        for _ in range(num_events):
            template = random.choice(self.event_templates)
            coin = random.choice(self.coins)
            value = random.randint(1000, 9999) if "block" in template["description"] else random.randint(1, 100)
            
            # Format strings
            title = template["title"].format(coin=coin, value=value)
            description = template["description"].format(coin=coin, value=value)
            currencies = [c.format(coin=coin) for c in template["currencies"]]
            
            # Determine detection time (recent past)
            detected_at = now - timedelta(minutes=random.randint(5, 120))
            
            event = {
                "event_type": template["type"],
                "title": title,
                "description": description,
                "source": "Simulated Calendar",
                "currencies": currencies,
                "impact_score": template["impact"],
                "detected_at": detected_at,
                "url": "https://example.com/calendar/event",
                "collected_at": now,
            }
            events.append(event)
            
        logger.info(f"{self.name}: Generated {len(events)} events")
        return events

    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate simulated data.
        """
        valid_data = []
        for item in data:
            if not item.get("title") or not item.get("event_type"):
                continue
            valid_data.append(item)
        return valid_data

    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store events in the database.
        """
        new_records = 0
        
        for item in data:
            # Check for existing event (deduplication based on title and date)
            # In a real collector, we'd use a unique ID from the source
            # Here we just check title + approximate time
            
            # Simplified deduplication for simulation
            # (In reality, simulation generates new events every run, so we might fill up DB)
            # But for "collection" logic, we just insert.
            
            event = CatalystEvents(**item)
            session.add(event)
            new_records += 1
            
        return new_records
