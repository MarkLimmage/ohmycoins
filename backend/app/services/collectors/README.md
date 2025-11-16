# Phase 2.5: Comprehensive Data Collection - Developer Guide

This guide explains how to work with the Phase 2.5 comprehensive data collection system (The 4 Ledgers).

## Overview

Phase 2.5 upgrades Oh My Coins from basic price collection to comprehensive market intelligence gathering:

- **Glass Ledger**: On-chain and fundamental blockchain data
- **Human Ledger**: Social sentiment and narrative data
- **Catalyst Ledger**: High-impact event-driven data
- **Exchange Ledger**: Enhanced market microstructure data

## Architecture

```
┌─────────────────────────────────────────┐
│          External Data Sources          │
│  DeFiLlama • CryptoPanic • SEC • Etc.  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Collection Framework             │
│  BaseCollector → APICollector           │
│                → ScraperCollector        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Collection Orchestrator             │
│  APScheduler • Health Monitoring         │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         PostgreSQL Database              │
│  6 New Tables for 4 Ledgers + Metadata  │
└─────────────────────────────────────────┘
```

## Database Schema

### Glass Ledger

**protocol_fundamentals**
- TVL, fees, and revenue for DeFi protocols
- One entry per protocol per day
- Source: DeFiLlama API

**on_chain_metrics**
- Active addresses, transaction volumes, etc.
- Multiple metrics per asset
- Source: Glassnode, Santiment (scraped)

### Human Ledger

**news_sentiment**
- News articles with sentiment analysis
- Source: CryptoPanic, Newscatcher
- Unique URLs to prevent duplicates

**social_sentiment**
- Social media posts and sentiment
- Source: Reddit, Twitter/X
- Platform-specific data

### Catalyst Ledger

**catalyst_events**
- High-impact market events
- SEC filings, exchange listings, etc.
- Source: SEC API, CoinSpot announcements

### Metadata

**collector_runs**
- Execution history for all collectors
- Success/failure tracking
- Error messages for debugging

## Implemented Collectors

### DeFiLlama Collector (Glass Ledger)

**Status**: ✅ Complete  
**Schedule**: Daily at 2 AM UTC  
**Data**: TVL, fees, revenue for 20+ DeFi protocols  
**API**: Free, no authentication  

```python
from app.services.collectors.glass import DeFiLlamaCollector

collector = DeFiLlamaCollector()
data = await collector.run()
```

### CryptoPanic Collector (Human Ledger)

**Status**: ✅ Complete  
**Schedule**: Every 5 minutes  
**Data**: News headlines with sentiment  
**API**: Free tier (500 req/day)  
**Auth**: Requires API key  

```python
from app.services.collectors.human import CryptoPanicCollector

# Set CRYPTOPANIC_API_KEY environment variable
collector = CryptoPanicCollector()
data = await collector.run()
```

## Configuration

### Environment Variables

```bash
# CryptoPanic API (get free key at https://cryptopanic.com/developers/api/)
CRYPTOPANIC_API_KEY=your_api_key_here
```

### Starting Collectors

Collectors are automatically started during application startup:

```python
from app.services.collectors.config import setup_collectors, start_collection

# Register collectors with orchestrator
setup_collectors()

# Start scheduled collection
start_collection()
```

## API Endpoints

### Health Check

```http
GET /api/v1/collectors/health
```

Response:
```json
{
  "orchestrator_status": "running",
  "collector_count": 2,
  "collectors": [
    {
      "name": "defillama_api",
      "ledger": "glass",
      "status": "success",
      "last_run": "2025-11-16T02:00:00Z",
      "success_count": 45,
      "error_count": 0
    }
  ],
  "timestamp": "2025-11-16T10:30:00Z"
}
```

### Collector Status

```http
GET /api/v1/collectors/{collector_name}/status
```

### Manual Trigger

```http
POST /api/v1/collectors/{collector_name}/trigger
```

## Creating a New Collector

### 1. Choose Base Class

- **APICollector**: For HTTP APIs (REST, GraphQL)
- **ScraperCollector**: For web scraping (static or dynamic)

### 2. Implement Required Methods

```python
from app.services.collectors.api_collector import APICollector

class MyCollector(APICollector):
    def __init__(self):
        super().__init__(
            name="my_collector",
            ledger="glass",  # or human, catalyst, exchange
            base_url="https://api.example.com",
        )
    
    async def collect(self) -> list[dict[str, Any]]:
        """Fetch data from source"""
        return await self.fetch_json("/endpoint")
    
    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate and clean data"""
        # Filter invalid records
        return [item for item in data if self._is_valid(item)]
    
    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """Store data in database"""
        for item in data:
            session.add(MyModel(**item))
        session.commit()
        return len(data)
```

### 3. Register with Orchestrator

```python
from app.services.collectors.orchestrator import get_orchestrator

orchestrator = get_orchestrator()
collector = MyCollector()

# Schedule: interval
orchestrator.register_collector(
    collector,
    schedule_type="interval",
    minutes=5,
)

# Or schedule: cron
orchestrator.register_collector(
    collector,
    schedule_type="cron",
    hour=2,
    minute=0,
)
```

### 4. Write Tests

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_collect():
    collector = MyCollector()
    collector.fetch_json = AsyncMock(return_value={"data": "test"})
    
    data = await collector.collect()
    assert len(data) > 0
```

## Testing

### Run All Tests

```bash
cd backend
pytest tests/services/collectors/ -v
```

### Run Specific Collector Tests

```bash
pytest tests/services/collectors/glass/test_defillama.py -v
```

### Coverage Report

```bash
pytest tests/services/collectors/ --cov=app.services.collectors --cov-report=html
```

## Monitoring

### View Collector Status

```bash
# Health check
curl http://localhost:8000/api/v1/collectors/health

# Specific collector
curl http://localhost:8000/api/v1/collectors/defillama_api/status
```

### Check Logs

```bash
# Docker logs
docker compose logs -f backend | grep collector

# Database query for recent runs
psql -d app -c "SELECT * FROM collector_runs ORDER BY started_at DESC LIMIT 10;"
```

### Query Collected Data

```sql
-- Recent protocol TVL data
SELECT protocol, tvl_usd, collected_at 
FROM protocol_fundamentals 
WHERE collected_at > NOW() - INTERVAL '7 days'
ORDER BY tvl_usd DESC;

-- Recent news sentiment
SELECT title, sentiment, sentiment_score, published_at
FROM news_sentiment
WHERE collected_at > NOW() - INTERVAL '1 day'
ORDER BY published_at DESC;
```

## Troubleshooting

### Collector Not Running

1. Check orchestrator status: `GET /api/v1/collectors/health`
2. Verify collector is registered: Check `collectors` array
3. Check logs: `docker compose logs backend | grep orchestrator`

### API Rate Limits

- **Free APIs**: Respect rate limits (set `rate_limit_delay`)
- **CryptoPanic**: 500 req/day = ~1 req per 3 minutes
- **DeFiLlama**: No published limits, but be respectful

### Database Errors

- **Unique constraint violation**: URL already exists in `news_sentiment`
- **Type errors**: Ensure Decimal conversion for financial data
- **Missing data**: Check validation logic

## Next Steps

### Planned Collectors

1. **SEC API** (Catalyst Ledger) - Corporate filings
2. **CoinSpot Announcements** (Catalyst Ledger) - Listing detection
3. **Reddit API** (Human Ledger) - Social sentiment
4. **Enhanced CoinSpot** (Exchange Ledger) - Bid/ask/volume

### Future Enhancements

- Data retention policies
- Real-time WebSocket support
- Advanced sentiment analysis (NLP)
- Data quality scoring
- Alert system for catalyst events

## References

- [ROADMAP.md](../../ROADMAP.md) - Complete project roadmap
- [Comprehensive_Data_REQUIREMENTS.md](../../Comprehensive_Data_REQUIREMENTS.md) - Detailed requirements
- [Comprehensive_Data_ARCHITECTURE.md](../../Comprehensive_Data_ARCHITECTURE.md) - Technical architecture
- [Comprehensive_Data_IMPLEMENTATION_PLAN.md](../../Comprehensive_Data_IMPLEMENTATION_PLAN.md) - Implementation plan
