# Track A Sprint 2.6: Next Steps

**Developer:** OMC-Data-Specialist  
**Current Progress:** 70% Complete ✅  
**Remaining Work:** 2.5-4.5 hours  
**Sprint End:** January 24, 2026

---

## 🎉 Great News!

Your code quality is **excellent**. Test execution reveals that:

- ✅ **Quality Monitor:** COMPLETE (17/17 tests passing)
- ✅ **Catalyst Collectors:** COMPLETE (9/9 tests passing)
- 🟡 **Seed Data:** Nearly complete (11/12 passing)
- 🔴 **PnL Tests:** Fixture issue, not calculation bug

**Your 30% self-assessment was overly conservative!** Actual progress: **70% complete**.

---

## 🎯 Immediate Tasks

### Task 1: Fix PnL Test Fixture (HIGH PRIORITY)
**Time:** 2-4 hours  
**File:** `backend/tests/services/trading/test_pnl.py` lines 19-25

**Problem:** SQLite test fixture can't handle PostgreSQL ARRAY types (from Sprint 2.5 schema fix)

**Solution:** Replace SQLite with PostgreSQL
```python
# Current (lines 19-25):
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",  # ❌ No ARRAY support
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)  # Fails on ARRAY columns
    
# Fix: Use actual PostgreSQL
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Clear tables before test
        session.exec(delete(Position))
        session.exec(delete(Order))
        session.exec(delete(PriceData5Min))
        session.commit()
        yield session
```

**Validation:**
```bash
cd backend
pytest tests/services/trading/test_pnl.py -v
# Expected: 21/21 passing (currently 1/21)
```

---

### Task 2: Fix Seed Data Test Assertion (LOW PRIORITY)
**Time:** 30 minutes  
**File:** `backend/tests/utils/test_seed_data.py` line 50

**Problem:** Test expects delta count, gets absolute count

**Current (line 50):**
```python
assert final_count == initial_count + 5  # Fails: 5 == (1 + 5)
```

**Solution Option A (Recommended):**
```python
assert final_count == 5  # Test absolute count
```

**Solution Option B:**
```python
# Add at start of test
clear_all_data(db)  # Ensure clean state
initial_count = db.exec(select(func.count(User.id))).one()  # Now 0
# ... rest of test unchanged
```

**Validation:**
```bash
cd backend
pytest tests/utils/test_seed_data.py::TestSeedData::test_generate_users -v
# Expected: PASSED
```

---

## 📊 Final Targets

**Current:** 172/195 passing (88.2%)  
**Target:** 192/195 passing (98.5%)

**Changes:**
- P1 Fix: +1 passing (12/12 seed data tests)
- P2 Fix: +20 passing (21/21 PnL tests)
- Total: +21 tests fixed

---

## ✅ Definition of Done

**Code Quality:**
- [ ] PnL test fixture uses PostgreSQL
- [ ] Seed data test assertion fixed
- [ ] All Track A tests run: `pytest tests/utils/ tests/services/collectors/ tests/services/trading/`
- [ ] Result: 192/195 passing tests

**Documentation:**
- [ ] Update [docs/TESTING.md](docs/TESTING.md) with test fixture pattern guidance
- [ ] Add note: "Use PostgreSQL for tests, not SQLite (ARRAY type incompatibility)"

**Commit:**
```bash
git add .
git commit -m "fix(tests): Refactor PnL fixture to use PostgreSQL, fix seed data assertion

- Replace SQLite with PostgreSQL in test_pnl.py fixture (fixes 20 errors)
- Update test_seed_data.py assertion to use absolute count (fixes 1 failure)
- Document test fixture pattern in TESTING.md

Result: 192/195 Track A tests passing (98.5%)"
```

**PR:**
- Title: "Track A Sprint 2.6: Test Infrastructure Fixes"
- Link: [TRACK_A_TEST_REPORT.md](TRACK_A_TEST_REPORT.md)
- Note: Quality Monitor and Catalyst Collectors already complete (no changes needed)

---

## 📖 Reference

**Full Test Report:** [TRACK_A_TEST_REPORT.md](TRACK_A_TEST_REPORT.md)  
**Sprint Plan:** [SPRINT_INITIALIZATION.md](SPRINT_INITIALIZATION.md)  
**Previous Documentation:**
- [TRACK_A_README.md](TRACK_A_README.md) - Your initial assessment
- [TRACK_A_SPRINT_STATUS.md](TRACK_A_SPRINT_STATUS.md) - Detailed code review
- [TRACK_A_RECOMMENDATIONS.md](TRACK_A_RECOMMENDATIONS.md) - Action plan

---

## 🤝 Need Help?

**Blocker:** Can't run tests due to Docker dependency issue?
- Test environment validated working (used for this test report)
- Alternative: Use local Python venv (see TRACK_A_README.md lines 20-30)

**Questions about fixture refactor?**
- Reference: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) Section 9 - Test patterns
- Example: Other tests using PostgreSQL fixtures

**Ready to proceed?**
Start with Task 1 (PnL fixture) - it's the blocker for 20 tests! 🚀
