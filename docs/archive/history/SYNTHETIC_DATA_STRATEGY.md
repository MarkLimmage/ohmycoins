# Synthetic Data Strategy for Oh My Coins

## Overview

This document outlines the strategy for populating the development environment database with data to enable comprehensive end-to-end testing of all system functions.

## Data Classification

We categorize data into two types:

### 1. **Real Public Data** (Collected from APIs)
Data that is publicly available and can be collected from external sources:

- **Price Data** - Collected from Coinspot Public API
  - Current spot prices for all cryptocurrencies
  - Bid/ask spreads
  - Updates every 5 minutes (when collector runs)
  
- **DeFi Protocol Data** - Collected from DeFiLlama API
  - Total Value Locked (TVL)
  - Protocol rankings
  - Multi-chain data
  
- **News Sentiment** - Collected from CryptoPanic API
  - Cryptocurrency news articles
  - Community sentiment scores
  - Tagged currencies
  
### 2. **Synthetic User Data** (Generated)
Data that is user-specific or not publicly available:

- **Users** - Test user accounts with varying profiles
- **Positions** - User cryptocurrency holdings
- **Orders** - Trading order history
- **Algorithms** - User-created trading algorithms
- **Deployed Algorithms** - Active algorithm deployments
- **Agent Sessions** - AI agent interaction history
- **Agent Artifacts** - Generated models and reports

## Implementation

### Data Seeding Script

Location: `/backend/app/utils/seed_data.py`

**Key Features:**
- Mix of real API data collection and synthetic data generation
- Configurable via command-line arguments
- Reproducible with fixed random seeds for testing
- Async support for API calls
- Batch processing for efficiency

### Usage

```bash
# Full seeding with real data
python -m app.utils.seed_data --all

# Custom configuration
python -m app.utils.seed_data --users 20 --algorithms 30

# Skip real data collection (faster for testing)
python -m app.utils.seed_data --all --no-real-data

# Clear all data
python -m app.utils.seed_data --clear
```

### Test Fixtures

Location: `/backend/app/utils/test_fixtures.py`

**Purpose:** Provide reusable test data fixtures optimized for unit and integration tests.

**Available Fixtures:**
- `test_user` - Creates a standard test user
- `test_superuser` - Creates a test superuser
- `test_price_data` - Creates 50 price data points
- `test_algorithm` - Creates a test algorithm

**Usage in Tests:**
```python
def test_create_order(db: Session, test_user: User, test_price_data):
    # Test user and price data are automatically created
    order = create_order(db, user=test_user, coin_type="BTC")
    assert order.user_id == test_user.id
```

## Data Sources

### Real Data APIs

1. **Coinspot Public API**
   - Endpoint: `https://www.coinspot.com.au/pubapi/v2/latest`
   - Rate Limit: No authentication required
   - Data: Real-time cryptocurrency prices
   
2. **DeFiLlama API**
   - Endpoint: `https://api.llama.fi/protocols`
   - Rate Limit: Free, no key required
   - Data: Protocol TVL and rankings
   
3. **CryptoPanic API**
   - Endpoint: `https://cryptopanic.com/api/v1/posts/`
   - Rate Limit: Free tier available
   - Data: Cryptocurrency news with sentiment

### Synthetic Data Generation

Uses the `Faker` library to generate:
- Realistic user names and emails
- Trading activity patterns
- Algorithm descriptions
- Agent session conversations

## Maintenance Strategy

### Keeping Data Fresh

#### Option 1: Manual Updates
Run the seeding script periodically to refresh data:

```bash
# Weekly data refresh
python -m app.utils.seed_data --clear
python -m app.utils.seed_data --all
```

#### Option 2: Automated Collection
Set up a cron job or scheduled task to collect real data:

```bash
# Add to crontab (every 6 hours)
0 */6 * * * cd /path/to/backend && python -m app.utils.seed_data --all --no-synthetic
```

#### Option 3: Development Script
Add to `docker-compose.override.yml`:

```yaml
services:
  data-seeder:
    build: ./backend
    command: python -m app.utils.seed_data --all
    depends_on:
      - db
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

### Handling Schema Changes

When the data model changes:

1. **Update the seeding script**
   - Modify `/backend/app/utils/seed_data.py`
   - Add functions for new models
   - Update `seed_all_async()` to include new data types

2. **Update test fixtures**
   - Add new fixture functions in `/backend/app/utils/test_fixtures.py`
   - Create helper functions for new models

3. **Run migrations first**
   ```bash
   alembic upgrade head
   python -m app.utils.seed_data --all
   ```

4. **Update documentation**
   - Add new data types to this document
   - Update examples and usage instructions

### Example: Adding a New Model

If you add a `Backtest` model:

1. Create generation function:
```python
def generate_backtests(session: Session, algorithms: list[Algorithm]) -> int:
    """Generate backtest results for algorithms."""
    count = 0
    for algo in algorithms:
        backtest = Backtest(
            algorithm_id=algo.id,
            # ... other fields
        )
        session.add(backtest)
        count += 1
    session.commit()
    return count
```

2. Add to `seed_all_async()`:
```python
async def seed_all_async(...):
    # ... existing code
    algorithms = generate_algorithms(session, users, algorithm_count)
    generate_backtests(session, algorithms)  # NEW
    # ... rest of code
```

3. Add test fixture:
```python
def create_test_backtest(session: Session, algorithm: Algorithm, **kwargs) -> Backtest:
    """Create a test backtest."""
    # implementation
```

## Integration with Testing

### Unit Tests
Use test fixtures for isolated testing:

```python
from app.utils.test_fixtures import create_test_user, create_test_algorithm

def test_algorithm_validation(db: Session):
    user = create_test_user(db)
    algo = create_test_algorithm(db, user, status="draft")
    assert algo.status == "draft"
```

### Integration Tests
Use the full seeding script to populate data:

```python
@pytest.fixture(scope="session", autouse=True)
def seed_test_database(db: Session):
    """Seed the test database once per test session."""
    import asyncio
    from app.utils.seed_data import seed_all_async
    
    asyncio.run(seed_all_async(
        db,
        user_count=5,
        collect_real_data=False,  # Faster for tests
        algorithm_count=10,
    ))
```

### End-to-End Tests
Use full dataset with real data:

```bash
# Setup E2E test environment
docker-compose up -d
python -m app.utils.seed_data --all
pytest tests/e2e/
```

## Performance Considerations

### Seeding Time

- **Synthetic data only**: ~5-10 seconds for full dataset
- **With real data collection**: ~30-60 seconds (depends on API response times)
- **Large datasets**: Use batch commits (implemented every 1000 records)

### Database Size

Typical dev environment data:
- 10 users
- ~10,000 price records (7 days, 5-min intervals, 10 coins)
- ~100 news articles
- ~20 agent sessions
- ~15 algorithms
- ~50 positions/orders

Total: **~2-5 MB** of test data

### Optimization Tips

1. **Use `--no-real-data` for fast iteration**
   ```bash
   python -m app.utils.seed_data --all --no-real-data
   ```

2. **Reduce data volume for unit tests**
   ```bash
   python -m app.utils.seed_data --users 3 --algorithms 5
   ```

3. **Use fixtures instead of full seeding in unit tests**
   ```python
   def test_feature(test_user, test_algorithm):
       # Only creates what's needed
   ```

## Data Validation

### Checking Data Quality

Run validation queries after seeding:

```python
from sqlmodel import Session, select, func
from app.models import User, PriceData5Min, Algorithm

with Session(engine) as session:
    # Check user count
    user_count = session.exec(select(func.count(User.id))).one()
    print(f"Users: {user_count}")
    
    # Check price data coverage
    price_count = session.exec(select(func.count(PriceData5Min.id))).one()
    print(f"Price records: {price_count}")
    
    # Check algorithm distribution
    algo_counts = session.exec(
        select(Algorithm.status, func.count(Algorithm.id))
        .group_by(Algorithm.status)
    ).all()
    print(f"Algorithms by status: {dict(algo_counts)}")
```

### Data Integrity Checks

The seeding script includes:
- Foreign key validation (SQLModel/SQLAlchemy handles this)
- Data type validation (Pydantic models)
- Constraint validation (unique keys, check constraints)
- Relationship integrity (cascading deletes)

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Use `--no-real-data` flag
   - Add delays between API calls
   - Use cached data

2. **Database Connection Errors**
   - Check `DATABASE_URL` environment variable
   - Ensure PostgreSQL is running
   - Verify network connectivity

3. **Foreign Key Violations**
   - Run `alembic upgrade head` first
   - Clear data before reseeding: `--clear` flag
   - Check model relationships

4. **Slow Seeding**
   - Reduce data volume
   - Use `--no-real-data`
   - Check database indexes
   - Use batch commits

### Debug Mode

Add verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run seeding with debug output
```

## Future Enhancements

### Planned Improvements

1. **Historical Price Data**
   - Integrate with paid APIs (CoinGecko, Messari) for historical data
   - Backfill multiple months of price history

2. **On-Chain Metrics**
   - Scrape Glassnode/Santiment public dashboards
   - Add blockchain-specific metrics

3. **Social Sentiment**
   - Reddit API integration
   - Twitter/X API integration (if available)

4. **Automated Refresh**
   - Background service to continuously collect real data
   - Delta updates instead of full refresh

5. **Data Versioning**
   - Tag datasets by version
   - Allow rollback to previous states
   - Compare datasets across versions

## Conclusion

This strategy provides a comprehensive approach to dev environment data:

✅ **Mix of real and synthetic data** for realism and privacy
✅ **Easy to maintain** as the schema evolves
✅ **Integrated with testing** through fixtures
✅ **Well-documented** with clear examples
✅ **Performant** with optimizations for different use cases

For questions or improvements, see the development team or update this document.
