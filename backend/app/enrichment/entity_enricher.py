"""Entity extraction enricher using regex-based POLE extraction."""

from __future__ import annotations

from typing import Any

from app.enrichment.base import EnrichmentResult, IEnricher
from app.models import NewsItem


class EntityEnricher(IEnricher):
    """Extracts POLE entities (Person, Organization, Location, Event) from news items."""

    # Known crypto organizations
    ORGANIZATIONS = {
        "SEC",
        "CFTC",
        "Fed",
        "Federal Reserve",
        "ECB",
        "European Central Bank",
        "BlackRock",
        "Grayscale",
        "Coinbase",
        "Binance",
        "Kraken",
        "Gemini",
        "Huobi",
        "OKEx",
        "FTX",
        "Celsius",
        "Genesis",
        "BlockFi",
        "JPMorgan",
        "Goldman Sachs",
        "Morgan Stanley",
        "Bank of America",
        "Wells Fargo",
    }

    # Known crypto figures/people
    PEOPLE = {
        "Satoshi Nakamoto",
        "Vitalik Buterin",
        "Changpeng Zhao",
        "Do Kwon",
        "Sam Bankman-Fried",
        "SBF",
        "Michael Saylor",
        "Tim Draper",
        "Tyler Winklevoss",
        "Cameron Winklevoss",
        "Elon Musk",
        "Mark Zuckerberg",
        "Janet Yellen",
        "Gary Gensler",
        "Jerome Powell",
        "Christine Lagarde",
    }

    # Known crypto events
    EVENTS = {
        "halving",
        "fork",
        "merger",
        "upgrade",
        "listing",
        "delisting",
        "hack",
        "breach",
        "exploit",
        "crash",
        "bull run",
        "bear market",
        "IPO",
        "bankruptcy",
        "bailout",
        "regulation",
        "sanctions",
        "probe",
        "investigation",
        "lawsuit",
        "settlement",
        "acquisition",
    }

    # Known locations/jurisdictions
    LOCATIONS = {
        "United States",
        "USA",
        "US",
        "Europe",
        "European Union",
        "EU",
        "China",
        "Hong Kong",
        "Singapore",
        "Japan",
        "South Korea",
        "UK",
        "London",
        "New York",
        "San Francisco",
        "Tokyo",
        "Dubai",
        "Switzerland",
        "Cayman Islands",
        "Malta",
    }

    @property
    def name(self) -> str:
        """Unique identifier for this enricher."""
        return "entity_extraction"

    def can_enrich(self, item: object) -> bool:
        """Check if item can be enriched (must be NewsItem with title)."""
        return isinstance(item, NewsItem) and bool(item.title)

    async def enrich(self, item: object) -> list[EnrichmentResult]:
        """
        Extract POLE entities from a news item using regex patterns.

        Returns one EnrichmentResult with all detected entities.
        """
        results: list[EnrichmentResult] = []

        if not isinstance(item, NewsItem):
            return results

        # Build search text from title and summary
        search_text = f"{item.title} {item.summary or ''}"

        # Extract entities
        organizations = self._extract_organizations(search_text)
        people = self._extract_people(search_text)
        events = self._extract_events(search_text)
        locations = self._extract_locations(search_text)

        # Only create a result if we found any entities
        if organizations or people or events or locations:
            result = EnrichmentResult(
                enricher_name="entity_extraction",
                enrichment_type="entity",
                data={
                    "entities": {
                        "organizations": list(organizations),
                        "people": list(people),
                        "events": list(events),
                        "locations": list(locations),
                    },
                    "relationships": self._infer_relationships(
                        organizations, people, events
                    ),
                },
                currencies=[],
                confidence=0.7,  # Regex-based confidence
            )
            results.append(result)

        return results

    def _extract_organizations(self, text: str) -> set[str]:
        """Extract known crypto organizations from text."""
        found = set()
        text_lower = text.lower()

        for org in self.ORGANIZATIONS:
            if org.lower() in text_lower:
                found.add(org)

        return found

    def _extract_people(self, text: str) -> set[str]:
        """Extract known crypto figures from text."""
        found = set()
        text_lower = text.lower()

        for person in self.PEOPLE:
            if person.lower() in text_lower:
                found.add(person)

        return found

    def _extract_events(self, text: str) -> set[str]:
        """Extract known crypto events from text."""
        found = set()
        text_lower = text.lower()

        for event in self.EVENTS:
            if event.lower() in text_lower:
                found.add(event)

        return found

    def _extract_locations(self, text: str) -> set[str]:
        """Extract known locations from text."""
        found = set()
        text_lower = text.lower()

        for location in self.LOCATIONS:
            if location.lower() in text_lower:
                found.add(location)

        return found

    def _infer_relationships(
        self, organizations: set[str], people: set[str], events: set[str]
    ) -> list[dict[str, Any]]:
        """Infer simple relationships between entities."""
        relationships = []

        # Example: if person and organization are both mentioned in same text,
        # they might be related
        if organizations and people:
            relationships.append(
                {
                    "type": "potential_association",
                    "entities": list(organizations) + list(people),
                    "confidence": 0.5,
                }
            )

        if organizations and events:
            relationships.append(
                {
                    "type": "potential_event_involvement",
                    "entities": list(organizations) + list(events),
                    "confidence": 0.6,
                }
            )

        return relationships
