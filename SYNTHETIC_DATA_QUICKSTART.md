# Synthetic Data Generation - Quick Start

## Overview

This system provides a comprehensive strategy for populating the dev environment with test data, combining **real data from public APIs** with **synthetic user-specific data**.

> 💡 **New!** Check out the [Persistent Dev Data Store](./PERSISTENT_DEV_DATA.md) for automatic database seeding, snapshots, and restore capabilities.

## Quick Commands

### Automatic Setup (Recommended)

```bash
# First-time setup: database auto-seeds on startup
docker-compose up -d

# Verify data
docker compose exec backend python -c "from sqlmodel import Session, select, func; from app.core.db import engine; from app.models import User; print(f'Users: {Session(engine).exec(select(func.count(User.id))).one()}')"
```

### Manual Seeding

```bash
# Navigate to backend directory
cd backend

# Full seeding with real data (recommended for dev)
python -m app.utils.seed_data --all

# Fast seeding with synthetic data only (for quick tests)
python -m app.utils.seed_data --all --no-real-data

# Custom configuration
python -m app.utils.seed_data --users 20 --algorithms 30 --agent-sessions 50

# Clear all data
python -m app.utils.seed_data --clear
```

### Database Management

```bash
# Reset to fresh seeded state
./scripts/db-reset.sh

# Create a snapshot
./scripts/db-snapshot.sh my-snapshot-name

# Restore from snapshot
./scripts/db-restore.sh my-snapshot-name
```

> 📚 **For detailed workflow guides**, see [Persistent Dev Data Store](./PERSISTENT_DEV_DATA.md)

## What Gets Created

### Real Data (from Public APIs)
- ✅ **Current cryptocurrency prices** from Coinspot
- ✅ **DeFi protocol data** (TVL, rankings) from DeFiLlama
- ✅ **News articles** with sentiment from CryptoPanic

### Synthetic Data (Generated)
- 👤 **Users** (default: 10) - Realistic user profiles
- 💹 **Algorithms** (default: 15) - Trading strategies
- 📊 **Positions & Orders** - Trading history
- 🤖 **Agent Sessions** (default: 20) - AI agent interactions
- 📦 **Deployed Algorithms** - Active algorithm deployments

## Integration with Tests

### Using Test Fixtures (Recommended for Unit Tests)

```python
from app.utils.test_fixtures import (
    create_test_user,
    create_test_algorithm,
    create_test_position,
)

def test_my_feature(db: Session):
    user = create_test_user(db)
    algo = create_test_algorithm(db, user, status="active")
    position = create_test_position(db, user, coin_type="BTC")
    
    # Your test code here
    assert position.user_id == user.id
```

### Available Fixtures

```python
# In conftest.py or test files
def test_with_fixtures(test_user, test_price_data, test_algorithm):
    # test_user: pre-created User
    # test_price_data: 50 price records
    # test_algorithm: pre-created Algorithm
    pass
```

## Data Maintenance

### When Schema Changes

1. **Run migrations first:**
   ```bash
   alembic upgrade head
   ```

2. **Update seeding script:**
   - Edit `app/utils/seed_data.py`
   - Add generation function for new models
   - Update `seed_all_async()`

3. **Update test fixtures:**
   - Edit `app/utils/test_fixtures.py`
   - Add fixture function for new models

4. **Re-seed database:**
   ```bash
   python -m app.utils.seed_data --clear
   python -m app.utils.seed_data --all
   ```

### Automated Refresh

Add to your development workflow:

```bash
# In docker-compose.override.yml
services:
  data-seeder:
    build: ./backend
    command: python -m app.utils.seed_data --all
    depends_on:
      - db
```

Or use a cron job:
```bash
# Refresh every 6 hours
0 */6 * * * cd /path/to/backend && python -m app.utils.seed_data --all
```

## Performance

- **Synthetic only**: ~5-10 seconds
- **With real data**: ~30-60 seconds
- **Database size**: ~2-5 MB typical

## Troubleshooting

### API Rate Limiting
```bash
# Skip real data collection
python -m app.utils.seed_data --all --no-real-data
```

### Database Errors
```bash
# Ensure migrations are current
alembic upgrade head

# Clear and re-seed
python -m app.utils.seed_data --clear
python -m app.utils.seed_data --all
```

### Slow Performance
```bash
# Reduce data volume
python -m app.utils.seed_data --users 5 --algorithms 10

# Or use synthetic data only
python -m app.utils.seed_data --all --no-real-data
```

## Documentation

- **Persistent Dev Data**: See [PERSISTENT_DEV_DATA.md](./PERSISTENT_DEV_DATA.md) for automatic seeding, snapshots, and restore workflows
- **Full Strategy**: See [SYNTHETIC_DATA_STRATEGY.md](./SYNTHETIC_DATA_STRATEGY.md) for overall approach and architecture
- **Implementation Details**: See [SYNTHETIC_DATA_IMPLEMENTATION_SUMMARY.md](./SYNTHETIC_DATA_IMPLEMENTATION_SUMMARY.md) for technical documentation
- **Code**: `app/utils/seed_data.py`
- **Test Fixtures**: `app/utils/test_fixtures.py`
- **Tests**: `tests/utils/test_seed_data.py`

## Examples

### Seed for E2E Testing

```bash
# Full realistic dataset
python -m app.utils.seed_data --all --users 20 --algorithms 30
```

### Seed for Unit Testing

```python
# Use fixtures in tests
from app.utils.test_fixtures import create_test_user

def test_feature(db):
    user = create_test_user(db, email="test@example.com")
    # Test your feature
```

### Seed for Integration Testing

```bash
# Medium dataset with real data
python -m app.utils.seed_data --all --users 10
```

### Seed for Demo/Presentation

```bash
# Rich dataset for demonstrations
python -m app.utils.seed_data --all --users 15 --algorithms 25 --agent-sessions 30
```

## Data Sources

- **Coinspot**: https://www.coinspot.com.au/pubapi/v2/latest
- **DeFiLlama**: https://api.llama.fi/protocols
- **CryptoPanic**: https://cryptopanic.com/api/v1/posts/

All free tier, no API keys required (though CryptoPanic has rate limits).

## Next Steps

1. Run initial seeding: `python -m app.utils.seed_data --all`
2. Verify data: Check database or API at http://localhost:8000/docs
3. Use in tests: Import fixtures from `app.utils.test_fixtures`
4. Maintain: Update when schema changes

For detailed information, see `SYNTHETIC_DATA_STRATEGY.md`.
