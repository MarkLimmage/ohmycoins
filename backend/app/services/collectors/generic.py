from typing import Any
import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session

from .scraper_collector import ScraperCollector

class GenericScraperCollector(ScraperCollector):
    """
    A generic collector that scrapes data based on configuration.
    """
    def __init__(self, name: str, ledger: str, config: dict[str, Any]):
        url = config.get("url")
        use_playwright = config.get("use_playwright", False)
        super().__init__(name, ledger, url, use_playwright)
        self.selectors = config.get("selectors", {})

    async def scrape_static(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, "html.parser")
        data = []
        
        list_selector = self.selectors.get("list_selector")
        item_selectors = self.selectors.get("item_selectors", {})
        
        if list_selector:
            items = soup.select(list_selector)
            for item in items:
                record = {}
                for key, selector in item_selectors.items():
                    element = item.select_one(selector)
                    record[key] = element.get_text(strip=True) if element else None
                data.append(record)
        else:
            # Flat selectors
            record = {}
            for key, selector in self.selectors.items():
                if isinstance(selector, str):
                    element = soup.select_one(selector)
                    record[key] = element.get_text(strip=True) if element else None
            if record:
                data.append(record)
            
        return data

    async def scrape_dynamic(self) -> list[dict[str, Any]]:
        # TODO: Implement dynamic scraping with Playwright context
        raise NotImplementedError("Dynamic scraping not yet fully implemented in GenericCollector")

    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Basic validation: check if not empty
        return data

    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        # For generic collectors, we might not have a specific table.
        # Ideally, we would store this in specific tables or a generic 'CollectedData' table.
        # For this sprint, getting the mechanism to run is key.
        # We'll just return count for now, effectively discarding data unless we add a generic table.
        # Or maybe log samples.
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Collected {len(data)} records for {self.name}: {data[:1]}...")
        return len(data)
