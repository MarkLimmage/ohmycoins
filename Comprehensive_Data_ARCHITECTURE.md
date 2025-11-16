# Comprehensive Data Collection - Architecture Design

## Document Information

**Version**: 1.0  
**Last Updated**: 2025-11-16  
**Status**: Final

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Architecture](#system-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Architecture](#data-architecture)
5. [Technology Stack](#technology-stack)

---

## 1. Architecture Overview

### 1.1 Architecture Principles

1. **Modularity**: Each ledger and collector is an independent component
2. **Scalability**: Horizontal scaling through stateless collectors
3. **Reliability**: Graceful degradation and fault tolerance
4. **Cost-Efficiency**: Maximize free/low-cost data sources
5. **Maintainability**: Clear separation of concerns
6. **Security**: Defense in depth, encrypted credentials

### 1.2 Architecture Constraints

- **Single Exchange**: CoinSpot only (simplifies complexity)
- **Budget Cap**: Maximum $100/month for API subscriptions
- **Technology Stack**: Python 3.10+, FastAPI, PostgreSQL
- **Deployment**: Docker containers

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                External Data Sources                      │
├──────────────────────────────────────────────────────────┤
│  Glass Ledger        Human Ledger       Catalyst Ledger   │
│  • DeFiLlama         • CryptoPanic      • SEC API         │
│  • Glassnode         • Newscatcher      • CoinSpot        │
│  • Nansen            • Reddit           • Announcements   │
│                      • Twitter                             │
│                                                            │
│                   Exchange Ledger                          │
│                   • CoinSpot API                           │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Oh My Coins Backend (FastAPI)                │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐  │
│  │     Comprehensive Collector Framework              │  │
│  ├────────────────────────────────────────────────────┤  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │  │
│  │  │Glass │ │Human │ │Catalyst│ │Exchange│           │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘             │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │   Collection Orchestrator (APScheduler + Queue)    │  │
│  └────────────────────────────────────────────────────┘  │
│                           │                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │   Data Validation Layer (Pydantic)                 │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                PostgreSQL Database                        │
├──────────────────────────────────────────────────────────┤
│  • price_data_5min (enhanced)  • on_chain_metrics        │
│  • protocol_fundamentals        • news_sentiment          │
│  • social_sentiment             • catalyst_events         │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Layers

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| **Data Source** | External APIs, Websites | Provide raw data |
| **Collection** | Collectors, Scrapers | Fetch data |
| **Orchestration** | Scheduler, Queue | Coordinate collection |
| **Validation** | Pydantic Models | Ensure data quality |
| **Persistence** | Database, ORM | Store data |
| **Monitoring** | Logs, Metrics | Track health |
| **API** | FastAPI Routes | Expose data |

---

## 3. Component Architecture

### 3.1 Base Collector Class

```python
# app/services/collectors/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime

class BaseCollector(ABC):
    """Base class for all collectors."""
    
    def __init__(self, name: str, ledger: str):
        self.name = name
        self.ledger = ledger
        self.status = "idle"
        self.last_run = None
        self.error_count = 0
        self.success_count = 0
    
    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from source."""
        pass
    
    async def run(self) -> bool:
        """Execute collection with error handling."""
        self.status = "running"
        self.last_run = datetime.utcnow()
        
        try:
            data = await self.collect()
            await self._validate_and_store(data)
            self.status = "success"
            self.success_count += 1
            return True
        except Exception as e:
            self.status = "failed"
            self.error_count += 1
            await self._log_error(e)
            return False
```

### 3.2 API Collector Pattern

```python
# app/services/collectors/api_collector.py
import aiohttp
from tenacity import retry, stop_after_attempt

class APICollector(BaseCollector):
    """Base for API-based collectors."""
    
    def __init__(self, name: str, base_url: str, api_key: str = None):
        super().__init__(name, "api")
        self.base_url = base_url
        self.api_key = api_key
    
    @retry(stop=stop_after_attempt(3))
    async def _make_request(self, endpoint: str) -> Dict:
        """Make HTTP request with retry."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{endpoint}", 
                                  headers=headers) as response:
                response.raise_for_status()
                return await response.json()
```

### 3.3 Web Scraper Pattern

```python
# app/services/collectors/scraper_collector.py
from playwright.async_api import async_playwright

class ScraperCollector(BaseCollector):
    """Base for web scraping collectors."""
    
    def __init__(self, name: str, url: str, use_browser: bool = False):
        super().__init__(name, "scraper")
        self.url = url
        self.use_browser = use_browser
    
    async def _scrape_with_playwright(self, url: str) -> str:
        """Scrape using Playwright for JS content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            content = await page.content()
            await browser.close()
            return content
```

### 3.4 Collection Orchestrator

```python
# app/services/orchestrator.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CollectionOrchestrator:
    """Orchestrates all data collection."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.collectors = {}
    
    def register_collector(self, collector, schedule: str, priority: int = 5):
        """Register collector with schedule."""
        self.collectors[collector.name] = collector
        self.scheduler.add_job(
            func=collector.run,
            trigger=schedule,
            id=collector.name
        )
    
    def start(self):
        """Start orchestrator."""
        self.scheduler.start()
    
    def get_health_status(self) -> Dict:
        """Get health status of all collectors."""
        return {
            name: collector.health_check()
            for name, collector in self.collectors.items()
        }
```

---

## 4. Data Architecture

### 4.1 Database Schema

```sql
-- Enhanced price data
CREATE TABLE price_data_5min (
    id SERIAL PRIMARY KEY,
    coin VARCHAR(10) NOT NULL,
    last NUMERIC NOT NULL,
    bid NUMERIC,
    ask NUMERIC,
    volume_24h NUMERIC,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_coin_timestamp (coin, timestamp DESC)
);

-- Glass Ledger
CREATE TABLE protocol_fundamentals (
    id SERIAL PRIMARY KEY,
    protocol VARCHAR(50) NOT NULL,
    tvl_usd NUMERIC,
    fees_24h NUMERIC,
    revenue_24h NUMERIC,
    collected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(protocol, collected_at::date)
);

CREATE TABLE on_chain_metrics (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(10) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value NUMERIC,
    source VARCHAR(50),
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Human Ledger
CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source VARCHAR(100),
    url TEXT UNIQUE,
    published_at TIMESTAMP,
    sentiment VARCHAR(20),
    sentiment_score NUMERIC,
    currencies TEXT[],
    collected_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE social_sentiment (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    content TEXT,
    author VARCHAR(100),
    score INTEGER,
    sentiment VARCHAR(20),
    currencies TEXT[],
    posted_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Catalyst Ledger
CREATE TABLE catalyst_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source VARCHAR(100),
    currencies TEXT[],
    impact_score INTEGER CHECK (impact_score BETWEEN 1 AND 10),
    detected_at TIMESTAMP DEFAULT NOW()
);

-- Collector Metadata
CREATE TABLE collector_runs (
    id SERIAL PRIMARY KEY,
    collector_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    records_collected INTEGER,
    error_message TEXT
);
```

### 4.2 Data Retention

```python
# app/services/data_retention.py
RETENTION_POLICIES = {
    "price_data_5min": 365,      # 1 year
    "protocol_fundamentals": 365,
    "on_chain_metrics": 180,
    "news_sentiment": 90,
    "social_sentiment": 30,
    "catalyst_events": 730,      # 2 years
    "collector_runs": 30
}
```

### 4.3 API Integration

```python
# app/api/routes/collectors.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/collectors")

@router.get("/health")
async def get_health():
    """Get collector health status."""
    orchestrator = get_orchestrator()
    return orchestrator.get_health_status()

@router.post("/{name}/trigger")
async def trigger_collector(name: str):
    """Manually trigger a collector."""
    orchestrator = get_orchestrator()
    return await orchestrator.trigger_manual(name)

@router.get("/data/glass/protocols")
async def get_protocols(protocol: str, days: int = 30):
    """Get protocol data."""
    # Query protocol_fundamentals
    pass

@router.get("/data/catalyst/events")
async def get_events(min_impact: int = 5, hours: int = 24):
    """Get catalyst events."""
    # Query catalyst_events
    pass
```

---

## 5. Technology Stack

### 5.1 Core Technologies

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | FastAPI | 0.104+ |
| **Database** | PostgreSQL | 15+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Task Scheduling** | APScheduler | 3.10+ |
| **Async HTTP** | aiohttp | 3.9+ |
| **Web Scraping (Static)** | BeautifulSoup4 | 4.12+ |
| **Web Scraping (Dynamic)** | Playwright | 1.40+ |
| **Caching** | Redis | 7+ |
| **Encryption** | cryptography | 41+ |
| **Data Validation** | Pydantic | 2.0+ |
| **Monitoring** | Prometheus Client | 0.19+ |

### 5.2 Dependencies

```toml
# pyproject.toml additions
[project.dependencies]
apscheduler = "^3.10.0"
aiohttp = "^3.9.0"
beautifulsoup4 = "^4.12.0"
playwright = "^1.40.0"
redis = "^5.0.0"
cryptography = "^41.0.0"
pydantic = "^2.0.0"
prometheus-client = "^0.19.0"
tenacity = "^8.2.0"
praw = "^7.7.0"  # Reddit API
```

### 5.3 Docker Configuration

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - COLLECTORS_ENABLED=true
      - COLLECTOR_TIER=1
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
      
  collector-worker:
    build: ./backend
    command: python -m app.services.collector_worker
    depends_on:
      - db
      - redis
```

---

**Document Status**: Complete  
**Last Updated**: 2025-11-16  
**Version**: 1.0
