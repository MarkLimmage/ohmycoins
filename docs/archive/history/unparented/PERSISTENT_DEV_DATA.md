# Persistent Dev Data Store

## Overview

The Oh My Coins project includes a **persistent dev data store** that automatically seeds your development database with realistic test data and provides utilities for managing database state across development sessions.

This system ensures:
- ✅ **Automatic seeding** on first startup
- ✅ **Persistent storage** across container restarts
- ✅ **Snapshot/restore** capabilities
- ✅ **Quick reset** to fresh state
- ✅ **Team collaboration** via shared snapshots

## Quick Start

### First-Time Setup

1. **Start the environment** (database will auto-seed):
   ```bash
   docker-compose up -d
   ```

2. **Verify data was created**:
   ```bash
   docker compose exec backend python -c "
   from sqlmodel import Session, select, func
   from app.core.db import engine
   from app.models import User, Algorithm, PriceData5Min
   
   with Session(engine) as session:
       users = session.exec(select(func.count(User.id))).one()
       algos = session.exec(select(func.count(Algorithm.id))).one()
       prices = session.exec(select(func.count(PriceData5Min.id))).one()
       print(f'✓ Users: {users}')
       print(f'✓ Algorithms: {algos}')
       print(f'✓ Price records: {prices}')
   "
   ```

3. **Access your environment**:
   - API Documentation: http://localhost:8000/docs
   - Frontend Dashboard: http://localhost:5173
   - Database Admin (Adminer): http://localhost:8080

### Default Credentials

- **Email**: `admin@example.com`
- **Password**: Check `.env` file for `FIRST_SUPERUSER_PASSWORD`

## Architecture

### Data Persistence

The development database uses Docker volumes to persist data:
- **Volume**: `app-db-data` (defined in `docker-compose.yml`)
- **Mount point**: `/var/lib/postgresql/data/pgdata`
- **Behavior**: Data survives `docker-compose down` and `docker-compose up`

### Automatic Seeding

On first startup, the `db-init` service:
1. Waits for database to be healthy
2. Checks if database is empty (no users)
3. If empty, runs seeding script with configured parameters
4. Creates realistic dev data combining real API data + synthetic users

**Configuration** (in `.env`):
```bash
AUTO_SEED_DB=true                    # Enable/disable auto-seeding
SEED_USER_COUNT=10                   # Number of test users
SEED_ALGORITHM_COUNT=15              # Number of trading algorithms
SEED_AGENT_SESSION_COUNT=20          # Number of AI agent sessions
SEED_COLLECT_REAL_DATA=true          # Fetch real price/DeFi/news data
```

## Common Workflows

### 1. Reset to Fresh State

**Quick reset** (with confirmation):
```bash
./scripts/db-reset.sh
```

**Skip confirmation**:
```bash
./scripts/db-reset.sh -y
```

**Fast reset** (no API calls):
```bash
./scripts/db-reset.sh --no-real-data
```

**Custom data volume**:
```bash
./scripts/db-reset.sh --users 20 --algorithms 30 --agent-sessions 50
```

### 2. Create Database Snapshot

**Create snapshot with custom name**:
```bash
./scripts/db-snapshot.sh my-feature-snapshot
```

**Create snapshot with timestamp**:
```bash
./scripts/db-snapshot.sh  # Auto-generates: dev-snapshot-20250122-143022
```

Snapshots are stored in `./backups/` directory and are compressed with gzip.

### 3. Restore from Snapshot

**List available snapshots**:
```bash
ls -lh ./backups/
```

**Restore specific snapshot**:
```bash
./scripts/db-restore.sh my-feature-snapshot
```

⚠️ **Warning**: This completely replaces your current database!

### 4. Share Snapshots with Team

**Using Git LFS** (recommended for large snapshots):
```bash
# Setup Git LFS (one-time)
git lfs install
git lfs track "backups/*.sql.gz"
git add .gitattributes

# Add and commit snapshot
git add backups/stable-dev-snapshot.sql.gz
git commit -m "Add stable dev snapshot"
git push
```

**Manual sharing**:
```bash
# Copy snapshot to shared location
cp backups/my-snapshot.sql.gz /path/to/shared/drive/
```

### 5. Disable Auto-Seeding

Set in `.env`:
```bash
AUTO_SEED_DB=false
```

Then restart:
```bash
docker-compose restart db-init
```

## Manual Seeding

If you prefer manual control over seeding:

### Full Seeding (Real + Synthetic Data)
```bash
docker compose run --rm backend python -m app.utils.seed_data --all
```

### Fast Seeding (Synthetic Only)
```bash
docker compose run --rm backend python -m app.utils.seed_data --all --no-real-data
```

### Custom Configuration
```bash
docker compose run --rm backend python -m app.utils.seed_data \
  --users 25 \
  --algorithms 40 \
  --agent-sessions 100
```

### Clear All Data
```bash
docker compose run --rm backend python -m app.utils.seed_data --clear
```

## Data Contents

### Real Data (from Public APIs)

| Source | Data Type | Update Frequency |
|--------|-----------|------------------|
| **Coinspot** | Cryptocurrency prices | On seed/manual refresh |
| **DeFiLlama** | DeFi protocol TVL | On seed/manual refresh |
| **CryptoPanic** | News with sentiment | On seed/manual refresh |

### Synthetic Data (Generated)

| Model | Default Count | Description |
|-------|---------------|-------------|
| **Users** | 10 | Test user accounts with realistic profiles |
| **Algorithms** | 15 | Trading strategies with various configurations |
| **Positions** | ~50 | Open cryptocurrency positions |
| **Orders** | ~100 | Historical trading orders |
| **Agent Sessions** | 20 | AI agent interaction history |
| **Deployed Algorithms** | ~10 | Active algorithm deployments |
| **Price Data** | ~10,000 | 5-minute candles for 10 coins over 7 days |

**Total Database Size**: ~2-5 MB typical

## Troubleshooting

### Database Not Auto-Seeding

**Check if service ran**:
```bash
docker-compose logs db-init
```

**Manually trigger seeding**:
```bash
docker compose run --rm backend python -m app.utils.seed_data --all
```

**Verify AUTO_SEED_DB setting**:
```bash
grep AUTO_SEED_DB .env
```

### API Rate Limiting

If you hit rate limits during seeding:

```bash
# Use cached/synthetic data only
./scripts/db-reset.sh --no-real-data
```

Or set in `.env`:
```bash
SEED_COLLECT_REAL_DATA=false
```

### Database Connection Errors

**Check database is running**:
```bash
docker compose ps db
```

**Check database health**:
```bash
docker compose exec db pg_isready -U postgres -d app
```

**Restart database**:
```bash
docker compose restart db
```

### Snapshot/Restore Failures

**Ensure database is running**:
```bash
docker compose up -d db
```

**Check available disk space**:
```bash
df -h
```

**Verify snapshot integrity**:
```bash
gunzip -t backups/my-snapshot.sql.gz
```

### Performance Issues

**Reduce data volume** in `.env`:
```bash
SEED_USER_COUNT=5
SEED_ALGORITHM_COUNT=10
SEED_AGENT_SESSION_COUNT=10
```

**Skip real data collection**:
```bash
SEED_COLLECT_REAL_DATA=false
```

**Check database indexes**:
```bash
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
```

## Advanced Usage

### Development Profiles

Create named snapshots for different scenarios:

```bash
# Baseline snapshot (empty with migrations)
./scripts/db-reset.sh --users 0 --algorithms 0 --agent-sessions 0 --no-real-data
./scripts/db-snapshot.sh baseline

# Light dev snapshot (fast)
./scripts/db-reset.sh --users 5 --algorithms 5 --no-real-data
./scripts/db-snapshot.sh light-dev

# Full dev snapshot (realistic)
./scripts/db-reset.sh --users 15 --algorithms 30 --agent-sessions 50
./scripts/db-snapshot.sh full-dev

# Demo snapshot (rich data for presentations)
./scripts/db-reset.sh --users 25 --algorithms 50 --agent-sessions 100
./scripts/db-snapshot.sh demo
```

Then switch between them:
```bash
./scripts/db-restore.sh baseline
./scripts/db-restore.sh full-dev
./scripts/db-restore.sh demo
```

### Automated Scheduled Refresh

Add to crontab for periodic real data updates:

```bash
# Refresh real data every 6 hours (preserves user data)
0 */6 * * * cd /home/mark/omc/ohmycoins && docker compose run --rm backend python -c "
from app.utils.seed_data import collect_real_price_data, collect_real_defi_data, collect_real_news_data
from app.core.db import engine
from sqlmodel import Session
import asyncio

async def refresh():
    with Session(engine) as session:
        await collect_real_price_data(session)
        await collect_real_defi_data(session)
        await collect_real_news_data(session)
        session.commit()

asyncio.run(refresh())
"
```

### CI/CD Integration

For automated testing pipelines:

```yaml
# .github/workflows/test.yml
- name: Setup test database
  run: |
    docker-compose up -d db
    docker-compose run --rm backend python -m app.utils.seed_data --all --no-real-data

- name: Run tests
  run: docker compose run --rm backend pytest

- name: Create test snapshot (on failure)
  if: failure()
  run: ./scripts/db-snapshot.sh ci-failure-$(date +%Y%m%d-%H%M%S)
```

### Database Migrations

When schema changes:

1. **Create migration**:
   ```bash
   docker compose run --rm backend alembic revision --autogenerate -m "Add new field"
   ```

2. **Review migration**:
   ```bash
   cat backend/app/alembic/versions/*_add_new_field.py
   ```

3. **Apply migration**:
   ```bash
   docker compose run --rm backend alembic upgrade head
   ```

4. **Update seeding script** if needed:
   - Edit `backend/app/utils/seed_data.py`
   - Add generation logic for new fields/models

5. **Reset with updated schema**:
   ```bash
   ./scripts/db-reset.sh -y
   ```

## File Reference

### Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `db-snapshot.sh` | Create database backup | `/scripts/db-snapshot.sh` |
| `db-restore.sh` | Restore from backup | `/scripts/db-restore.sh` |
| `db-reset.sh` | Clear and re-seed | `/scripts/db-reset.sh` |

### Configuration

| File | Purpose |
|------|---------|
| `.env` | Environment variables for seeding config |
| `docker-compose.yml` | Defines `app-db-data` volume |
| `docker-compose.override.yml` | Defines `db-init` service |

### Data Generation

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/utils/seed_data.py` | Main seeding script | 634 |
| `backend/app/utils/test_fixtures.py` | Test data factories | 209 |

### Documentation

| File | Purpose |
|------|---------|
| `PERSISTENT_DEV_DATA.md` | This document |
| `SYNTHETIC_DATA_STRATEGY.md` | Overall data strategy |
| `SYNTHETIC_DATA_QUICKSTART.md` | Quick reference guide |
| `SYNTHETIC_DATA_IMPLEMENTATION_SUMMARY.md` | Implementation details |

## Best Practices

### For Individual Developers

1. **Start with auto-seeding enabled** - Let the system set up your environment
2. **Create snapshots before risky changes** - Easy rollback
3. **Use `--no-real-data` for speed** - When you don't need live prices
4. **Reset regularly** - Keep your dev environment clean

### For Teams

1. **Share baseline snapshots** - Ensure consistent starting state
2. **Document custom snapshots** - Add metadata files explaining snapshot purpose
3. **Use Git LFS for snapshots** - Version control without bloating repo
4. **Establish naming convention** - e.g., `{feature}-{date}-{purpose}.sql.gz`

### For Testing

1. **Use test fixtures for unit tests** - Faster than full database seeding
2. **Use snapshots for integration tests** - Known-good state
3. **Disable auto-seed in CI** - Explicit seeding in test setup
4. **Create failure snapshots** - Debugging aid when tests fail

## Migration from Legacy Setup

If you have existing manual seeding workflows:

### Before (Manual)
```bash
# Old way - manual every time
docker-compose up -d db
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.utils.seed_data --all
```

### After (Automatic)
```bash
# New way - automatic on first startup
docker-compose up -d
# Database is already seeded and ready!
```

### Transition Steps

1. **Create snapshot of current state** (backup):
   ```bash
   ./scripts/db-snapshot.sh pre-migration-backup
   ```

2. **Enable auto-seeding** in `.env`:
   ```bash
   AUTO_SEED_DB=true
   ```

3. **Test with fresh database**:
   ```bash
   docker compose down -v  # Remove volumes
   docker-compose up -d    # Auto-seeds
   ```

4. **Verify data**:
   ```bash
   docker compose exec backend python -c "from sqlmodel import Session, select, func; from app.core.db import engine; from app.models import User; print(Session(engine).exec(select(func.count(User.id))).one())"
   ```

5. **Rollback if needed**:
   ```bash
   ./scripts/db-restore.sh pre-migration-backup
   ```

## Performance Benchmarks

Typical seeding performance on standard developer laptop:

| Configuration | Time | Database Size |
|---------------|------|---------------|
| Synthetic only (minimal) | ~3-5s | ~1 MB |
| Synthetic only (default) | ~5-10s | ~2 MB |
| With real data (default) | ~30-60s | ~3-5 MB |
| Large dataset (50 users) | ~15-20s | ~5-8 MB |
| Demo dataset (100 users) | ~30-40s | ~10-15 MB |

Snapshot operations:

| Operation | Time | Notes |
|-----------|------|-------|
| Create snapshot | ~2-5s | Includes compression |
| Restore snapshot | ~3-8s | Includes decompression |
| Reset database | ~8-15s | Clear + re-seed |

## Support

### Getting Help

1. **Check logs**:
   ```bash
   docker-compose logs db-init
   docker-compose logs backend
   ```

2. **Verify environment**:
   ```bash
   cat .env | grep SEED_
   ```

3. **Test database connectivity**:
   ```bash
   docker compose exec db psql -U postgres -d app -c "SELECT version();"
   ```

### Common Issues

See **Troubleshooting** section above for solutions to:
- Database not auto-seeding
- API rate limiting
- Connection errors
- Snapshot/restore failures
- Performance issues

### Further Reading

- [Synthetic Data Strategy](./SYNTHETIC_DATA_STRATEGY.md) - Overall approach
- [Synthetic Data Quickstart](./SYNTHETIC_DATA_QUICKSTART.md) - Quick commands
- [Implementation Summary](./SYNTHETIC_DATA_IMPLEMENTATION_SUMMARY.md) - Technical details
- [seed_data.py](./backend/app/utils/seed_data.py) - Source code

## Changelog

### v1.0.0 - Initial Implementation (November 2025)

- ✅ Automatic database seeding on first startup
- ✅ Docker volume persistence
- ✅ Snapshot/restore utilities
- ✅ Quick reset script
- ✅ Configurable via environment variables
- ✅ Comprehensive documentation

### Future Enhancements

Planned improvements:
- [ ] Web UI for snapshot management
- [ ] Automated daily snapshots
- [ ] Snapshot versioning and tagging
- [ ] Cloud storage integration (S3, GCS)
- [ ] Database diff tool
- [ ] Performance profiling dashboard
