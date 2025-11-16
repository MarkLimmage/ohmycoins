"""
Scraper collector base class for web scraping-based data sources.

This module provides a base class for collectors that scrape data from websites,
with support for both static (BeautifulSoup) and dynamic (Playwright) scraping.
"""

import logging
from abc import abstractmethod
from typing import Any

from .base import BaseCollector

logger = logging.getLogger(__name__)


class ScraperCollector(BaseCollector):
    """
    Base class for web scraping-based collectors.
    
    Provides:
    - Abstract interface for scraping operations
    - Common scraping utilities
    - Error handling for scraping failures
    
    Subclasses should implement either:
    - scrape_static() for static HTML scraping (BeautifulSoup)
    - scrape_dynamic() for dynamic content scraping (Playwright)
    """
    
    def __init__(
        self,
        name: str,
        ledger: str,
        url: str,
        use_playwright: bool = False,
    ):
        """
        Initialize the scraper collector.
        
        Args:
            name: Unique name for this collector
            ledger: The ledger this collector belongs to
            url: URL to scrape
            use_playwright: Whether to use Playwright for dynamic content (default: False)
        """
        super().__init__(name, ledger)
        self.url = url
        self.use_playwright = use_playwright
    
    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect data by scraping the target URL.
        
        Returns:
            List of dictionaries containing the scraped data
        
        Raises:
            Exception: If scraping fails
        """
        logger.debug(f"{self.name}: Scraping {self.url}")
        
        if self.use_playwright:
            return await self.scrape_dynamic()
        else:
            return await self.scrape_static()
    
    @abstractmethod
    async def scrape_static(self) -> list[dict[str, Any]]:
        """
        Scrape data from static HTML using BeautifulSoup.
        
        Returns:
            List of dictionaries containing the scraped data
        
        Raises:
            Exception: If scraping fails
        """
        pass
    
    @abstractmethod
    async def scrape_dynamic(self) -> list[dict[str, Any]]:
        """
        Scrape data from dynamic content using Playwright.
        
        Returns:
            List of dictionaries containing the scraped data
        
        Raises:
            Exception: If scraping fails
        """
        pass
