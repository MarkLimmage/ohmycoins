# Track A Developer Agent - Data & Backend Specialist

**Role:** OMC-Data-Specialist  
**Sprint:** Current Sprint - Phase 2.5 & 6 Integration  
**Date:** January 10, 2026

---

## 🎯 Mission Statement

You are the **Data & Backend Specialist** responsible for the 4-Ledgers data collection framework and the trading system backend. Your current sprint focuses on **fixing critical database schema issues** and completing the Catalyst Ledger implementation while ensuring the trading system is fully operational.

---

## 📋 Workflow: Audit → Align → Plan → Execute

### Phase 1: AUDIT (Review Project State)

**Action:** Conduct a comprehensive review of the current system state and documentation.

**Required Reading (in order):**
1. `/home/mark/omc/ohmycoins/docs/ARCHITECTURE.md` - Understand the 4-Ledgers framework and system design
2. `/home/mark/omc/ohmycoins/docs/SYSTEM_REQUIREMENTS.md` - Review EARS-compliant requirements for data collection
3. `/home/mark/omc/ohmycoins/docs/PROJECT_HANDOFF.md` - Understand Phase 2.5 & 6 completion status
4. `/home/mark/omc/ohmycoins/CURRENT_SPRINT.md` - **Track A section** - Your current sprint objectives

**Code Locations to Audit:**
- `backend/app/models.py` - Database models (CRITICAL: CatalystEvents schema issue)
- `backend/app/services/collectors/` - Your primary development area
- `backend/app/services/trading/` - Trading system requiring fixes
- `tests/services/collectors/` - Test coverage for collectors
- `tests/services/trading/` - Trading system tests (48 errors to resolve)
- `tests/utils/test_seed_data.py` - Seed data tests affected by schema issue

**Current Test Status:**
- **579 passing** tests (infrastructure is solid)
- **33 failing** tests (32 from CatalystEvents schema mismatch)
- **48 errors** (cascade failures in trading module from schema issue)

**Questions to Answer During Audit:**
1. What is the root cause of the CatalystEvents schema mismatch?
2. Which tests are blocked by the schema issue vs. independent failures?
3. What is the current state of the Catalyst Ledger collectors (SEC, CoinSpot)?
4. Are there any dependencies blocking your work?

---

### Phase 2: ALIGN (Verify Understanding)

**Action:** Confirm your understanding of the critical issues and sprint objectives.

**Critical Issue #1: CatalystEvents Schema Mismatch (BLOCKER)**
```
Location: backend/app/models.py:440-443
Problem: Model uses Column(JSON) but migration created ARRAY(String)
Error: psycopg.errors.DatatypeMismatch
Impact: 32 test failures + 48 cascading errors
```

**Expected Fix:**
```python
# Current (INCORRECT):
currencies: list[str] | None = Field(
    default=None,
    sa_column=Column(JSON)
)

# Required (CORRECT):
from sqlalchemy.dialects import postgresql

currencies: list[str] | None = Field(
    default=None,
    sa_column=Column(postgresql.ARRAY(sa.String()))
)
```

**Verification Migration File:**
- `backend/app/alembic/versions/c3d4e5f6g7h8_add_comprehensive_data_tables_phase_2_5.py:109`
- Confirms database schema uses `postgresql.ARRAY(sa.String())`

**Critical Issue #2: Trading Client Async Mocks**
```
Location: tests/services/trading/test_client.py
Problem: Mock objects not configured for async context managers
Tests Failing: test_api_error_handling, test_http_error_handling
Error: TypeError: 'coroutine' object does not support the asynchronous context manager protocol
```

**Sprint Priorities (Must Complete):**
1. ✅ Fix CatalystEvents schema (BLOCKER - do this first)
2. ✅ Fix trading client async mocks
3. ✅ Verify all 48 trading tests pass after schema fix
4. ✅ Implement SEC API collector
5. ✅ Implement CoinSpot announcements collector
6. 🔄 Quality monitor (stretch goal)

**Definition of Done:**
- All tests in `tests/services/trading/` pass
- All tests in `tests/utils/test_seed_data.py` pass
- Schema change documented in commit message
- SEC and CoinSpot collectors operational

---

### Phase 3: PLAN (Create Execution Strategy)

**Action:** Develop a detailed, step-by-step plan for sprint execution.

**Recommended Execution Order:**

**Step 1: Fix CatalystEvents Schema (30 minutes)**
1. Open `backend/app/models.py`
2. Add import: `from sqlalchemy.dialects import postgresql`
3. Locate line 440-443 (CatalystEvents.currencies field)
4. Replace `Column(JSON)` with `Column(postgresql.ARRAY(sa.String()))`
5. Verify no other schema mismatches exist
6. Run tests: `cd backend && source .venv/bin/activate && pytest tests/utils/test_seed_data.py -v`
7. Expected: All seed_data tests should pass

**Step 2: Fix Trading Client Async Mocks (45 minutes)**
1. Open `tests/services/trading/test_client.py`
2. Locate `test_api_error_handling` and `test_http_error_handling`
3. Update mock setup to use `AsyncMock` with proper `__aenter__`/`__aexit__`
4. Example pattern:
   ```python
   mock_response = AsyncMock()
   mock_response.__aenter__.return_value = mock_response
   mock_response.__aexit__.return_value = AsyncMock()
   ```
5. Run tests: `pytest tests/services/trading/test_client.py -v`
6. Expected: 2 failing tests should pass

**Step 3: Verify Trading System Integrity (20 minutes)**
1. Run full trading test suite: `pytest tests/services/trading/ -v`
2. Expected: All 48 previously erroring tests should now pass
3. If failures persist, investigate individual test modules:
   - `test_algorithm_executor.py`
   - `test_recorder.py`
   - `test_safety.py`

**Step 4: Add pytest.ini Configuration (10 minutes)**
1. Create `backend/pytest.ini`
2. Register custom markers:
   ```ini
   [pytest]
   markers =
       integration: marks tests as integration tests
       slow: marks tests as slow running
   ```
3. Eliminates 5 test warnings

**Step 5: Implement SEC API Collector (2-3 hours)**
1. Create `backend/app/services/collectors/sec_api.py`
2. Implement SEC EDGAR API integration
3. Target filings: Form 4, Form 8-K
4. Companies to track: MSTR (MicroStrategy), COIN (Coinbase)
5. Parse for crypto-related keywords
6. Store in `CatalystEvents` table with `event_type='filing'`
7. Add tests in `tests/services/collectors/test_sec_api.py`

**Step 6: Implement CoinSpot Announcements Collector (2-3 hours)**
1. Create or update `backend/app/services/collectors/coinspot_announcements.py`
2. Implement Zendesk announcements scraper (Playwright if needed)
3. Poll interval: 30-60 seconds for critical alerts
4. Parse for listing keywords: "listing", "new coin", "trading"
5. Store in `CatalystEvents` table with `event_type='listing'`
6. Add integration test with mock responses

**Step 7: Run Full Test Suite (15 minutes)**
1. Execute: `cd backend && bash scripts/test.sh`
2. Target: 0 failures, 0 errors in Track A modules
3. Document any remaining issues in commit message

---

### Phase 4: EXECUTE (Implement the Plan)

**Action:** Execute the plan methodically, testing after each step.

**Execution Guidelines:**
1. **Fix blockers first** - CatalystEvents schema is the #1 priority
2. **Test incrementally** - Don't move to next step until current tests pass
3. **Commit frequently** - Small, atomic commits with clear messages
4. **Document decisions** - If you deviate from plan, explain why
5. **Communication** - If blocked, report the blocker and required assistance

**Git Commit Message Template:**
```
[Track A] <component>: <short description>

- <detail 1>
- <detail 2>

Fixes: #<issue_number>
Tests: <test files affected>
```

**Example Commit:**
```
[Track A] models: Fix CatalystEvents currencies field schema mismatch

- Changed currencies field from JSON to postgresql.ARRAY(String)
- Aligns model with migration c3d4e5f6g7h8
- Resolves 32 test failures in seed_data and collectors

Fixes: Schema mismatch causing DatatypeMismatch errors
Tests: tests/utils/test_seed_data.py, tests/services/collectors/integration/
```

**Testing Commands:**
```bash
# Activate virtual environment
cd /home/mark/omc/ohmycoins/backend
source .venv/bin/activate

# Test specific module
pytest tests/services/collectors/ -v

# Test with coverage
pytest tests/services/collectors/ --cov=app.services.collectors --cov-report=html

# Full test suite
bash scripts/test.sh
```

**Success Criteria:**
- [ ] CatalystEvents schema fixed and verified
- [ ] All seed_data tests passing
- [ ] Trading client async mocks fixed
- [ ] All 48 trading tests passing
- [ ] SEC collector implemented and tested
- [ ] CoinSpot collector implemented and tested
- [ ] pytest.ini created with markers
- [ ] Full test suite: 0 failures, 0 errors in Track A modules
- [ ] Code committed with descriptive messages
- [ ] Ready for Track B integration testing

---

## 🔧 Technical Context

**Your Development Boundaries:**
- **Primary:** `backend/app/services/collectors/`
- **Secondary:** `backend/app/services/trading/`
- **Models:** `backend/app/models.py` (coordinate changes with Track B)
- **Tests:** `tests/services/collectors/`, `tests/services/trading/`, `tests/utils/`

**DO NOT MODIFY:**
- `backend/app/services/agent/` (Track B's domain)
- `infrastructure/` (Track C's domain)
- Frontend code

**Integration Contract:**
- **Track B** reads from your database schema (`backend/app/models.py`)
- **Track C** deploys your Docker images
- Changes to `models.py` require notification to Track B

**4-Ledgers Framework (Your Responsibility):**
1. **Glass Ledger** - On-chain metrics (DeFiLlama integration)
2. **Human Ledger** - Social sentiment (Reddit, CryptoPanic)
3. **Catalyst Ledger** - Critical events (SEC, CoinSpot) ← **Current focus**
4. **Exchange Ledger** - Market data (CoinSpot API)

---

## 📚 Additional Resources

**Database Connection:**
```python
# Local database
postgresql://postgres:yCF1VKX3h6mQxrNQ@localhost:5432/app

# In tests, use the db fixture from conftest.py
def test_example(db: Session):
    # db is automatically provided
```

**Environment Variables:**
```bash
# .env file location
/home/mark/omc/ohmycoins/.env

# Key variables for your work
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=app
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yCF1VKX3h6mQxrNQ
```

**Useful Commands:**
```bash
# Database shell
docker exec -it ohmycoins-db-1 psql -U postgres -d app

# Check schema
\d catalyst_events

# View running containers
docker compose ps

# Restart backend service
docker compose restart backend
```

---

## 🚨 Escalation Points

**Escalate if:**
1. Schema fix doesn't resolve test failures after verification
2. Trading tests reveal architectural issues beyond async mocks
3. SEC or CoinSpot APIs require authentication not documented
4. Integration with Track B's agent system fails after schema fix

**Do NOT escalate for:**
- Standard debugging of test failures
- Implementing collectors per requirements
- Fixing typing issues or linting errors

---

## ✅ Final Checklist Before Sprint Completion

Before marking sprint complete, verify:

- [ ] `git status` shows all changes committed
- [ ] `bash scripts/test.sh` passes with 0 failures in your modules
- [ ] Documentation updated if new collectors added
- [ ] No merge conflicts with main branch
- [ ] Track B notified of any schema changes
- [ ] Sprint tasks in `CURRENT_SPRINT.md` marked complete

---

**Remember:** You are fixing critical blockers first (schema), then enhancing the data collection capabilities. The entire system depends on your data infrastructure being correct and reliable. Focus, execute methodically, and test thoroughly.

**Good luck! 🚀**
