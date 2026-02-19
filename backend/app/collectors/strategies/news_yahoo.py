from typing import Any, Dict, List
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
import logging

class YahooNewsCollector(ICollector):
    
    @property
    def name(self) -> str:
        return "news_yahoo"
        
    @property
    def description(self) -> str:
        return "Scrapes crypto news from Yahoo Finance."
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string", 
                    "default": "https://finance.yahoo.com/topic/crypto/",
                    "title": "Base URL"
                },
                "max_items": {
                    "type": "integer",
                    "default": 10,
                    "title": "Max Items"
                }
            },
            "required": ["base_url"]
        }
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return "base_url" in config
    
    async def test_connection(self, config: Dict[str, Any]) -> bool:
        url = config.get("base_url", "https://finance.yahoo.com/topic/crypto/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def collect(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = config.get("base_url", "https://finance.yahoo.com/topic/crypto/")
        limit = config.get("max_items", 10)
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # Fetch listing page
                async with session.get(url, headers=headers, timeout=30) as response:
                    content = await response.text()
                
                soup = BeautifulSoup(content, 'html.parser')
                links = []
                
                # Extract links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/news/' in href:
                        full_url = urljoin("https://finance.yahoo.com", href).split('?')[0]
                        if full_url not in links:
                            links.append(full_url)
                            if len(links) >= limit:
                                break
                
                # Fetch details for each link (simple version: just return links/titles from listing if possible, 
                # but for full content we'd need to visit each. For speed in this demo, we might just return the listing info
                # or visit the first few. Let's visit them to match the scraper logic.)
                
                for article_url in links:
                    try:
                        async with session.get(article_url, headers=headers, timeout=10) as detail_res:
                            if detail_res.status != 200: continue
                            detail_html = await detail_res.text()
                            
                        detail_soup = BeautifulSoup(detail_html, 'html.parser')
                        
                        # Extract Content
                        article_body = ""
                        # Try common Yahoo selectors
                        article_container = (
                            detail_soup.find('div', class_=lambda x: x and 'caas-body' in x.lower()) or
                            detail_soup.find('div', class_=lambda x: x and 'article-body' in x.lower()) or
                            detail_soup.find('article')
                        )
                        
                        if article_container:
                            paragraphs = article_container.find_all('p')
                            article_body = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                            
                        title_tag = detail_soup.find('h1')
                        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
                        
                        # Publish date
                        publish_date = None
                        time_tag = detail_soup.find('time')
                        if time_tag and time_tag.has_attr('datetime'):
                            publish_date = time_tag['datetime']
                            
                        results.append({
                            "title": title,
                            "link": article_url,
                            "published": publish_date,
                            "summary": article_body[:500] if article_body else "", # Truncate for summary
                            "source": "YahooFinance",
                            "collected_at": datetime.utcnow().isoformat()
                        })
                        
                    except Exception as e:
                        logging.error(f"Error scraping Yahoo article {article_url}: {e}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error collecting from Yahoo: {e}")
            
        return results

CollectorRegistry.register(YahooNewsCollector)
