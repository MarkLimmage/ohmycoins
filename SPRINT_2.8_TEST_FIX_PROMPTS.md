# Sprint 2.8 - Test Fix Prompts for Developer A

**Target Developer:** OMC-Data-Specialist (Track A - Data & Backend)  
**Priority:** HIGH - Must complete before BYOM implementation  
**Target Outcome:** 99% test pass rate (655/661 tests)

---

## Overview: 16 Test Failures Analysis

All 16 failing tests are in Track A (Data & Backend). Based on Sprint 2.7 results, the failures break down as follows:

1. **PnL Calculation Logic** - 2 failures (HIGH PRIORITY)
2. **Seed Data Test Isolation** - 11 failures (MEDIUM PRIORITY)
3. **Safety Manager Configuration** - 1 failure (MEDIUM PRIORITY)
4. **Synthetic Data Diversity** - 1 failure (LOW PRIORITY)
5. **Playwright Import Errors** - 3 failures (mentioned in docs, LOW PRIORITY)

---

## Prompt 1: Fix PnL Calculation Logic (HIGH PRIORITY)

**Priority:** P0 - CRITICAL  
**Estimated Effort:** 4-6 hours  
**Impact:** Trading calculations accuracy

### Context

Two PnL calculation tests are failing with significant discrepancies in unrealized P&L calculations:

```
FAILED tests/services/trading/test_pnl.py::test_calculate_unrealized_pnl_with_position
  AssertionError: assert Decimal('31628.799829620000000000') == Decimal('4000.00')

FAILED tests/services/trading/test_pnl.py::test_pnl_with_no_price_data
  AssertionError: assert Decimal('15814.399914810000000000') == Decimal('0')
```

The calculated values are **significantly higher** than expected, suggesting a multiplication error or incorrect price data retrieval in the PnL calculation engine.

### Your Task

**Objective:** Investigate and fix the unrealized P&L calculation logic in the trading PnL engine to ensure accurate profit/loss calculations.

**Action Steps:**

1. **Read the failing tests:**
   - File: `backend/tests/services/trading/test_pnl.py`
   - Focus on: `test_calculate_unrealized_pnl_with_position` (line ~432)
   - Focus on: `test_pnl_with_no_price_data` (line ~875)

2. **Examine the PnL calculation logic:**
   - File: `backend/app/services/trading/pnl.py`
   - Look for the `calculate_unrealized_pnl()` function
   - Check price data retrieval logic
   - Verify calculation formulas: `(current_price - entry_price) * quantity`

3. **Debug the calculation:**
   - Add logging to understand what values are being used
   - Check if price data is being retrieved correctly
   - Verify that the correct price (5-min, hourly, daily) is being used
   - Look for off-by-one errors or incorrect multipliers

4. **Common issues to check:**
   - Is the price being multiplied by quantity twice?
   - Is the wrong price source being queried (e.g., cents vs dollars)?
   - Is the position quantity correct?
   - Are there currency conversion issues (BTC vs AUD)?

5. **Fix and validate:**
   - Correct the calculation logic
   - Run the specific tests: `pytest backend/tests/services/trading/test_pnl.py::test_calculate_unrealized_pnl_with_position -v`
   - Run all PnL tests: `pytest backend/tests/services/trading/test_pnl.py -v`
   - Ensure all 13/13 PnL API tests remain passing

**Expected Outcome:**
- Both PnL calculation tests pass
- All other PnL tests remain stable (13/13 API tests)
- Calculation logic is documented with comments explaining the formula

**Files to Modify:**
- `backend/app/services/trading/pnl.py` - Fix calculation logic
- Possibly `backend/tests/services/trading/test_pnl.py` - If test expectations are incorrect

---

## Prompt 2: Fix Seed Data Test Isolation (MEDIUM PRIORITY)

**Priority:** P1 - High  
**Estimated Effort:** 2-3 hours  
**Impact:** Test stability and development workflows

### Context

11 tests in `backend/tests/utils/test_seed_data.py` are failing due to unique constraint violations on user emails:

```
sqlalchemy.exc.IntegrityError: (psycopg.errors.UniqueViolation) 
duplicate key value violates unique constraint "ix_user_email"
```

This is followed by 10 cascading `PendingRollbackError` failures. This is a **test isolation issue** - tests are creating users with the same email addresses, causing database constraint violations.

### Your Task

**Objective:** Fix test isolation in seed data tests by implementing UUID-based unique email generation, following the pattern used in Sprint 2.7 for PnL tests.

**Action Steps:**

1. **Review the successful pattern from Sprint 2.7:**
   - File: `backend/tests/services/trading/test_pnl_api.py`
   - Look for UUID usage in test data creation (search for `uuid.uuid4()`)
   - Example pattern:
   ```python
   import uuid
   
   # Generate unique email for test isolation
   unique_id = uuid.uuid4().hex[:8]
   user = UserCreate(
       email=f"test_{unique_id}@example.com",
       password="testpassword123"
   )
   ```

2. **Identify all failing tests in seed data:**
   - `test_generate_users`
   - `test_generate_algorithms`
   - `test_generate_positions_and_orders`
   - `test_clear_all_data`
   - `test_create_test_user`
   - `test_create_test_price_data`
   - `test_create_test_algorithm`
   - `test_create_test_position`
   - `test_create_test_order`
   - `test_user_position_relationship`
   - `test_user_order_relationship`

3. **Apply UUID pattern to seed data utilities:**
   - File: `backend/app/utils/seed_data.py`
   - Update any user creation functions to use UUID-based emails
   - Ensure all helper functions that create users accept optional email parameter
   - Apply same pattern to algorithm names if needed

4. **Update test fixtures:**
   - File: `backend/tests/utils/test_seed_data.py`
   - Add `import uuid` at top of file
   - For each test creating users, generate unique emails
   - Ensure tests don't rely on specific email values unless necessary

5. **Test the fix:**
   - Run all seed data tests: `pytest backend/tests/utils/test_seed_data.py -v`
   - Run tests multiple times to ensure isolation: `pytest backend/tests/utils/test_seed_data.py -v --count=3`
   - Verify no cascading errors

**Expected Outcome:**
- All 11 seed data tests pass
- Tests can run independently without order dependencies
- Tests can run multiple times without cleanup issues

**Files to Modify:**
- `backend/app/utils/seed_data.py` - Add UUID to user/algorithm generation
- `backend/tests/utils/test_seed_data.py` - Update test data creation

**Pattern Reference:**
Sprint 2.7 successfully used this pattern to fix 13/13 PnL API tests. Apply the same approach here.

---

## Prompt 3: Fix Safety Manager Test Configuration (MEDIUM PRIORITY)

**Priority:** P1 - High  
**Estimated Effort:** 1 hour  
**Impact:** Safety mechanism validation

### Context

One safety manager test is failing with an unexpected safety violation:

```
FAILED tests/services/trading/test_safety.py::TestSafetyManager::test_algorithm_exposure_limit_within_limit
  app.services.trading.safety.SafetyViolation: Daily loss limit exceeded. 
  Loss: 1000.00 AUD, Limit: 500.00 AUD (5% of portfolio)
```

The test `test_algorithm_exposure_limit_within_limit` is checking **exposure limits**, but a **daily loss limit** is being triggered instead. This suggests either:
- Test configuration issue (wrong portfolio value)
- Test is creating losses when it shouldn't
- Safety manager is checking wrong limits

### Your Task

**Objective:** Fix the safety manager test to properly validate exposure limits without triggering daily loss limits.

**Action Steps:**

1. **Read the failing test:**
   - File: `backend/tests/services/trading/test_safety.py`
   - Locate: `test_algorithm_exposure_limit_within_limit`
   - Understand what the test is trying to validate

2. **Analyze the error:**
   - Daily loss limit: 500 AUD (5% of portfolio)
   - Actual loss: 1000 AUD
   - This means portfolio value is 10,000 AUD (5% = 500)
   - But the test is somehow generating 1000 AUD loss

3. **Check test setup:**
   - Is the portfolio value set correctly?
   - Are positions being created with losses?
   - Is the test creating orders that result in losses?
   - Should the test be setting a higher portfolio value?

4. **Review safety manager logic:**
   - File: `backend/app/services/trading/safety.py`
   - Line ~240: Daily loss limit check
   - Verify the calculation logic is correct
   - Check if exposure limit is being checked before daily loss limit

5. **Possible fixes:**
   - **Option A:** Increase portfolio value in test to accommodate 1000 AUD loss
   - **Option B:** Adjust test to create positions/orders without losses
   - **Option C:** Disable daily loss check for this specific test (use mock or config)
   - **Option D:** Fix calculation error in safety manager

6. **Validate the fix:**
   - Run: `pytest backend/tests/services/trading/test_safety.py::TestSafetyManager::test_algorithm_exposure_limit_within_limit -v`
   - Run all safety tests: `pytest backend/tests/services/trading/test_safety.py -v`

**Expected Outcome:**
- Test passes and validates exposure limits correctly
- Daily loss limit checking remains functional
- All other safety manager tests remain passing

**Files to Modify:**
- `backend/tests/services/trading/test_safety.py` - Fix test configuration
- Possibly `backend/app/services/trading/safety.py` - If logic issue found

---

## Prompt 4: Fix Synthetic Data Diversity Test (LOW PRIORITY)

**Priority:** P2 - Medium  
**Estimated Effort:** 1-2 hours  
**Impact:** Non-blocking for production

### Context

One synthetic data generation test is failing:

```
FAILED tests/integration/test_synthetic_data_examples.py::TestDataRealism::test_user_profiles_diversity
  AssertionError: assert 1 > 1
```

This assertion `assert 1 > 1` will always fail, suggesting either:
- The test is checking that unique count > 1, but only 1 unique value exists
- There's a logic error in the diversity calculation
- The synthetic data generator is producing identical values

### Your Task

**Objective:** Fix the synthetic data diversity test to ensure user profile generation creates diverse, realistic data.

**Action Steps:**

1. **Read the test:**
   - File: `backend/tests/integration/test_synthetic_data_examples.py`
   - Line ~223: `test_user_profiles_diversity`
   - Understand what diversity metric is being checked

2. **Identify the diversity check:**
   - Is it checking unique email count?
   - Is it checking unique name count?
   - Is it checking some other user attribute?

3. **Examine synthetic data generation:**
   - File: Look for synthetic data generation utilities
   - Check if user profile generation has sufficient randomization
   - Verify random seed isn't causing identical outputs

4. **Debug the actual values:**
   - Add print statements to see what's being generated
   - Check how many users are being created
   - Verify the actual diversity metric value

5. **Common fixes:**
   - Increase randomization in data generation
   - Use UUID or timestamps for guaranteed uniqueness
   - Increase number of users generated if too few
   - Remove or adjust random seed if it's causing identical values

6. **Validate:**
   - Run: `pytest backend/tests/integration/test_synthetic_data_examples.py::TestDataRealism::test_user_profiles_diversity -v`
   - Run multiple times to ensure randomization works

**Expected Outcome:**
- Test passes with diverse user profiles
- Synthetic data generation creates realistic, varied data
- Test provides useful validation of data quality

**Files to Modify:**
- Possibly `backend/app/utils/synthetic_data.py` or similar
- `backend/tests/integration/test_synthetic_data_examples.py` - Fix test logic if needed

---

## Prompt 5: Add Playwright to Docker Container (LOW PRIORITY)

**Priority:** P2 - Medium  
**Estimated Effort:** 1-2 hours  
**Impact:** 3 catalyst collector tests currently not executing

### Context

From the documentation, 3 tests are failing due to Playwright not being installed in the Docker container:

```
Playwright Dependency (3 import errors)
- Location: Catalyst collector tests
- Issue: Playwright not installed in container
- Code validated in Sprint 2.6
```

The Catalyst collector uses Playwright for web scraping (SEC filings, exchange announcements), but the dependency isn't available in the test environment.

### Your Task

**Objective:** Add Playwright to the backend Docker container to enable catalyst collector tests.

**Action Steps:**

1. **Identify the Playwright dependency:**
   - File: `backend/pyproject.toml`
   - Check if playwright is listed as a dependency
   - Check if it's under `[tool.poetry.dependencies]` or `[tool.poetry.group.dev.dependencies]`

2. **Update Dockerfile to install Playwright:**
   - File: `backend/Dockerfile`
   - Add Playwright system dependencies
   - Run playwright install command
   
   Example additions:
   ```dockerfile
   # Install Playwright dependencies
   RUN apt-get update && apt-get install -y \
       libnss3 \
       libnspr4 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libcups2 \
       libdrm2 \
       libdbus-1-3 \
       libxkbcommon0 \
       libxcomposite1 \
       libxdamage1 \
       libxfixes3 \
       libxrandr2 \
       libgbm1 \
       libpango-1.0-0 \
       libcairo2 \
       libasound2 \
       && rm -rf /var/lib/apt/lists/*
   
   # Install Playwright browsers
   RUN pip install playwright && playwright install chromium
   ```

3. **Check if tests are marked appropriately:**
   - File: `backend/tests/services/collector/test_catalyst_collector.py`
   - Ensure tests using Playwright are marked with `@pytest.mark.integration`
   - These tests should be skippable if Playwright isn't available

4. **Update pytest markers:**
   - File: `backend/pytest.ini`
   - Ensure `integration` marker is registered

5. **Test locally:**
   - Rebuild Docker image: `docker compose build backend`
   - Run collector tests: `docker compose run backend pytest tests/services/collector/ -v`

6. **Consider alternatives:**
   - If Playwright adds too much to image size, consider:
     - Making these tests optional with `@pytest.mark.requires_playwright`
     - Running them only in CI/CD with playwright-enabled image
     - Using a multi-stage build for testing vs production

**Expected Outcome:**
- 3 catalyst collector tests can import and use Playwright
- Tests pass (code was validated in Sprint 2.6)
- Docker image builds successfully with minimal size increase

**Files to Modify:**
- `backend/Dockerfile` - Add Playwright installation
- Possibly `backend/pyproject.toml` - Ensure playwright is in dependencies
- Possibly `backend/pytest.ini` - Add playwright-related markers

---

## Execution Strategy

### Recommended Order:

1. **Start with Prompt 1** (PnL Calculation) - 4-6 hours
   - **Why:** Highest priority, affects trading accuracy
   - **Blocker:** Must be fixed before production deployment

2. **Then Prompt 2** (Seed Data Isolation) - 2-3 hours
   - **Why:** Affects 11 tests, high impact on test stability
   - **Pattern:** Use proven UUID approach from Sprint 2.7

3. **Then Prompt 3** (Safety Manager) - 1 hour
   - **Why:** Quick win, validates safety mechanisms

4. **Then Prompt 4** (Synthetic Data) - 1-2 hours
   - **Why:** Low impact, can be deferred if needed

5. **Finally Prompt 5** (Playwright) - 1-2 hours
   - **Why:** Lowest priority, tests were validated in Sprint 2.6

### Total Estimated Effort: 9-15 hours

### Sprint 2.8 Integration:

These fixes can run **in parallel** with BYOM Sprint 2.8 foundation work (8-12 hours), as they modify different code areas:
- Test fixes: Track A (trading, utils, tests)
- BYOM foundation: Track B (agent services, encryption, database)

### Success Criteria:

- ✅ Target: 655/661 tests passing (99% pass rate)
- ✅ All high-priority fixes (PnL + Seed Data) = 13 tests fixed
- ✅ All medium-priority fixes (Safety + Synthetic) = 2 tests fixed
- ✅ Playwright fix = 3 tests enabled (if time permits)

---

## Testing Strategy

After each fix:

1. **Run specific test:** `pytest path/to/test_file.py::test_name -v`
2. **Run test file:** `pytest path/to/test_file.py -v`
3. **Run related tests:** `pytest path/to/test_directory/ -v`
4. **Run full suite:** `docker compose run backend pytest -v`

### Validation Commands:

```bash
# After fixing PnL (Prompt 1)
docker compose run backend pytest tests/services/trading/test_pnl.py -v

# After fixing seed data (Prompt 2)
docker compose run backend pytest tests/utils/test_seed_data.py -v --count=3

# After fixing safety (Prompt 3)
docker compose run backend pytest tests/services/trading/test_safety.py -v

# After fixing synthetic data (Prompt 4)
docker compose run backend pytest tests/integration/test_synthetic_data_examples.py -v

# After fixing playwright (Prompt 5)
docker compose run backend pytest tests/services/collector/ -v

# Final validation
docker compose run backend pytest -v
```

---

## Documentation Updates

After completing all fixes, update:

1. **CURRENT_SPRINT.md** - Mark Sprint 2.8 test fixes complete
2. **ROADMAP.md** - Update test pass rate to 99%
3. Create **Sprint 2.8 completion report** following Sprint 2.7 template

---

**Generated:** 2026-01-17  
**Target Developer:** OMC-Data-Specialist (Track A)  
**Sprint:** 2.8 - Test Stabilization  
**Next Phase:** BYOM Implementation (Track B)
