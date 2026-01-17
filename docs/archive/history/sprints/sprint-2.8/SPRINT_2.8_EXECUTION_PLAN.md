# Sprint 2.8 Execution Plan

**Status:** Ready to Execute  
**Date:** January 17, 2026  
**Sprint Goal:** Achieve 99% test pass rate + Begin BYOM foundation

---

## Executive Summary

**Current State:**
- 645/661 tests passing (97.6%)
- 16 test failures in Track A (Data & Backend)
- AWS staging environment deployed and operational
- All Track B (Agentic AI) tests passing (318/318)

**Sprint 2.8 Goal:**
- Fix 13-16 test failures → Target: 655-661 tests passing (99-100%)
- Begin BYOM foundation work (8-12 hours)
- Prepare for production deployment

**Total Estimated Effort:** 17-27 hours (split between Track A and Track B)

---

## Developer Assignment

### Developer A: OMC-Data-Specialist (Track A - Test Fixes)
**Workload:** 9-15 hours  
**Focus:** Fix all 16 failing tests

**Tasks:**
1. ✅ Fix PnL calculation logic (2 tests) - 4-6 hours - **P0 CRITICAL**
2. ✅ Fix seed data test isolation (11 tests) - 2-3 hours - **P1 HIGH**
3. ✅ Fix safety manager test (1 test) - 1 hour - **P1 HIGH**
4. ✅ Fix synthetic data diversity (1 test) - 1-2 hours - **P2 MEDIUM**
5. ✅ Add Playwright to container (3 tests) - 1-2 hours - **P2 MEDIUM**

**Detailed Prompts:** See [SPRINT_2.8_TEST_FIX_PROMPTS.md](SPRINT_2.8_TEST_FIX_PROMPTS.md)

### Developer B: OMC-ML-Scientist (Track B - BYOM Foundation)
**Workload:** 8-12 hours  
**Focus:** Begin BYOM implementation

**Tasks:**
1. ✅ Create database schema (UserLLMCredentials table) - 2-3 hours
2. ✅ Extend EncryptionService for LLM keys - 2-3 hours
3. ✅ Implement LLM Factory (OpenAI + Google) - 2-3 hours
4. ✅ Create API endpoints (CRUD + validation) - 2-3 hours

**Detailed Requirements:** See [docs/requirements/BYOM_USER_STORIES.md](docs/requirements/BYOM_USER_STORIES.md)

### Developer C: OMC-DevOps-Engineer (Track C - Standby)
**Workload:** 0 hours (Sprint 2.7 complete, monitoring staging)  
**Focus:** Monitor staging environment, prepare for production deployment

**Tasks:**
1. ✅ Monitor staging environment health
2. ✅ Document any deployment issues
3. ✅ Prepare production deployment checklist

---

## Work Parallelization

These tasks can run **in parallel** with zero conflicts:

**Track A (Developer A):**
- Modifies: `backend/app/services/trading/`, `backend/app/utils/`, `backend/tests/`
- Focus: Trading logic, test utilities, test files

**Track B (Developer B):**
- Modifies: `backend/app/services/agent/`, `backend/app/models/`, `backend/app/api/`
- Focus: Agent services, database models, API endpoints

**Zero overlap** - Different directories, different functional areas.

---

## Sprint Schedule

### Week 1 (Jan 17-21)
**Days 1-2 (Fri-Sat):**
- Developer A: Fix PnL calculation (P0) + Seed data isolation (P1) = 6-9 hours
- Developer B: Database schema + Encryption service = 4-6 hours

**Days 3-4 (Sun-Mon):**
- Developer A: Fix safety manager + synthetic data = 2-3 hours
- Developer B: LLM Factory + API endpoints = 4-6 hours

**Day 5 (Tue):**
- Developer A: Add Playwright (if time) = 1-2 hours
- Developer B: BYOM testing and documentation = 2 hours
- Both: Integration and sprint wrap-up

### Week 2 (Jan 22-26)
**Contingency week** - Handle any blockers, complete testing, prepare for Sprint 2.9

---

## Success Criteria

### Minimum (Must Have):
- ✅ PnL calculation tests fixed (2 tests) - **CRITICAL FOR PRODUCTION**
- ✅ Seed data isolation fixed (11 tests) - **CRITICAL FOR TEST STABILITY**
- ✅ Test pass rate ≥ 95% (629+ tests)
- ✅ BYOM database schema created and migrated
- ✅ BYOM encryption service implemented

### Target (Should Have):
- ✅ Safety manager test fixed (1 test)
- ✅ Synthetic data test fixed (1 test)
- ✅ Test pass rate ≥ 98% (646+ tests)
- ✅ BYOM LLM Factory implemented (OpenAI + Google)
- ✅ BYOM API endpoints created

### Stretch (Nice to Have):
- ✅ Playwright tests enabled (3 tests)
- ✅ Test pass rate = 100% (661 tests)
- ✅ BYOM API fully tested
- ✅ BYOM frontend wireframes created

---

## Risk Management

### Known Risks:

**Risk 1: PnL Calculation Complex**
- **Likelihood:** Medium
- **Impact:** High (blocks production)
- **Mitigation:** 
  - Allocate 6 hours (upper estimate)
  - Request peer review from Developer B (agent uses trading data)
  - Document calculation thoroughly

**Risk 2: Test Fixes Create Regressions**
- **Likelihood:** Low
- **Impact:** Medium
- **Mitigation:**
  - Run full test suite after each fix
  - Use UUID pattern proven in Sprint 2.7
  - Follow established patterns from conftest.py

**Risk 3: BYOM Scope Creep**
- **Likelihood:** Medium
- **Impact:** Low (well-defined requirements)
- **Mitigation:**
  - Stick to Sprint 2.8 scope (foundation only)
  - Defer UI work to Sprint 2.10
  - Follow BYOM_USER_STORIES.md strictly

---

## Testing Strategy

### After Each Fix (Developer A):

```bash
# 1. Test specific fix
docker compose run backend pytest path/to/test::test_name -v

# 2. Test related module
docker compose run backend pytest path/to/module/ -v

# 3. Full regression check
docker compose run backend pytest -v

# 4. Record new pass rate
# Update CURRENT_SPRINT.md with results
```

### After BYOM Changes (Developer B):

```bash
# 1. Test database migration
docker compose run backend alembic upgrade head

# 2. Test new models
docker compose run backend pytest tests/models/ -v

# 3. Test new API endpoints
docker compose run backend pytest tests/api/ -v -k "llm"

# 4. Full agent tests (ensure no regressions)
docker compose run backend pytest tests/services/agent/ -v
```

---

## Communication Protocol

### Daily Updates:
- Post test results to #sprint-updates channel
- Report blockers immediately
- Share insights across tracks

### Mid-Sprint Check-in (Day 3):
- Review progress vs. plan
- Adjust priorities if needed
- Identify any scope changes

### Sprint End Review (Day 5):
- Final test run and results
- Documentation updates
- Sprint retrospective
- Plan Sprint 2.9

---

## Documentation Updates Required

### During Sprint:
- [ ] Update CURRENT_SPRINT.md with daily progress
- [ ] Create BYOM implementation notes
- [ ] Document any PnL calculation insights

### End of Sprint:
- [ ] Create Sprint 2.8 completion report (follow Sprint 2.7 template)
- [ ] Update ROADMAP.md with new test pass rate
- [ ] Archive Sprint 2.8 work in docs/archive/history/sprints/sprint-2.8/
- [ ] Update PROJECT_HANDOFF.md with BYOM status

---

## Next Sprint Preview (Sprint 2.9)

**Planned Focus:** BYOM Agent Integration (16-20 hours)

**Objectives:**
- Refactor AgentOrchestrator to use LLM Factory
- Add Anthropic Claude support
- Implement prompt template management
- Add session-level model selection
- Complete integration testing

**Depends On:**
- ✅ Sprint 2.8 BYOM foundation complete
- ✅ All high-priority test fixes complete
- ✅ Database schema migrated

---

## Approval & Sign-off

### Sprint 2.8 Authorization:

**Approved by:** [Project Owner]  
**Date:** [TBD]  
**Start Date:** January 17, 2026  
**End Date:** January 26, 2026 (2 weeks, 1 week contingency)

### Ready to Start Checklist:

- ✅ Sprint 2.7 complete and archived
- ✅ All prompts prepared for Developer A
- ✅ BYOM requirements documented
- ✅ AWS staging environment stable
- ✅ No critical blockers
- ✅ Developers available and briefed

**Status: READY TO START** 🚀

---

**Generated:** 2026-01-17  
**Sprint:** 2.8 - Test Stabilization + BYOM Foundation  
**Project:** Oh My Coins (OMC)
