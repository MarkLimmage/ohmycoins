# Sprint 2.8 Test Fix Prompts

**Sprint Start Date:** 2026-01-17  
**Status:** IN PROGRESS  
**Goal:** Fix remaining 16 test failures from Sprint 2.7 to achieve 99%+ test pass rate

---

## Overview

Sprint 2.7 achieved 97.6% test pass rate (645/661 passing). Sprint 2.8 focuses on fixing the remaining 16 test failures to achieve 99%+ pass rate and prepare for production deployment.

### Current Test Status
- **Total Tests:** 661 collected
- **Passing:** 645 (97.6%)
- **Failing:** 16 (2.4%)
- **Skipped:** 11

---

## Developer A: Fix Seed Data Test Isolation (High Priority)

**Assigned to:** Developer A  
**Files to modify:** `backend/tests/utils/test_seed_data.py`  
**Estimated effort:** 2-3 hours

### Problem
11 test failures in `test_seed_data.py` caused by duplicate email constraint violations. The issue is identical to the PnL test isolation issue fixed in Sprint 2.7.

### Root Cause
Hardcoded email addresses in test data generation causing duplicate key violations when tests run in parallel or sequentially without proper cleanup.

### Solution (Apply UUID Pattern from Sprint 2.7)
Follow the same pattern used in Sprint 2.7 Track A for PnL tests:

1. **Add UUID to email generation in test fixtures**
   - Import `uuid` module
   - Change from: `email="test@example.com"`
   - Change to: `email=f"test_{uuid.uuid4()}@example.com"`

2. **Apply to all test fixture functions that create users**
   - `test_generate_users`
   - `test_create_test_user`
   - Any other functions creating User objects

3. **Reference Implementation**
   See `backend/tests/api/routes/test_pnl.py` for the UUID pattern:
   ```python
   import uuid
   
   email=f"pnl_test_{uuid.uuid4()}@example.com"
   ```

### Expected Results
- All 11 tests in `test_seed_data.py` should pass
- No duplicate key violations
- Tests should be isolated and repeatable

### Validation
```bash
cd backend
pytest tests/utils/test_seed_data.py -v
```

All tests should pass.

---

## Developer B: Review PnL Calculation Logic (High Priority)

**Assigned to:** Developer B  
**Files to investigate:** 
- `backend/app/services/trading/pnl.py`
- `backend/tests/services/trading/test_pnl.py`  
**Estimated effort:** 4-6 hours

### Problem
2 test failures in `test_pnl.py`:
1. `test_calculate_unrealized_pnl_with_position` - Expected: 4000.00, Got: 31628.80
2. `test_pnl_with_no_price_data` - Expected: 0, Got: 15814.40

### Root Cause
Calculation discrepancies in unrealized PnL logic. The actual values are significantly different from expected, suggesting a logic error rather than a test issue.

### Investigation Steps
1. Review the `calculate_unrealized_pnl()` method in `pnl.py`
2. Check position value calculation formulas
3. Verify price data handling when no data is available
4. Review test expectations - are they correct?
5. Check for currency conversion issues or decimal precision

### Expected Action
This requires business logic review - DO NOT just change test expectations. Fix the actual calculation logic if incorrect, or update tests if expectations are wrong with clear justification.

---

## Developer C: Fix Safety Manager Test Configuration (Medium Priority)

**Assigned to:** Developer C  
**Files to investigate:**
- `backend/tests/services/trading/test_safety.py`
- `backend/app/services/trading/safety.py`  
**Estimated effort:** 1-2 hours

### Problem
1 test failure: `test_algorithm_exposure_limit_within_limit`
- Error: "Daily loss limit exceeded. Loss: 1000.00 AUD, Limit: 500.00 AUD (5% of portfolio)"

### Root Cause
Test configuration issue - the test expects the algorithm to be within limits, but the safety manager is rejecting it based on daily loss limit.

### Investigation Steps
1. Review test setup - what portfolio value and loss are being tested?
2. Check if the loss limit calculation is correct (5% of portfolio = 500 AUD → portfolio = 10,000 AUD)
3. Verify if test is setting up a loss of 1000 AUD when it should be less
4. Review if this is a test setup issue or a safety manager logic issue

### Expected Action
Either fix the test setup to be within limits, or fix the safety manager logic if it's calculating incorrectly.

---

## Developer D: Fix User Profile Diversity Test (Low Priority)

**Assigned to:** Developer D  
**Files to investigate:** `backend/tests/integration/test_synthetic_data_examples.py`  
**Estimated effort:** 1-2 hours

### Problem
1 test failure: `test_user_profiles_diversity`
- Error: `assert 1 > 1` (suggests only 1 unique value when expecting more)

### Root Cause
Synthetic data generation not creating diverse enough user profiles. The test expects multiple unique values in some field but only getting 1.

### Investigation Steps
1. Review what field is being checked for diversity
2. Check synthetic data generation logic
3. Verify if this is a data generation issue or test expectation issue
4. Increase sample size or improve generation algorithm

### Expected Action
Fix the synthetic data generation to create more diverse profiles, or adjust test expectations if they're unrealistic.

---

## Sprint 2.8 Success Criteria

✅ **Target:** 99%+ test pass rate (653+ of 661 passing)

### Priority Breakdown
- **P1 (High):** Seed data tests (11 failures) + PnL tests (2 failures) = 13 tests
- **P2 (Medium):** Safety manager test (1 failure) = 1 test  
- **P3 (Low):** Diversity test (1 failure) = 1 test
- **P4 (Blocked):** Playwright dependency (3 import errors) = Not counted in Sprint 2.8

### Minimum Viable Sprint
Fix P1 issues → 658/661 passing = 99.5% pass rate ✅

---

## Reference Documents
- [ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md](ACTION_REQUIRED_SPRINT_2.7_COMPLETE.md) - Sprint 2.7 completion summary
- [docs/archive/history/sprints/sprint-2.7/SPRINT_2.7_FINAL_REPORT.md](docs/archive/history/sprints/sprint-2.7/SPRINT_2.7_FINAL_REPORT.md) - Detailed Sprint 2.7 results
- [backend/tests/api/routes/test_pnl.py](backend/tests/api/routes/test_pnl.py) - UUID pattern reference implementation

---

**Generated:** 2026-01-17  
**Sprint 2.8 Status:** Ready to Start  
**Next Action:** Developer A - Fix seed data test isolation
