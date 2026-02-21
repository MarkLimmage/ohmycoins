from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import aiohttp
import logging
from bs4 import BeautifulSoup
from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry

# Constants
COINSPOT_PUBLIC_API_URL = "https://www.coinspot.com.au/pubapi/v2/latest"
COINSPOT_TRADECOINS_URL = "https://www.coinspot.com.au/tradecoins"

class CoinSpotPriceCollector(ICollector):
    
    @property
    def name(self) -> str:
        return "market_coinspot"
        
    @property
    def description(self) -> str:
        return "Collects real-time crypto prices from CoinSpot (API or Scraping)."
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "use_web_scraping": {
                    "type": "boolean",
                    "default": True,
                    "title": "Use Web Scraping (All Coins)"
                },
                "request_timeout": {
                    "type": "integer",
                    "default": 30,
                    "title": "Request Timeout (seconds)"
                }
            },
            "required": []
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True
        
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        url = COINSPOT_TRADECOINS_URL if config.get("use_web_scraping", True) else COINSPOT_PUBLIC_API_URL
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def collect(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        use_web_scraping = config.get("use_web_scraping", True)
        timeout = config.get("request_timeout", 30)
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                if use_web_scraping:
                    results = await self._collect_via_scraping(session, timeout)
                else:
                    results = await self._collect_via_api(session, timeout)
                    
        except Exception as e:
            logging.error(f"Error collecting from CoinSpot: {e}")
            
        return results

    async def _collect_via_api(self, session: aiohttp.ClientSession, timeout: int) -> List[Dict[str, Any]]:
        results = []
        try:
            async with session.get(COINSPOT_PUBLIC_API_URL, timeout=timeout) as response:
                if response.status != 200:
                    logging.error(f"CoinSpot API returned status {response.status}")
                    return []
                    
                data = await response.json()
                if data.get("status") == "ok":
                    prices = data.get("prices", {})
                    timestamp = datetime.now(timezone.utc)
                    
                    for coin, details in prices.items():
                        try:
                            # API returns string numbers
                            bid = float(details.get('bid', 0))
                            ask = float(details.get('ask', 0))
                            last = float(details.get('last', 0))
                            
                            results.append({
                                "type": "price",
                                "source": "coinspot",
                                "coin_type": coin.lower(),
                                "bid": bid,
                                "ask": ask,
                                "last": last,
                                "timestamp": timestamp.isoformat()
                            })
                        except (ValueError, TypeError) as e:
                            continue
        except Exception as e:
            logging.error(f"Error fetching from CoinSpot API: {e}")
            
        return results

    async def _collect_via_scraping(self, session: aiohttp.ClientSession, timeout: int) -> List[Dict[str, Any]]:
        results = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get(COINSPOT_TRADECOINS_URL, headers=headers, timeout=timeout) as response:
                if response.status != 200:
                    logging.error(f"CoinSpot Scraping returned status {response.status}")
                    return []
                    
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                coin_rows = soup.find_all('tr', attrs={'data-coin': True})
                timestamp = datetime.now(timezone.utc)
                
                for row in coin_rows:
                    coin_symbol = row.get('data-coin', '').lower()
                    if not coin_symbol or coin_symbol == 'aud':
                        continue
                        
                    try:
                        tds = row.find_all('td')
                        if len(tds) >= 4:
                            # Typically index 2 is buy, 3 is sell on this page (based on original code)
                            # Original code: buy_td = tds[2], sell_td = tds[3]
                            buy_val = tds[2].get('data-value')
                            sell_val = tds[3].get('data-value')
                            
                            if buy_val and sell_val:
                                bid = float(buy_val)
                                ask = float(sell_val)
                                last = (bid + ask) / 2 # imputed
                                
                                results.append({
                                    "type": "price",
                                    "source": "coinspot",
                                    "coin_type": coin_symbol,
                                    "bid": bid,
                                    "ask": ask,
                                    "last": last,
                                    "timestamp": timestamp.isoformat()
                                })
                    except Exception:
                        continue
                        
        except Exception as e:
            logging.error(f"Error scraping CoinSpot: {e}")
            
        return results

CollectorRegistry.register(CoinSpotPriceCollector)
