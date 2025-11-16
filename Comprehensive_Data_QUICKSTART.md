# Comprehensive Data Collection - Quick Start Guide

## Overview

This guide provides practical code examples and quick-start instructions for implementing the 4 Ledgers data collection system in Oh My Coins.

**Target Audience**: Developers implementing the data collection upgrade  
**Prerequisites**: Python 3.10+, FastAPI, PostgreSQL, basic web scraping knowledge  
**Time to Read**: 15 minutes

---

## The 4 Ledgers at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    Oh My Coins - Data Collection                 │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌──────▼──────┐      ┌─────▼─────┐      ┌──────▼──────┐
    │   Glass     │      │   Human   │      │  Catalyst   │
    │   Ledger    │      │   Ledger  │      │   Ledger    │
    └──────┬──────┘      └─────┬─────┘      └──────┬──────┘
           │                    │                    │
    ┌──────▼────────────────────▼────────────────────▼──────┐
    │                  Exchange Ledger                       │
    │                  (CoinSpot API)                        │
    └────────────────────────────────────────────────────────┘
                              │
                     ┌────────▼─────────┐
                     │  PostgreSQL DB   │
                     └──────────────────┘
```

---

## Quick Setup

### 1. Install Dependencies

```bash
cd backend
uv add scrapy playwright beautifulsoup4 aiohttp redis pydantic-settings
uv add requests pandas pytz
playwright install chromium
```

### 2. Environment Configuration

```bash
# .env
# Glass Ledger (Tier 2)
NANSEN_API_KEY=your_nansen_key_here  # Optional, for Tier 2

# Human Ledger (Tier 2)
NEWSCATCHER_API_KEY=your_newscatcher_key_here  # Optional, for Tier 2

# Catalyst Ledger - No keys needed (all free)

# Exchange Ledger
COINSPOT_API_KEY=your_existing_key
COINSPOT_API_SECRET=your_existing_secret

# Scraping (Tier 3)
PROXY_SERVICE_URL=your_proxy_url  # Optional, for X scraping
```

---

## Ledger 1: The Glass Ledger (On-Chain Data)

### DeFiLlama API Integration (Free)

**Endpoint**: `https://api.llama.fi`  
**Purpose**: Protocol fundamentals (TVL, fees, revenue)

```python
# app/services/collectors/defillama.py
import aiohttp
from datetime import datetime
from typing import Dict, List

class DeFiLlamaCollector:
    """Collects protocol fundamental data from DeFiLlama."""
    
    BASE_URL = "https://api.llama.fi"
    
    async def get_protocol_tvl(self, protocol: str) -> Dict:
        """Get Total Value Locked for a protocol."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/protocol/{protocol}"
            async with session.get(url) as response:
                data = await response.json()
                return {
                    "protocol": protocol,
                    "tvl_usd": data.get("tvl", 0),
                    "chain_tvls": data.get("chainTvls", {}),
                    "timestamp": datetime.utcnow()
                }
    
    async def get_protocol_fees(self, protocol: str) -> Dict:
        """Get protocol fees and revenue."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/summary/fees/{protocol}"
            async with session.get(url) as response:
                data = await response.json()
                return {
                    "protocol": protocol,
                    "total_fees_24h": data.get("total24h", 0),
                    "total_revenue_24h": data.get("totalRevenue24h", 0),
                    "timestamp": datetime.utcnow()
                }
    
    async def collect_all_protocols(self, protocols: List[str]):
        """Collect data for multiple protocols."""
        results = []
        for protocol in protocols:
            tvl_data = await self.get_protocol_tvl(protocol)
            fee_data = await self.get_protocol_fees(protocol)
            results.append({**tvl_data, **fee_data})
        return results

# Usage
protocols = ["uniswap", "aave", "compound", "curve"]
collector = DeFiLlamaCollector()
data = await collector.collect_all_protocols(protocols)
```

---

### Glassnode Dashboard Scraper (Free - High Complexity)

**Target**: `https://studio.glassnode.com`  
**Purpose**: Free on-chain metrics (Active Addresses, MVRV, etc.)  
**Complexity**: High (requires Playwright for JavaScript rendering)

```python
# app/services/scrapers/glassnode_scraper.py
from playwright.async_api import async_playwright
import json
from datetime import datetime

class GlassnodeScraper:
    """Scrapes free metrics from Glassnode Studio."""
    
    BASE_URL = "https://studio.glassnode.com"
    
    async def scrape_metric(self, asset: str, metric: str) -> Dict:
        """
        Scrape a single metric from Glassnode.
        
        Examples:
        - asset="BTC", metric="addresses-active-count"
        - asset="ETH", metric="mvrv"
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to metric page
            url = f"{self.BASE_URL}/metrics?a={asset}&m={metric}"
            await page.goto(url, wait_until="networkidle")
            
            # Wait for chart to load
            await page.wait_for_selector(".chart-container", timeout=30000)
            
            # Extract data from page (method varies by Glassnode's structure)
            # This is a simplified example - actual implementation needs to 
            # reverse-engineer their chart data structure
            data = await page.evaluate("""
                () => {
                    // Glassnode stores data in window object or specific elements
                    // This is pseudo-code - actual path needs investigation
                    const chartData = window.__CHART_DATA__ || {};
                    return chartData;
                }
            """)
            
            await browser.close()
            
            return {
                "asset": asset,
                "metric": metric,
                "value": data.get("latest_value"),
                "historical": data.get("series", []),
                "timestamp": datetime.utcnow()
            }

# Usage (run daily)
scraper = GlassnodeScraper()
btc_active = await scraper.scrape_metric("BTC", "addresses-active-count")
eth_mvrv = await scraper.scrape_metric("ETH", "mvrv")
```

**Note**: Glassnode's structure changes frequently. This scraper requires ongoing maintenance.

---

### Nansen API Integration (Tier 2: $49/month)

**Endpoint**: `https://api.nansen.ai`  
**Purpose**: "Smart Money" wallet tracking

```python
# app/services/collectors/nansen.py
import aiohttp
from typing import List, Dict

class NansenCollector:
    """Collects Smart Money data from Nansen Pro API."""
    
    BASE_URL = "https://api.nansen.ai/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_smart_money_flows(self, token: str) -> Dict:
        """Get net flows from smart money wallets for a token."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/smart-money/flows/{token}"
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                return {
                    "token": token,
                    "net_flow_usd": data.get("netFlowUsd", 0),
                    "smart_money_buying": data.get("buyingWallets", []),
                    "smart_money_selling": data.get("sellingWallets", []),
                    "timestamp": datetime.utcnow()
                }
    
    async def get_wallet_labels(self, address: str) -> Dict:
        """Get labels for a wallet address."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/labels/{address}"
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                return data.get("labels", [])

# Usage
collector = NansenCollector(api_key=os.getenv("NANSEN_API_KEY"))
btc_flows = await collector.get_smart_money_flows("bitcoin")
```

---

## Ledger 2: The Human Ledger (Sentiment Data)

### CryptoPanic API (Free)

**Endpoint**: `https://cryptopanic.com/api/v1`  
**Purpose**: Aggregated crypto news with sentiment tags

```python
# app/services/collectors/cryptopanic.py
import aiohttp
from typing import List, Dict

class CryptoPanicCollector:
    """Collects tagged crypto news from CryptoPanic."""
    
    BASE_URL = "https://cryptopanic.com/api/v1"
    
    async def get_news(
        self, 
        currencies: str = "BTC,ETH", 
        filter_type: str = "hot"
    ) -> List[Dict]:
        """
        Get crypto news.
        
        Args:
            currencies: Comma-separated list of currency codes
            filter_type: "rising", "hot", or "bullish"/"bearish"
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/posts/"
            params = {
                "auth_token": "public",  # Free tier
                "currencies": currencies,
                "filter": filter_type,
                "public": "true"
            }
            async with session.get(url, params=params) as response:
                data = await response.json()
                
                news_items = []
                for post in data.get("results", []):
                    news_items.append({
                        "title": post["title"],
                        "url": post["url"],
                        "source": post["source"]["title"],
                        "published_at": post["published_at"],
                        "votes": {
                            "positive": post["votes"]["positive"],
                            "negative": post["votes"]["negative"],
                            "important": post["votes"]["important"]
                        },
                        "currencies": [c["code"] for c in post.get("currencies", [])],
                        "sentiment": self._calculate_sentiment(post["votes"])
                    })
                
                return news_items
    
    def _calculate_sentiment(self, votes: Dict) -> str:
        """Calculate sentiment from votes."""
        pos = votes.get("positive", 0)
        neg = votes.get("negative", 0)
        
        if pos + neg == 0:
            return "neutral"
        
        ratio = pos / (pos + neg)
        if ratio > 0.6:
            return "bullish"
        elif ratio < 0.4:
            return "bearish"
        else:
            return "neutral"

# Usage (run every 5 minutes)
collector = CryptoPanicCollector()
hot_news = await collector.get_news(currencies="BTC,ETH", filter_type="hot")
```

---

### Newscatcher API (Tier 2: $10/month)

**Endpoint**: `https://api.newscatcherapi.com/v2`  
**Purpose**: High-quality news with built-in sentiment

```python
# app/services/collectors/newscatcher.py
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict

class NewscatcherCollector:
    """Collects crypto news from Newscatcher API."""
    
    BASE_URL = "https://api.newscatcherapi.com/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"x-api-key": api_key}
    
    async def search_crypto_news(
        self, 
        query: str = "cryptocurrency OR bitcoin OR ethereum",
        hours_back: int = 24
    ) -> List[Dict]:
        """Search for crypto-related news."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/search"
            from_date = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
            
            params = {
                "q": query,
                "lang": "en",
                "from": from_date,
                "sort_by": "relevancy",
                "page_size": 100
            }
            
            async with session.get(url, headers=self.headers, params=params) as response:
                data = await response.json()
                
                articles = []
                for article in data.get("articles", []):
                    articles.append({
                        "title": article["title"],
                        "summary": article.get("summary", ""),
                        "source": article["clean_url"],
                        "published_at": article["published_date"],
                        "sentiment": article.get("sentiment", "neutral"),
                        "url": article["link"]
                    })
                
                return articles

# Usage
collector = NewscatcherCollector(api_key=os.getenv("NEWSCATCHER_API_KEY"))
news = await collector.search_crypto_news(hours_back=1)
```

---

### Reddit API (Free)

**Purpose**: Retail investor sentiment from r/cryptocurrency

```python
# app/services/collectors/reddit.py
import praw  # pip install praw
from datetime import datetime
from typing import List, Dict

class RedditCollector:
    """Collects sentiment from Reddit crypto communities."""
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="OhMyCoins/1.0"
        )
    
    def get_hot_posts(self, subreddit: str = "cryptocurrency", limit: int = 50) -> List[Dict]:
        """Get hot posts from a subreddit."""
        subreddit_obj = self.reddit.subreddit(subreddit)
        posts = []
        
        for post in subreddit_obj.hot(limit=limit):
            posts.append({
                "title": post.title,
                "text": post.selftext,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "created_utc": datetime.fromtimestamp(post.created_utc),
                "url": post.url,
                "flair": post.link_flair_text
            })
        
        return posts
    
    def calculate_sentiment_score(self, posts: List[Dict]) -> float:
        """Calculate overall sentiment from posts."""
        if not posts:
            return 0.5
        
        total_score = sum(p["score"] * p["upvote_ratio"] for p in posts)
        return min(max(total_score / len(posts) / 1000, 0), 1)  # Normalize 0-1

# Usage (run every 15 minutes)
collector = RedditCollector()
posts = collector.get_hot_posts(limit=50)
sentiment = collector.calculate_sentiment_score(posts)
```

---

## Ledger 3: The Catalyst Ledger (Event Data)

### SEC API (Free)

**Endpoint**: `https://data.sec.gov/submissions/`  
**Purpose**: Regulatory actions and filings

```python
# app/services/collectors/sec.py
import aiohttp
from typing import List, Dict
from datetime import datetime

class SECCollector:
    """Collects regulatory data from SEC.gov API."""
    
    BASE_URL = "https://data.sec.gov"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "OhMyCoins contact@ohmycoins.com",  # Required by SEC
            "Accept-Encoding": "gzip, deflate"
        }
    
    async def get_company_filings(self, cik: str) -> Dict:
        """
        Get filings for a company by CIK number.
        
        Example CIKs:
        - Coinbase: 0001679788
        - MicroStrategy: 0001050446
        """
        async with aiohttp.ClientSession() as session:
            # Pad CIK to 10 digits
            cik_padded = cik.zfill(10)
            url = f"{self.BASE_URL}/submissions/CIK{cik_padded}.json"
            
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                
                recent_filings = data.get("filings", {}).get("recent", {})
                filings = []
                
                for i in range(len(recent_filings.get("filingDate", []))):
                    filings.append({
                        "form": recent_filings["form"][i],
                        "filing_date": recent_filings["filingDate"][i],
                        "accession_number": recent_filings["accessionNumber"][i],
                        "primary_document": recent_filings["primaryDocument"][i],
                        "description": recent_filings.get("primaryDocDescription", [""])[i]
                    })
                
                return {
                    "cik": cik,
                    "company": data.get("name"),
                    "filings": filings[:10]  # Latest 10
                }
    
    async def search_crypto_keywords(self, companies: List[str]) -> List[Dict]:
        """Monitor multiple companies for crypto-related filings."""
        crypto_filings = []
        
        for cik in companies:
            data = await self.get_company_filings(cik)
            
            for filing in data["filings"]:
                # Check if filing mentions crypto keywords
                desc = filing["description"].lower()
                if any(kw in desc for kw in ["crypto", "bitcoin", "digital asset", "blockchain"]):
                    crypto_filings.append({
                        "company": data["company"],
                        "filing": filing,
                        "detected_at": datetime.utcnow()
                    })
        
        return crypto_filings

# Usage (run every 10 minutes during market hours)
collector = SECCollector()
# Monitor major crypto companies
companies = ["0001679788", "0001050446"]  # Coinbase, MicroStrategy
filings = await collector.search_crypto_keywords(companies)
```

---

### CoinSpot Announcements Scraper (Free - Critical)

**Target**: `https://coinspot.zendesk.com/hc/en-us/categories/360000087515-General-Announcements-Updates`  
**Purpose**: Detect new listings (highest-ROI catalyst)

```python
# app/services/scrapers/coinspot_announcements.py
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime
from typing import List, Dict

class CoinSpotAnnouncementsScraper:
    """Scrapes CoinSpot announcements for listing events."""
    
    BASE_URL = "https://coinspot.zendesk.com/hc/en-us"
    ANNOUNCEMENTS_URL = f"{BASE_URL}/categories/360000087515-General-Announcements-Updates"
    
    async def check_for_new_listings(self) -> List[Dict]:
        """
        Check for new coin listings or mainnet swaps.
        This should run every 30-60 seconds for fastest detection.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.ANNOUNCEMENTS_URL) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all article links
                articles = soup.find_all('a', class_='article-list-link')
                
                events = []
                for article in articles:
                    title = article.text.strip()
                    url = self.BASE_URL + article['href']
                    
                    # Detect listing/mainnet events
                    if self._is_listing_event(title):
                        events.append({
                            "type": "listing",
                            "title": title,
                            "url": url,
                            "coin": self._extract_coin_name(title),
                            "detected_at": datetime.utcnow()
                        })
                
                return events
    
    def _is_listing_event(self, title: str) -> bool:
        """Check if title indicates a listing/mainnet event."""
        title_lower = title.lower()
        keywords = [
            "coinspot will support",
            "new coin",
            "listing",
            "mainnet",
            "airdrop",
            "now available"
        ]
        return any(kw in title_lower for kw in keywords)
    
    def _extract_coin_name(self, title: str) -> str:
        """Extract coin name from title."""
        # Example: "CoinSpot will support the XYZ Mainnet Swap"
        # This is simplified - actual implementation needs robust parsing
        import re
        match = re.search(r'support (?:the )?(\w+)', title, re.IGNORECASE)
        if match:
            return match.group(1)
        return "Unknown"

# Usage (run in tight loop - every 30 seconds)
scraper = CoinSpotAnnouncementsScraper()
while True:
    new_listings = await scraper.check_for_new_listings()
    if new_listings:
        # IMMEDIATE ACTION REQUIRED
        for listing in new_listings:
            print(f"🚨 NEW LISTING DETECTED: {listing['coin']}")
            # Trigger trading algorithm or alert
    await asyncio.sleep(30)
```

---

## Ledger 4: The Exchange Ledger (CoinSpot)

### CoinSpot API Client (Free - Enhanced)

**Purpose**: Price data + trade execution

```python
# app/services/coinspot_client.py
import hmac
import hashlib
import json
import time
import aiohttp
from typing import Dict, List

class CoinSpotClient:
    """Enhanced CoinSpot API client for data and trading."""
    
    PUBLIC_API = "https://www.coinspot.com.au/pubapi/v2"
    PRIVATE_API = "https://www.coinspot.com.au/api/v2"
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
    
    # PUBLIC METHODS (No auth required)
    
    async def get_latest_prices(self) -> Dict:
        """Get latest prices for all coins."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.PUBLIC_API}/latest"
            async with session.post(url) as response:
                data = await response.json()
                return data.get("prices", {})
    
    async def get_coin_price(self, coin: str) -> float:
        """Get price for specific coin."""
        prices = await self.get_latest_prices()
        return float(prices.get(coin, {}).get("last", 0))
    
    # PRIVATE METHODS (Require auth)
    
    def _generate_signature(self, post_data: Dict) -> str:
        """Generate HMAC-SHA512 signature."""
        post_data_json = json.dumps(post_data, separators=(',', ':'))
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            post_data_json.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        return signature
    
    def _get_headers(self, post_data: Dict) -> Dict:
        """Generate request headers."""
        nonce = int(time.time() * 1000)
        post_data['nonce'] = nonce
        
        return {
            'Content-Type': 'application/json',
            'key': self.api_key,
            'sign': self._generate_signature(post_data)
        }
    
    async def get_balances(self) -> Dict:
        """Get account balances."""
        post_data = {}
        headers = self._get_headers(post_data)
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.PRIVATE_API}/my/balances"
            async with session.post(url, json=post_data, headers=headers) as response:
                return await response.json()
    
    async def place_market_buy(self, coin: str, amount_aud: float) -> Dict:
        """
        Place a market buy order.
        
        Args:
            coin: Coin code (e.g., "BTC", "ETH")
            amount_aud: Amount in AUD to spend
        """
        post_data = {
            'cointype': coin,
            'amount': amount_aud
        }
        headers = self._get_headers(post_data)
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.PRIVATE_API}/my/buy"
            async with session.post(url, json=post_data, headers=headers) as response:
                return await response.json()
    
    async def place_market_sell(self, coin: str, amount_coin: float) -> Dict:
        """
        Place a market sell order.
        
        Args:
            coin: Coin code (e.g., "BTC", "ETH")
            amount_coin: Amount of coin to sell
        """
        post_data = {
            'cointype': coin,
            'amount': amount_coin
        }
        headers = self._get_headers(post_data)
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.PRIVATE_API}/my/sell"
            async with session.post(url, json=post_data, headers=headers) as response:
                return await response.json()

# Usage
client = CoinSpotClient(
    api_key=os.getenv("COINSPOT_API_KEY"),
    api_secret=os.getenv("COINSPOT_API_SECRET")
)

# Get prices (public)
btc_price = await client.get_coin_price("BTC")

# Trade (private - requires credentials)
balances = await client.get_balances()
buy_result = await client.place_market_buy("BTC", 100.0)  # Buy $100 of BTC
```

---

## Data Storage Patterns

### Database Schema

```sql
-- Glass Ledger
CREATE TABLE on_chain_metrics (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(10) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value NUMERIC,
    source VARCHAR(50),
    collected_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_asset_metric (asset, metric_name, collected_at)
);

CREATE TABLE protocol_fundamentals (
    id SERIAL PRIMARY KEY,
    protocol VARCHAR(50) NOT NULL,
    tvl_usd NUMERIC,
    fees_24h NUMERIC,
    revenue_24h NUMERIC,
    collected_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_protocol_time (protocol, collected_at)
);

-- Human Ledger
CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source VARCHAR(100),
    published_at TIMESTAMP,
    sentiment VARCHAR(20),  -- bullish, bearish, neutral
    sentiment_score NUMERIC,  -- -1 to 1
    currencies TEXT[],
    url TEXT,
    collected_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_published (published_at)
);

CREATE TABLE social_sentiment (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50),  -- reddit, twitter, etc.
    content TEXT,
    score INTEGER,
    sentiment VARCHAR(20),
    currencies TEXT[],
    author VARCHAR(100),
    posted_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_platform_time (platform, posted_at)
);

-- Catalyst Ledger
CREATE TABLE catalyst_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),  -- listing, regulatory, corporate
    title TEXT NOT NULL,
    description TEXT,
    source VARCHAR(100),
    currencies TEXT[],
    impact_score INTEGER,  -- 1-10
    detected_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_type_time (event_type, detected_at)
);

-- Exchange Ledger (enhance existing price_data_5min)
ALTER TABLE price_data_5min ADD COLUMN volume_24h NUMERIC;
ALTER TABLE price_data_5min ADD COLUMN bid NUMERIC;
ALTER TABLE price_data_5min ADD COLUMN ask NUMERIC;
```

---

## Testing Strategies

### Unit Tests

```python
# tests/services/test_defillama.py
import pytest
from app.services.collectors.defillama import DeFiLlamaCollector

@pytest.mark.asyncio
async def test_get_protocol_tvl():
    collector = DeFiLlamaCollector()
    data = await collector.get_protocol_tvl("uniswap")
    
    assert "tvl_usd" in data
    assert data["tvl_usd"] > 0
    assert data["protocol"] == "uniswap"

@pytest.mark.asyncio
async def test_get_protocol_fees():
    collector = DeFiLlamaCollector()
    data = await collector.get_protocol_fees("uniswap")
    
    assert "total_fees_24h" in data
    assert data["protocol"] == "uniswap"
```

### Integration Tests

```python
# tests/integration/test_data_pipeline.py
import pytest
from app.services.data_pipeline import DataPipeline

@pytest.mark.asyncio
async def test_full_collection_cycle():
    """Test complete data collection from all ledgers."""
    pipeline = DataPipeline()
    
    # Collect from all sources
    results = await pipeline.collect_all()
    
    assert "glass" in results
    assert "human" in results
    assert "catalyst" in results
    assert "exchange" in results
    
    # Verify data quality
    assert len(results["glass"]["protocols"]) > 0
    assert len(results["exchange"]["prices"]) > 0
```

---

## Common Pitfalls and Solutions

### 1. Rate Limiting

**Problem**: APIs throttle requests  
**Solution**: Implement exponential backoff

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 429:  # Too Many Requests
                raise Exception("Rate limited")
            return await response.json()
```

### 2. Web Scraper Detection

**Problem**: Scrapers get blocked  
**Solution**: Rotate user agents and use delays

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    # ... more user agents
]

async def scrape_with_rotation(url: str):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    await asyncio.sleep(random.uniform(1, 3))  # Random delay
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            return await response.text()
```

### 3. Data Quality Issues

**Problem**: Missing or malformed data  
**Solution**: Validation layer

```python
from pydantic import BaseModel, validator

class OnChainMetric(BaseModel):
    asset: str
    metric_name: str
    metric_value: float
    source: str
    
    @validator('metric_value')
    def value_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Metric value cannot be negative')
        return v
    
    @validator('asset')
    def asset_must_be_uppercase(cls, v):
        return v.upper()
```

---

## Next Steps

1. **Start with Exchange Ledger**: Enhance existing CoinSpot client (1 day)
2. **Add Catalyst Ledger**: SEC API + CoinSpot scraper (3 days)
3. **Implement Glass Ledger**: DeFiLlama API (2 days)
4. **Add Human Ledger**: CryptoPanic + Reddit (3 days)
5. **Test and Validate**: End-to-end testing (2 days)

**Total: 11 days for Tier 1 implementation**

---

## Resources

### Documentation
- [DeFiLlama API Docs](https://defillama.com/docs/api)
- [CryptoPanic API Docs](https://cryptopanic.com/developers/api/)
- [SEC EDGAR API](https://www.sec.gov/edgar/sec-api-documentation)
- [CoinSpot API Docs](https://www.coinspot.com.au/api)

### Tools
- [Playwright](https://playwright.dev/python/)
- [Scrapy](https://scrapy.org/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- [aiohttp](https://docs.aiohttp.org/)

---

**Document Status**: Complete  
**Last Updated**: 2025-11-16  
**Version**: 1.0
