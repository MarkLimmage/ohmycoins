from typing import Any, Dict, List
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
import logging

class DecryptCollector(ICollector):
    
    @property
    def name(self) -> str:
        return "news_decrypt"
        
    @property
    def description(self) -> str:
        return "Scrapes crypto news from Decrypt."
        
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string", 
                    "default": "https://decrypt.co/",
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
        url = config.get("base_url", "https://decrypt.co/")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def collect(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = config.get("base_url", "https://decrypt.co/")
        limit = config.get("max_items", 10)
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    content = await response.text()
                    
                soup = BeautifulSoup(content, 'html.parser')
                links = []
                
                # Extract links - Decrypt uses /number/title format
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('https://decrypt.co/'):
                        parts = href.replace('https://decrypt.co/', '').split('/')
                        if len(parts) > 0 and parts[0].isdigit():
                            if href not in links:
                                links.append(href)
                                if len(links) >= limit:
                                    break
                
                for article_url in links:
                    try:
                        async with session.get(article_url, headers=headers, timeout=10) as detail_res:
                            if detail_res.status != 200: continue
                            detail_html = await detail_res.text()
                            
                        detail_soup = BeautifulSoup(detail_html, 'html.parser')
                        
                        title_tag = detail_soup.find('h1', class_='post-title') or detail_soup.find('h1')
                        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
                        
                        summary = ""
                        subtitle_tag = detail_soup.find('h2', class_='post-subtitle')
                        if subtitle_tag:
                            summary = subtitle_tag.get_text(strip=True)
                        
                        time_tag = detail_soup.find('time')
                        published = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None
                        
                        results.append({
                            "title": title,
                            "link": article_url,
                            "published": published,
                            "summary": summary,
                            "source": "Decrypt",
                            "collected_at": datetime.utcnow().isoformat()
                        })
                        
                    except Exception as e:
                        logging.error(f"Error scraping Decrypt article {article_url}: {e}")
                        continue
                        
        except Exception as e:
            logging.error(f"Error collecting from Decrypt: {e}")
            
        return results

CollectorRegistry.register(DecryptCollector)
