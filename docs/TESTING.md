# Testing Guide

**Last Updated:** 2026-01-10  
**Current Status:** 192 passing tests, 3 failures, 0 errors (Track A domain)

---

## Quick Start

### Run All Tests
```bash
cd backend
source .venv/bin/activate
pytest --tb=short --quiet
```

### Run Specific Test Suites
```bash
# API tests
pytest tests/api/ -v

# Agent integration tests
pytest tests/services/agent/integration/ -v

# Trading system tests
pytest tests/services/trading/ -v

# Collectors
pytest tests/services/collectors/ -v
```

### Test Configuration
- **Config File:** `backend/pytest.ini`
- **Markers:** `integration`, `slow`, `requires_api`, `unit`, `smoke`
- **Coverage:** Run with `bash scripts/test.sh` for coverage report

---

## Test Patterns

### Database Testing with PostgreSQL

**✅ CORRECT - Use PostgreSQL for tests**
```python
# Use the shared session fixture from tests/conftest.py
def test_my_feature(session: Session):
    # This session connects to actual PostgreSQL (via Docker)
    # It includes proper transaction isolation and cleanup
    pass
```

**❌ INCORRECT - Don't use SQLite with PostgreSQL-specific types**
```python
# This will fail with models using ARRAY, JSONB, etc.
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")  # ❌ Won't work
    SQLModel.metadata.create_all(engine)  # Fails on ARRAY columns
```

**Why?** 
- Sprint 2.5 introduced PostgreSQL-specific types (`ARRAY(String)`) for currency fields
- SQLite doesn't support these types
- Test fixtures must match production database type

**Best Practice:**
- Use the shared `session` fixture from `tests/conftest.py`
- It provides PostgreSQL connection with proper isolation
- Automatic cleanup between tests via savepoints

**Example: Custom fixture with test data**
```python
# For tests that need pre-populated data
@pytest.fixture(name="db")
def db_fixture(session: Session):
    """Create test data in PostgreSQL session.
    
    Uses the shared session fixture from conftest.py which provides:
    - PostgreSQL database connection (supports ARRAY types)
    - Transaction isolation via savepoints
    - Automatic cleanup after each test
    """
    # Create test data
    user = User(email="test@example.com", hashed_password="hashed")
    session.add(user)
    session.flush()  # Use flush(), not commit() to preserve savepoint
    session.refresh(user)
    
    # Store IDs for tests
    session.user_id = user.id  # type: ignore[attr-defined]
    return session
```

**Important: Use flush(), not commit()**
- The shared `session` fixture uses savepoints for transaction isolation
- Calling `commit()` breaks out of the savepoint and causes isolation issues
- Use `flush()` to write to the database while staying within the transaction
- The savepoint is automatically rolled back after each test

**Foreign Key Constraints**
- PostgreSQL enforces foreign key constraints (unlike SQLite)
- Tests must create required parent records before creating child records
- Example: Create User before creating AgentSession

```python
# ✅ CORRECT - Create user first
@pytest.fixture
def user_id(db: Session):
    user = User(email="test@example.com", hashed_password="hashed")
    db.add(user)
    db.flush()  # Flush without committing
    return user.id

# Then use user_id in tests that create agent sessions
async def test_agent_session(db: Session, user_id: uuid.UUID):
    session = await session_manager.create_session(db, user_id, ...)
```

### Async Mock for Context Managers
```python
from unittest.mock import MagicMock, AsyncMock

# ✅ CORRECT - Use MagicMock for the callable
mock_session.post = MagicMock(return_value=mock_response)
mock_response.__aenter__ = AsyncMock(return_value=mock_response)
mock_response.__aexit__ = AsyncMock(return_value=None)
```

### Agent Testing
```python
@pytest.mark.asyncio
async def test_agent_workflow(db: Session, orchestrator: AgentOrchestrator):
    # Use session_manager methods directly in async tests
    state = await session_manager.get_session_state(session_id)
```

---

## Known Issues & Workarounds

### Issue: SQLModel Relationship Collections
**Problem:** Cannot use `list["Model"]` in Relationship()  
**Workaround:** Use unidirectional relationships + explicit queries
```python
# Get related records
positions = session.exec(select(Position).where(Position.user_id == user.id)).all()
```

### ✅ RESOLVED: PnL Test Fixture (Sprint 2.6)
**Problem:** SQLite fixture couldn't handle PostgreSQL ARRAY types  
**Solution:** Removed local SQLite fixture, now uses shared PostgreSQL session from conftest.py  
**Result:** 21/21 PnL tests now passing  
**Impact:** Does not block development  
**Workaround:** Skip with `pytest -k "not pnl"`

### Issue: Agent Security Tests (4 errors)  
**Status:** Redis connection configuration  
**Impact:** Performance tests only  
**Workaround:** Tests pass with proper Redis setup

---

## Test Coverage Goals

**Current:** ~85% coverage  
**Target:** 90% coverage by end of Phase 3

**Priority Areas:**
1. Agent workflow edge cases
2. Trading safety manager scenarios
3. Collector error handling
4. API authentication paths

---

## Load Testing Patterns (Sprint 2.12)

### Rate Limiting Load Tests

Performance testing for rate limiting middleware using k6:

```bash
# Quick smoke test
cd backend/tests/performance
k6 run --duration 2m --vus 10 load_test_rate_limiting.js

# Full test suite (all scenarios)
k6 run load_test_rate_limiting.js

# High concurrency test
k6 run --vus 200 --duration 5m load_test_rate_limiting.js

# Test against staging
BASE_URL=https://staging.example.com k6 run load_test_rate_limiting.js
```

**Test Scenarios:**
1. **Per-Minute Limit**: 60 req/min for normal users
2. **Per-Hour Limit**: 1000 req/hour for normal users  
3. **Admin Multiplier**: 5x limits (300 req/min, 10000 req/hour)
4. **Concurrent Users**: 100 concurrent users
5. **Redis Performance**: Target <10ms latency under 1000 req/min

**Success Criteria:**
- Response time p(95) < 500ms
- Response time p(99) < 1000ms
- Redis latency p(95) < 100ms
- Rate limit headers present on all responses
- 429 responses include Retry-After header

See [Performance Tests README](../backend/tests/performance/README.md) for detailed documentation.

---

## Historical Test Reports

Detailed sprint test reports archived in `docs/archive/history/`:
- Sprint 2.5 (Jan 2026): Critical schema fixes, agent orchestrator integration
