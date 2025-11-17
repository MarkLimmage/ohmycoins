# Phase 2.5 Collectors - Troubleshooting Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-17

---

## Quick Diagnosis

Run this command to check overall system health:

```bash
cd backend
uv run python -c "
from app.services.collectors.orchestrator import get_orchestrator
from app.services.collectors.quality_monitor import get_quality_monitor
from app.services.collectors.metrics import get_metrics_tracker
from sqlmodel import create_engine, Session
import asyncio

async def diagnose():
    # Check orchestrator
    orch = get_orchestrator()
    print('=== Orchestrator Status ===')
    print(f'Running: {orch.is_running}')
    print(f'Collectors: {len(orch._collectors)}')
    
    # Check metrics
    tracker = get_metrics_tracker()
    print('\n=== Metrics Summary ===')
    summary = tracker.get_summary()
    for key, value in summary.items():
        print(f'{key}: {value}')
    
    print('\n=== Health Status ===')
    health = tracker.get_health_status()
    for key, value in health.items():
        print(f'{key}: {value}')
    
    # Check quality (requires database)
    # monitor = get_quality_monitor()
    # metrics = await monitor.check_all(session)
    # print(f'\nQuality Score: {metrics.overall_score:.2f}')

asyncio.run(diagnose())
"
```

---

## Problem Categories

1. [Collector Not Running](#collector-not-running)
2. [Data Not Being Collected](#data-not-being-collected)
3. [API/Network Errors](#apinetwork-errors)
4. [Database Issues](#database-issues)
5. [Performance Problems](#performance-problems)
6. [Quality Issues](#quality-issues)

---

## Collector Not Running

### Symptoms
- Orchestrator shows collector is not registered
- No scheduled jobs for collector
- Collector never executes

### Diagnosis

```python
from app.services.collectors.orchestrator import get_orchestrator

orch = get_orchestrator()

# Check if collector is registered
collectors = orch._collectors
print(f"Registered collectors: {list(collectors.keys())}")

# Check specific collector
collector_name = "reddit_api"
if collector_name in collectors:
    print(f"{collector_name} is registered")
else:
    print(f"{collector_name} is NOT registered")
```

### Solutions

#### 1. Collector Not Registered

**Cause:** Collector not added to config.py

**Fix:**
```python
# In backend/app/services/collectors/config.py

from app.services.collectors.human import RedditCollector

def setup_collectors():
    orchestrator = get_orchestrator()
    
    # Add this section
    reddit = RedditCollector()
    orchestrator.register_collector(
        reddit,
        schedule_type="interval",
        minutes=15,
    )
```

#### 2. Orchestrator Not Started

**Cause:** `start_collection()` not called

**Fix:**
```python
# In your application startup (e.g., main.py)

from app.services.collectors.config import setup_collectors, start_collection

@app.on_event("startup")
async def startup():
    setup_collectors()
    start_collection()  # Make sure this is called!
```

#### 3. Import Errors

**Cause:** Collector class not properly exported

**Fix:**
```python
# In backend/app/services/collectors/human/__init__.py

from .reddit import RedditCollector

__all__ = ["CryptoPanicCollector", "RedditCollector"]
```

---

## Data Not Being Collected

### Symptoms
- Collector runs but no data in database
- Success reported but record count is 0
- Old data but no new data

### Diagnosis

```python
from sqlmodel import Session, select, func
from app.models import NewsSentiment
from datetime import datetime, timedelta, timezone

# Check if any data exists
with Session(engine) as session:
    count = session.exec(select(func.count(NewsSentiment.id))).one()
    print(f"Total sentiment records: {count}")
    
    # Check recent data
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent = session.exec(
        select(func.count(NewsSentiment.id))
        .where(NewsSentiment.collected_at > yesterday)
    ).one()
    print(f"Records from last 24h: {recent}")
```

### Solutions

#### 1. External API Returns Empty Data

**Cause:** API has no data for the timeframe/query

**Fix:**
- Adjust date filters in collector
- Verify API query parameters
- Check API documentation

**Example:**
```python
# In Reddit collector, increase post limit
params = {
    "limit": 50,  # Increase from 25 to 50
    "raw_json": 1,
}
```

#### 2. Data Validation Filters Out Everything

**Cause:** Validation rules too strict

**Diagnosis:**
```python
# Add logging to validate_data method
async def validate_data(self, data):
    logger.info(f"Validating {len(data)} records")
    validated = []
    
    for item in data:
        if not item.get("title"):
            logger.warning(f"Rejected: Missing title")
            continue
        # ... more validation
        
        validated.append(item)
    
    logger.info(f"Validated {len(validated)}/{len(data)} records")
    return validated
```

**Fix:**
- Review validation logic
- Adjust required fields
- Add logging to see what's being rejected

#### 3. Time Zone Issues

**Cause:** Date filters exclude recent data due to timezone mismatch

**Fix:**
```python
# Always use UTC
from datetime import timezone

now = datetime.now(timezone.utc)
cutoff = now - timedelta(days=30)
```

#### 4. Database Transaction Not Committed

**Cause:** Missing `session.commit()`

**Fix:**
```python
async def store_data(self, data, session):
    for item in data:
        model = NewsSentiment(**item)
        session.add(model)
    
    session.commit()  # Don't forget this!
    return len(data)
```

---

## API/Network Errors

### Symptoms
- Timeout errors
- Connection refused
- 403/429 HTTP errors
- SSL certificate errors

### Diagnosis

```python
from app.services.collectors.metrics import get_metrics_tracker

tracker = get_metrics_tracker()
metrics = tracker.get_collector_metrics("reddit_api")

print(f"Failed runs: {metrics.failed_runs}")
print(f"Last error: {metrics.last_error}")
print(f"Last failure: {metrics.last_failure_at}")
```

### Solutions

#### 1. Timeout Errors

**Cause:** Network latency or slow API

**Fix:**
```python
# In collector __init__
super().__init__(
    name="reddit_api",
    base_url="https://www.reddit.com",
    timeout=60,  # Increase from 30 to 60
    max_retries=5,  # Increase retries
    rate_limit_delay=3.0,  # Increase delay
)
```

#### 2. Rate Limiting (429 errors)

**Cause:** Too many requests to API

**Fix:**
```python
# Increase delay between requests
self.rate_limit_delay = 5.0  # 5 seconds between requests

# Or adjust collection schedule
orchestrator.register_collector(
    collector,
    schedule_type="interval",
    minutes=30,  # Reduce from every 15 minutes
)
```

#### 3. Authentication Errors (403)

**Cause:** Missing or invalid API key

**Fix:**
```bash
# Set environment variable
export CRYPTOPANIC_API_KEY=your_actual_key_here

# Verify it's set
echo $CRYPTOPANIC_API_KEY
```

#### 4. User-Agent Blocked

**Cause:** Default user-agent is blocked

**Fix:**
```python
# Set custom user-agent
headers = {
    "User-Agent": "OhMyCoins/1.0 (contact@example.com)",
}

response = await self.fetch_json(url, headers=headers)
```

#### 5. SSL Certificate Errors

**Cause:** Certificate verification issues

**Fix (temporary, for testing only):**
```python
import aiohttp

async with aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(ssl=False)  # Only for testing!
) as session:
    # ...
```

**Better fix:** Update certificates:
```bash
pip install --upgrade certifi
```

---

## Database Issues

### Symptoms
- "relation does not exist" errors
- Foreign key constraint violations
- Connection pool exhausted
- Data type mismatch errors

### Diagnosis

```bash
# Check database is running
docker compose ps db

# Check migrations
cd backend
uv run alembic current

# Check for pending migrations
uv run alembic heads
```

### Solutions

#### 1. Missing Tables

**Cause:** Migrations not run

**Fix:**
```bash
cd backend
uv run alembic upgrade head
```

#### 2. Schema Mismatch

**Cause:** Model doesn't match database schema

**Diagnosis:**
```bash
# Generate new migration
uv run alembic revision --autogenerate -m "Fix schema"

# Review the generated migration
cat app/alembic/versions/XXXXX_fix_schema.py

# Apply if correct
uv run alembic upgrade head
```

#### 3. Connection Pool Exhausted

**Cause:** Too many open connections

**Fix:**
```python
# In database configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase pool size
    max_overflow=40,  # Increase overflow
    pool_pre_ping=True,  # Check connections
)
```

#### 4. Duplicate Key Violations

**Cause:** Trying to insert duplicate records

**Fix:**
```python
# Add unique constraint handling
try:
    session.add(record)
    session.commit()
except IntegrityError:
    session.rollback()
    logger.debug(f"Duplicate record, skipping")
```

---

## Performance Problems

### Symptoms
- Slow collector execution
- High latency
- Memory usage growing
- CPU usage high

### Diagnosis

```python
from app.services.collectors.metrics import get_metrics_tracker

tracker = get_metrics_tracker()
metrics = tracker.get_collector_metrics("reddit_api")

print(f"Average latency: {metrics.average_latency:.2f}s")
print(f"Total runs: {metrics.total_runs}")
print(f"Average records/run: {metrics.average_records_per_run:.2f}")
```

### Solutions

#### 1. Slow Database Queries

**Cause:** Missing indexes

**Fix:**
```sql
-- Add indexes for common queries
CREATE INDEX idx_news_sentiment_collected_at 
ON news_sentiment(collected_at DESC);

CREATE INDEX idx_catalyst_events_event_date 
ON catalyst_events(event_date DESC);

CREATE INDEX idx_price_data_timestamp 
ON price_data_5min(timestamp DESC);
```

#### 2. Large Dataset Processing

**Cause:** Processing too much data at once

**Fix:**
```python
# Process in batches
BATCH_SIZE = 100

for i in range(0, len(data), BATCH_SIZE):
    batch = data[i:i + BATCH_SIZE]
    await self.store_data(batch, session)
    session.commit()  # Commit each batch
```

#### 3. Memory Leaks

**Cause:** Sessions not properly closed

**Fix:**
```python
# Always use context manager
with Session(engine) as session:
    # Use session
    pass
# Session automatically closed

# Or in async
async with AsyncSession(engine) as session:
    # Use session
    pass
```

#### 4. Concurrent Collection Issues

**Cause:** Multiple collectors blocking each other

**Fix:**
```python
# Use different database connections per collector
# Already handled by orchestrator

# Or increase pool size
engine = create_engine(
    DATABASE_URL,
    pool_size=30,  # One per collector + overhead
)
```

---

## Quality Issues

### Symptoms
- Low quality scores
- Many quality alerts
- Inconsistent data
- Missing fields

### Diagnosis

```python
from app.services.collectors.quality_monitor import get_quality_monitor

monitor = get_quality_monitor()
metrics = await monitor.check_all(session)

print(f"Overall score: {metrics.overall_score:.2f}")
print(f"Completeness: {metrics.completeness_score:.2f}")
print(f"Timeliness: {metrics.timeliness_score:.2f}")
print(f"Accuracy: {metrics.accuracy_score:.2f}")

print("\nIssues:")
for issue in metrics.issues:
    print(f"  - {issue}")

print("\nWarnings:")
for warning in metrics.warnings:
    print(f"  - {warning}")
```

### Solutions

#### 1. Stale Data (Low Timeliness)

**Cause:** Collector not running frequently enough

**Fix:**
```python
# Increase collection frequency
orchestrator.register_collector(
    collector,
    schedule_type="interval",
    minutes=10,  # More frequent
)
```

#### 2. Missing Data (Low Completeness)

**Cause:** Collectors failing or not registered

**Fix:**
- Check all collectors are registered
- Verify collectors are running
- Check for errors in failed collectors

#### 3. Invalid Data (Low Accuracy)

**Cause:** Data validation not strict enough

**Fix:**
```python
# Add more validation
async def validate_data(self, data):
    validated = []
    for item in data:
        # Check required fields
        if not all(key in item for key in ['title', 'url']):
            continue
        
        # Check data ranges
        if item.get('sentiment_score'):
            score = float(item['sentiment_score'])
            if not -1.0 <= score <= 1.0:
                continue
        
        validated.append(item)
    return validated
```

---

## Emergency Procedures

### System Down

```bash
# 1. Stop orchestrator
pkill -f "app.services.collectors"

# 2. Check logs
tail -f logs/app.log

# 3. Restart database
docker compose restart db

# 4. Run migrations
cd backend && uv run alembic upgrade head

# 5. Restart application
# (depends on your deployment)
```

### Data Corruption

```bash
# 1. Stop collection
# (stop orchestrator)

# 2. Backup database
docker compose exec db pg_dump -U postgres dbname > backup.sql

# 3. Clean bad data
psql -U postgres -d dbname -c "
DELETE FROM news_sentiment WHERE sentiment_score > 1.0;
DELETE FROM catalyst_events WHERE event_date IS NULL;
"

# 4. Verify data quality
# Run quality monitor

# 5. Resume collection
# (restart orchestrator)
```

### Reset Everything

```bash
# Nuclear option - use with caution!

# 1. Stop all services
docker compose down

# 2. Remove volumes
docker compose down -v

# 3. Restart services
docker compose up -d

# 4. Run migrations
cd backend && uv run alembic upgrade head

# 5. Reset metrics
python -c "
from app.services.collectors.metrics import get_metrics_tracker
tracker = get_metrics_tracker()
tracker.reset_metrics()
"

# 6. Restart collection
# (start application)
```

---

## Getting Help

### Diagnostic Information to Provide

When asking for help, include:

1. **System Status:**
```bash
# Orchestrator status
python -c "from app.services.collectors.orchestrator import get_orchestrator; print(get_orchestrator().get_health_status())"

# Metrics summary
python -c "from app.services.collectors.metrics import get_metrics_tracker; import json; print(json.dumps(get_metrics_tracker().get_summary(), indent=2))"
```

2. **Recent Logs:**
```bash
tail -100 logs/app.log | grep -i error
```

3. **Database Status:**
```bash
docker compose ps db
docker compose exec db psql -U postgres -c "SELECT count(*) FROM news_sentiment;"
```

4. **Environment:**
```bash
python --version
docker --version
docker compose version
```

### Support Contacts

- **Documentation:** `PHASE25_DOCUMENTATION.md`
- **Developer Summary:** `DEVELOPER_A_SUMMARY.md`
- **Code Location:** `backend/app/services/collectors/`

---

**Version:** 1.0.0  
**Last Updated:** 2025-11-17
