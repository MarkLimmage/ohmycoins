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

## Historical Test Reports

Detailed sprint test reports archived in `docs/archive/history/`:
- Sprint 2.5 (Jan 2026): Critical schema fixes, agent orchestrator integration
