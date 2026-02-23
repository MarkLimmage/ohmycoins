from typing import Any, Dict, List, Optional
import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime, timezone

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import PriceData5Min

logger = logging.getLogger(__name__)

class CoinspotExchangeCollector(ICollector):
    @property
    def name(self) -> str:
        return "CoinspotExchange"

    @property
    def description(self) -> str:
        return "Fetches cryptocurrency prices from Coinspot via API or Web Scraping."

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "use_web_scraping": {"type": "boolean", "default": True},
                "max_retries": {"type": "integer", "default": 3},
                "retry_delay": {"type": "integer", "default": 5},
                "timeout": {"type": "number", "default": 30.0}
            },
            "required": []
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        # Configuration is optional/flexible, mostly defaults apply
        return True

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        # Test by fetching the public API which is always available
        url = "https://www.coinspot.com.au/pubapi/v2/latest"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("status") == "ok"
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def collect(self, config: Dict[str, Any]) -> List[PriceData5Min]:
        # Default to True for web scraping if not specified, to ensure full coin coverage
        use_web_scraping = config.get("use_web_scraping", True)
        max_retries = config.get("max_retries", 3)
        retry_delay = config.get("retry_delay", 5)
        timeout = config.get("timeout", 30.0)

        prices_data = None

        for attempt in range(1, max_retries + 1):
            try:
                if use_web_scraping:
                    prices_data = await self._fetch_scraped_prices(timeout)
                else:
                    prices_data = await self._fetch_public_prices(timeout)

                if prices_data:
                    break
            except Exception as e:
                logger.error(f"Error in collect attempt {attempt}: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
        
        if not prices_data:
            logger.error("Failed to collect data from Coinspot.")
            return []

        # Convert dict to PriceData5Min objects
        results = []
        now = datetime.now(timezone.utc)
        
        for coin, data in prices_data.items():
            try:
                # Ensure we have required fields
                if "bid" in data and "ask" in data and "last" in data:
                    item = PriceData5Min(
                        coin_type=coin.lower(),
                        bid=Decimal(str(data["bid"])),
                        ask=Decimal(str(data["ask"])),
                        last=Decimal(str(data["last"])),
                        timestamp=now
                        # created_at is handled by default factory
                    )
                    results.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse coin data for {coin}: {e}")
                continue
                
        logger.info(f"Collected {len(results)} price records from Coinspot.")
        return results

    async def _fetch_public_prices(self, timeout: float) -> Optional[Dict[str, Any]]:
        url = "https://www.coinspot.com.au/pubapi/v2/latest"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "ok":
                return data.get("prices", {})
        return None

    async def _fetch_scraped_prices(self, timeout: float) -> Optional[Dict[str, Any]]:
        url = "https://www.coinspot.com.au/tradecoins"
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            
            soup = BeautifulSoup(html, 'html.parser')
            coin_rows = soup.find_all('tr', attrs={'data-coin': True})
            
            prices = {}
            for row in coin_rows:
                coin_symbol = row.get('data-coin', '').upper()
                if not coin_symbol or coin_symbol == 'AUD':
                    continue
                
                try:
                    tds = row.find_all('td')
                    if len(tds) >= 4:
                        # Index 2 is Buy, Index 3 is Sell
                        buy_val = tds[2].get('data-value')
                        sell_val = tds[3].get('data-value')
                        
                        if buy_val and sell_val:
                            buy_price = float(buy_val)
                            sell_price = float(sell_val)
                            
                            if buy_price > 0 and sell_price > 0:
                                last_price = (buy_price + sell_price) / 2
                                prices[coin_symbol.lower()] = {
                                    "bid": buy_price,
                                    "ask": sell_price,
                                    "last": last_price
                                }
                except Exception:
                    continue
            
            return prices if prices else None
