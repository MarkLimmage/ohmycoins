# Sprint 2.8 Prestart Failure Investigation

**Date:** January 17, 2026  
**Issue:** Integration tests failing due to prestart script errors  
**Status:** ✅ ROOT CAUSE IDENTIFIED

---

## Problem Summary

During Sprint 2.8 finalization, running tests with `docker compose run backend pytest` fails with:
```
service "prestart" didn't complete successfully: exit 255
```

This caused 42 integration/security tests to fail (23 integration + 19 security), blocking comprehensive Sprint 2.8 validation.

---

## Root Cause Analysis

### 1. Prestart Script Execution

The `backend` service in `docker-compose.yml` has a dependency on `prestart`:
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
    prestart:
      condition: service_completed_successfully  # ← Blocks if prestart fails
```

### 2. Prestart Script Failure

**Script:** [backend/scripts/prestart.sh](backend/scripts/prestart.sh)
```bash
#!/usr/bin/env bash
set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Run migrations
alembic upgrade head  # ← FAILS HERE

# Create initial data in DB
python app/initial_data.py
```

**Error from prestart logs:**
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head'; 
please specify a specific target revision, '<branchname>@head' to narrow to a specific head, 
or 'heads' for all heads

FAILED: Multiple head revisions are present for given argument 'head'
```

### 3. Alembic Migration Branching Issue

**Migration History:**
```
58387c92ac18 (initial_models) ← Base
  ↓
2a5dad6f1c22 (add_price_data_5min_table)
  ↓
b5pu1jf8qzda (align_price_data_5min_with_architecture)
  ↓
74xslpy3kp6z (add_user_timestamps_and_coinspot_credentials)
  ↓
a51f14ba7e3a (add_coinspot_credentials_table)
  ↓
8abf25dd5d93 (add_user_profile_fields)
  ↓
c0e0bdfc3471 (add_agent_session_tables)
  ↓
c3d4e5f6g7h8 (add_comprehensive_data_tables_phase_2_5)
  ↓
d1e2f3g4h5i6 (drop_item_table)
  ├─→ a1b2c3d4e5f6 (BYOM - add_user_llm_credentials) ← HEAD 2 (Sprint 2.8)
  └─→ e7f8g9h0i1j2 (add_url_collected_at_to_catalyst_events)
        ↓
      f9g0h1i2j3k4 (add_trading_tables)
        ↓
      28ac3452fc30 (add_algorithm_and_deployed_algorithm) ← HEAD 1 (Sprint 2.6)
```

**The Problem:**
- The BYOM migration (`a1b2c3d4e5f6`) was created with `down_revision = 'd1e2f3g4h5i6'`
- But `d1e2f3g4h5i6` already has descendants (`e7f8g9h0i1j2` → `f9g0h1i2j3k4` → `28ac3452fc30`)
- This created **two independent migration heads**
- Alembic's `upgrade head` command doesn't know which head to use

**Why This Happened:**
- Developer B created the BYOM migration in Sprint 2.8 based on an older revision
- The correct `down_revision` should have been `28ac3452fc30` (latest algorithm tables migration)
- This suggests Developer B's branch was created before Sprint 2.6 algorithm work was merged

---

## Impact Assessment

### Tests Affected

**Integration Tests (23 failures):**
- `tests/integration/test_deployment_database.py`: 19 tests
- `tests/integration/test_api_integration.py`: 4 tests

**Security Tests (19 failures):**  
- All security tests depend on proper database schema and backend startup

**Total Impact:**
- 42 tests blocked (out of 704 = 6% of test suite)
- All BYOM unit tests (43) pass because they don't depend on prestart
- All other unit tests pass with `--no-deps` flag to bypass prestart

### Sprint 2.8 Validation Impact

**What We Could Validate:**
- ✅ BYOM unit tests: 43/43 passing (100%)
- ✅ Seed data tests: 11/12 passing (91.7%)
- ✅ Non-integration tests: 646 passing

**What We Couldn't Validate:**
- ❌ Integration tests with full backend startup
- ❌ Security tests requiring initialized database
- ❌ End-to-end workflows

**Reported Test Results:**
- Tests: 704 total
- Passing: 646 (91.8%)
- Failing: 58 (includes 42 blocked by prestart + 16 other failures)

---

## Sprint 2.7 Context

### Prestart Script Creation

**Sprint 2.7 Changes:**
- No changes to prestart script itself
- Script already existed from earlier sprints
- Sprint 2.7 focused on PostgreSQL fixture migration for tests

**From Sprint 2.7 Final Report:**
> "Migration failures (check `prestart` logs)" - Documentation mentioned this as a potential issue

**Sprint 2.7 Test Execution:**
- Tests run successfully (645/661 passing)
- No migration branching issues at that time
- All migrations were linear: `... → e7f8g9h0i1j2 → f9g0h1i2j3k4 → 28ac3452fc30`

### When Branching Occurred

**Timeline:**
1. **Sprint 2.6-2.7:** Linear migrations ending at `28ac3452fc30` (algorithm tables)
2. **Sprint 2.8:** BYOM branch created with `down_revision = 'd1e2f3g4h5i6'` (earlier revision)
3. **Sprint 2.8:** Branch merged, creating two heads

This means the branching was introduced in **Sprint 2.8**, not Sprint 2.7.

---

## Solution Options

### Option 1: Merge Migration Heads (RECOMMENDED)

Create a merge migration that consolidates both heads:

```bash
cd backend
docker compose run --rm backend alembic merge -m "merge BYOM and algorithm migrations" 28ac3452fc30 a1b2c3d4e5f6
```

This creates a new migration with:
```python
revision = '<new_revision_id>'
down_revision = ('28ac3452fc30', 'a1b2c3d4e5f6')  # Tuple for merge
branch_labels = None
depends_on = None
```

**Pros:**
- Preserves both migration histories
- No data loss
- Standard Alembic pattern for resolving branches
- Safe for production

**Cons:**
- Requires creating a new migration file
- Needs testing to ensure no conflicts

### Option 2: Rebase BYOM Migration

Manually edit `a1b2c3d4e5f6_add_user_llm_credentials_and_extend_agent_session_byom.py`:
```python
# Change from:
down_revision = 'd1e2f3g4h5i6'

# To:
down_revision = '28ac3452fc30'
```

**Pros:**
- Creates linear migration history
- Simpler than merge

**Cons:**
- **DANGEROUS** if migration already applied to any database
- Requires recreating migration ID to avoid conflicts
- Not recommended for shared environments

### Option 3: Specify Head Explicitly (WORKAROUND)

For testing only, bypass prestart:
```bash
docker compose run --rm backend pytest --no-deps tests/
```

Or run migrations manually with specific head:
```bash
docker compose run --rm backend alembic upgrade a1b2c3d4e5f6  # BYOM head
docker compose run --rm backend alembic upgrade 28ac3452fc30  # Algorithm head
```

**Pros:**
- Quick fix for immediate testing needs
- No migration changes required

**Cons:**
- Doesn't solve the root problem
- Tests still fail when run normally
- Not sustainable

---

## Recommended Resolution

### For Sprint 2.8 (Current):

**Immediate:** Use Option 3 (workaround) to complete Sprint 2.8 validation:
```bash
# Run tests without prestart dependency
docker compose run --rm backend pytest --no-deps tests/

# Or run migrations manually to both heads
docker compose run --rm backend sh -c "alembic upgrade 28ac3452fc30 && alembic upgrade a1b2c3d4e5f6"
```

**Document:** Note in Sprint 2.8 final report that integration tests couldn't be validated due to migration branching

### For Sprint 2.9 (Next):

**Priority 1:** Create merge migration (Option 1):
```bash
cd backend
docker compose run --rm backend alembic merge -m "merge BYOM and algorithm migrations" 28ac3452fc30 a1b2c3d4e5f6
```

**Priority 2:** Validate merge:
- Run full migration from scratch
- Test all integration tests
- Verify both BYOM and algorithm features work

**Priority 3:** Update development guidelines:
- Always create migrations from latest `head`
- Run `alembic heads` before creating new migrations
- Check for branch conflicts before merging PRs

---

## Key Learnings

### Developer Workflow Issues

1. **Branch Timing:** Developer B's BYOM branch was created before Sprint 2.6 algorithm work merged
2. **Rebase Needed:** Should have rebased before creating migration
3. **Review Gap:** PR review didn't catch migration branching (hard to spot without running alembic)

### Testing Infrastructure

1. **Unit Tests vs Integration Tests:**
   - Unit tests (BYOM, seed data) passed without issue
   - Integration tests blocked by prestart dependency
   - This is why we saw 646/704 passing (92%), not 100%

2. **Test Isolation:**
   - Tests with `--no-deps` flag bypass prestart
   - Good for rapid unit testing
   - Bad for catching integration issues

### Documentation Gaps

1. **Migration Best Practices:** Need documented workflow for creating migrations
2. **Prestart Debugging:** Need guide for diagnosing prestart failures
3. **Alembic Commands:** Need quick reference for common scenarios

---

## Prevention for Future Sprints

### Pre-PR Checklist

- [ ] Run `alembic heads` - should show exactly 1 head
- [ ] Run `alembic current` - verify on latest head
- [ ] Run `docker compose run --rm backend pytest` (full suite with prestart)
- [ ] Check migration chain with `alembic history`

### Migration Guidelines

1. **Before creating migration:**
   ```bash
   git pull origin main  # Get latest
   docker compose run --rm backend alembic upgrade head  # Sync local DB
   docker compose run --rm backend alembic heads  # Verify single head
   ```

2. **Create migration:**
   ```bash
   docker compose run --rm backend alembic revision --autogenerate -m "description"
   ```

3. **After creating migration:**
   ```bash
   docker compose run --rm backend alembic heads  # Still single head?
   docker compose run --rm backend pytest  # Full test suite
   ```

### CI/CD Checks

Add to GitHub Actions:
```yaml
- name: Check migration heads
  run: |
    docker compose run --rm backend alembic heads > heads.txt
    HEAD_COUNT=$(wc -l < heads.txt)
    if [ $HEAD_COUNT -gt 1 ]; then
      echo "ERROR: Multiple migration heads detected"
      cat heads.txt
      exit 1
    fi
```

---

## References

- **Alembic Documentation:** https://alembic.sqlalchemy.org/en/latest/branches.html
- **Sprint 2.7 Final Report:** [docs/archive/history/sprints/sprint-2.7/SPRINT_2.7_FINAL_REPORT.md](docs/archive/history/sprints/sprint-2.7/SPRINT_2.7_FINAL_REPORT.md)
- **Sprint 2.8 Final Report:** [docs/archive/history/sprints/sprint-2.8/SPRINT_2.8_FINAL_REPORT.md](docs/archive/history/sprints/sprint-2.8/SPRINT_2.8_FINAL_REPORT.md)
- **Prestart Script:** [backend/scripts/prestart.sh](backend/scripts/prestart.sh)
- **Migration Files:** [backend/app/alembic/versions/](backend/app/alembic/versions/)

---

**Investigation Date:** January 17, 2026  
**Investigator:** GitHub Copilot (Claude Sonnet 4.5)  
**Status:** ✅ Root cause identified, resolution plan documented  
**Next Action:** Create merge migration in Sprint 2.9
