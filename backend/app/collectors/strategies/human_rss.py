from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import feedparser # type: ignore
import time
from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import NewsItem

logger = logging.getLogger(__name__)

class HumanRSSCollector(ICollector):
    @property
    def name(self) -> str:
        return "HumanRSSCollector"

    @property
    def description(self) -> str:
        return "Ingests news headlines from RSS feeds (e.g., CoinDesk, Cointelegraph)."

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feed_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [
                        "https://www.coindesk.com/arc/outboundfeeds/rss/",
                        "https://cointelegraph.com/rss"
                    ]
                },
                "mock_mode": {"type": "boolean", "default": False}
            },
            "required": ["feed_urls"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        if "feed_urls" not in config or not isinstance(config["feed_urls"], list):
            return False
        return True

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        if config.get("mock_mode", False):
            return True

        # Simple test: try to fetch the first feed
        feed_urls = config.get("feed_urls", [])
        if not feed_urls:
            return False
            
        try:
            # Add user agent to prevent 403
            feed = feedparser.parse(feed_urls[0], agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            if hasattr(feed, 'status'):
                logger.info(f"Feed status: {feed.status}")
            
            if feed.bozo and not feed.entries: # Only fail if bozo AND no entries
                logger.warning(f"Feed malformed: {feed.bozo_exception}")
                # return False # Let's be lenient if entries exist
            
            return len(feed.entries) > 0 or (hasattr(feed, 'status') and feed.status == 200)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def collect(self, config: Dict[str, Any]) -> List[Any]:
        results = []
        if config.get("mock_mode", False):
            # Mock data
            results.append(NewsItem(
                title="Bitcoin hits $100k (Mock)",
                link="https://example.com/btc-100k",
                published_at=datetime.now(),
                summary="Bitcoin has finally reached the moon.",
                source="MockSource",
                collected_at=datetime.now()
            ))
            results.append(NewsItem(
                title="Ethereum gas fees drop (Mock)",
                link="https://example.com/eth-gas",
                published_at=datetime.now(),
                summary="Gas is cheap now.",
                source="MockSource",
                collected_at=datetime.now()
            ))
            return results

        feed_urls = config.get("feed_urls", [])

        for url in feed_urls:
            try:
                logger.info(f"Fetching RSS feed: {url}")
                feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                
                if hasattr(feed, 'status'):
                    logger.info(f"Feed status for {url}: {feed.status}")
                
                if not feed.entries:
                    logger.warning(f"No entries found for {url}")
                    continue

                source_name = "Unknown"
                if "coindesk" in url:
                    source_name = "CoinDesk"
                elif "cointelegraph" in url:
                    source_name = "Cointelegraph"
                elif "feed" in feed and "title" in feed.feed:
                    source_name = feed.feed.title

                for entry in feed.entries[:10]: # Limit to 10 most recent
                    # Parse published date
                    published_at = None
                    if hasattr(entry, "published_parsed"):
                        published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    elif hasattr(entry, "updated_parsed"):
                        published_at = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                    
                    # Create NewsItem
                    item = NewsItem(
                        title=entry.title,
                        link=entry.link,
                        published_at=published_at,
                        summary=entry.summary if hasattr(entry, "summary") else None,
                        source=source_name,
                        collected_at=datetime.now()
                    )
                    results.append(item)

            except Exception as e:
                logger.error(f"Error fetching feed {url}: {e}")
        
        return results

# Register strategy
CollectorRegistry.register(HumanRSSCollector)
