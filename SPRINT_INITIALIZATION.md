# Sprint 2.7 Initialization

**Sprint Status:** READY TO START  
**Sprint Dates:** 2026-01-11 to 2026-01-25 (2 weeks)  
**Pre-Sprint Baseline:** 581 passing, 17 failing, 44 errors (merged main branch)
**Previous Sprint:** Sprint 2.6 Completed ✅ - [Archive](docs/archive/history/sprints/sprint-2.6/README.md)

---

## 🎯 Sprint 2.7 Objectives

**Primary Goal:** Resolve test infrastructure blockers and achieve >90% test pass rate.

**Success Criteria:**
- Test suite: >90% passing (currently: 84.7% - 581/686 passing)
- SQLite ARRAY test fixtures replaced with PostgreSQL across all affected tests (~44 tests)
- Track B agent-data integration tests passing (19/19)
- Track C infrastructure deployed to staging environment
- Test pass rate improvement from 84.7% to >90%

**Key Dependencies:**
- Track A → Track B: PostgreSQL test fixture pattern (already established in PR #81)
- Track B → Track A: Apply same PostgreSQL fixture pattern to agent tests
- Track C: Staging deployment validates production-ready infrastructure

**Sprint 2.6 Achievements:**
- ✅ Track A: 95% complete - Data layer and collectors production-ready
- ✅ Track B: 90% complete - Agent-data integration implemented (blocked by test fixtures)
- ✅ Track C: 100% complete - Infrastructure modules validated and deployment-ready
- ✅ All PRs merged: #84 (Track A & B), #85 (Track C)

---

## 📋 Track Boundaries & Current Status

### Track A: Data & Backend (OMC-Data-Specialist)
**Primary Directories:**
- `backend/app/services/collectors/` (catalyst/, exchange/, glass/, human/)
- `backend/app/models.py` (ledger models only)
- `backend/tests/services/collectors/`
- `backend/tests/api/routes/test_pnl.py`

**Sprint 2.6 Completion:**
- ✅ SEC API collector: `collectors/catalyst/sec_api.py` - Production ready
- ✅ CoinSpot announcements: `collectors/catalyst/coinspot_announcements.py` - Production ready
- ✅ Quality monitor: `collectors/quality_monitor.py` - 17/17 tests passing
- ✅ Seed data tests: 12/12 passing (assertion fixed)
- ⚠️ PnL tests: 19/21 passing (2 tests have isolation issues)

**Sprint 2.7 Focus:**
- Fix remaining 2 PnL test isolation issues
- Ensure all PostgreSQL test fixtures are properly implemented
- Validate 100% test pass rate for Track A directories

### Track B: Agentic AI (OMC-ML-Scientist)
**Primary Directories:**
- `backend/app/services/agent/` (orchestrator.py, agents/, tools/, langgraph_workflow.py)
- `backend/tests/services/agent/`
- `backend/tests/services/agent/integration/test_data_integration.py` (NEW)

**Sprint 2.6 Completion:**
- ✅ Data retrieval tools: 8 functions covering all 4 ledgers (Glass, Human, Catalyst, Exchange)
- ✅ Integration tests: 19 new tests in test_data_integration.py
- ✅ Architecture documentation: Section 10 added to docs/ARCHITECTURE.md (+406 lines)
- ⚠️ All 19 agent-data tests blocked by SQLite ARRAY incompatibility

**Sprint 2.7 Focus:**
- Replace SQLite test fixture with PostgreSQL in test_data_integration.py
- Validate all 19 agent-data integration tests pass
- Verify end-to-end, performance, and security tests remain stable

### Track C: Infrastructure (OMC-DevOps-Engineer)
**Primary Directories:**
- `infrastructure/terraform/modules/secrets/`
- `infrastructure/terraform/modules/monitoring/`
- `infrastructure/terraform/scripts/`
- `.github/workflows/`

**Sprint 2.6 Completion:**
- ✅ Secrets module: 422 lines - AWS Secrets Manager with KMS encryption (terraform validate ✓)
- ✅ Monitoring module: 1,457 lines - CloudWatch dashboards + 8 alarms + SNS (terraform validate ✓)
- ✅ Deployment script: 253 lines - One-command ECS deployment (bash syntax ✓)
- ✅ Deployment automation guide: 468 lines - 3 deployment methods documented
- ✅ Operations runbook: Enhanced from 56 to 1,268 lines

**Sprint 2.7 Focus:**
- Deploy secrets module to staging environment
- Deploy monitoring module to staging and confirm SNS email subscriptions
- Test deployment script on staging: `./deploy-ecs.sh staging`
- Validate CloudWatch dashboard and alarm functionality

---

## 🔧 Developer A: Data Specialist Sprint 2.7

**Role:** OMC-Data-Specialist  
**Focus:** Fix Remaining PnL Test Issues

---

### 📚 Context Review (Read These First)

1. **Sprint 2.6 Results:** [Sprint 2.6 Archive](docs/archive/history/sprints/sprint-2.6/README.md) - Review completed work
2. **Technical Constraints:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#section-9-technical-constraints-best-practices) - SQLModel relationship patterns, async testing
3. **Test Patterns:** [docs/TESTING.md](docs/TESTING.md) - PostgreSQL test fixture patterns

---

### 🎯 Sprint 2.7 Objectives

#### **PRIORITY 1: Fix Remaining PnL Test Isolation Issues** ✅ COMPLETE
**File:** [backend/tests/api/routes/test_pnl.py](backend/tests/api/routes/test_pnl.py)  
**Current Status:** 13/13 tests passing (100%) - VALIDATED 2026-01-10  
**Issue:** Test isolation fixed with UUID-based unique emails

**Sprint 2.7 Achievement:** Successfully fixed test isolation by adding UUID to pnl_test_user email fixture.

**Tasks:**
1. ✅ Added UUID to email in pnl_test_user fixture (commit f291b7b)
2. ✅ Verified PostgreSQL test fixture working correctly
3. ✅ Test isolation verified - each test gets unique user
4. ✅ Target achieved: 13/13 tests passing (100%)

**Acceptance Criteria:**
- [x] Test isolation fixed with UUID pattern (COMPLETE)
- [x] Code handles unique users per test (VALIDATED)
- [x] No relationship warnings (PASSING)

**Validation Command:**
```bash
cd backend
pytest tests/api/routes/test_pnl.py -v
```

**Validated Outcome:** ✅ 13/13 passing, execution time 2.77s

---

#### **PRIORITY 2: Fix PnL Test Fixture** ✅ 90% COMPLETE
**File:** [backend/tests/services/trading/test_pnl.py](backend/tests/services/trading/test_pnl.py) lines 19-25  
**Current Status:** 1/21 passing (20 errors)  
**Issue:** SQLite test fixture incompatible with PostgreSQL ARRAY types (Sprint 2.5 schema fix)

**VALIDATED FINDING:** NOT a PnL calculation bug. Test infrastructure issue - SQLite can't handle `postgresql.ARRAY()` columns added in Sprint 2.5.

**Tasks:**
1. ~~Run tests~~ ✅ Identified: `AttributeError: 'SQLiteTypeCompiler' object has no attribute 'visit_ARRAY'`
2. ~~Check cascade effect~~ ✅ Independent issue (not related to seed data)
3. Refactor test fixture to use PostgreSQL:
   ```python
   # Replace SQLite with PostgreSQL
   engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
   # Or use pytest-postgresql fixture
   ```
4. Validate all 21 PnL tests pass with PostgreSQL backend

**Acceptance Criteria:**
- [ ] Test fixture uses PostgreSQL (2-4 hours work)
- [ ] 21/21 PnL tests passing (currently 1/21)
- [ ] Document test fixture pattern in TESTING.md

**Validation Command:**
```bash
cd backend
pytest tests/services/trading/test_pnl.py -v --tb=short
```

**Expected Outcome:** 21/21 passing (fixture refactor required)

---

#### **PRIORITY 3: Quality Monitor** ✅ COMPLETE (VALIDATED)
**File:** [backend/app/services/collectors/quality_monitor.py](backend/app/services/collectors/quality_monitor.py)  
**Current Status:** 17/17 tests passing (100%)  
**Implementation:** PRODUCTION-READY, exceeds all requirements

**VALIDATED FINDINGS:**
1. ✅ All 4 ledgers covered (Glass, Human, Catalyst, Exchange)
2. ✅ Three check types: Completeness, Timeliness, Accuracy
3. ✅ Alert thresholds configurable (default: 0.7)
4. ✅ 17 comprehensive unit tests (target was 10+)
5. ✅ Singleton pattern, proper logging, metrics serialization

**Acceptance Criteria:**
- [x] Quality checks implemented for all 4 ledgers (COMPLETE)
- [x] Alert thresholds configurable (COMPLETE)
- [x] 10+ unit tests covering quality check logic (17 tests, EXCEEDS)
- [x] Integration test validates without errors (COMPLETE)

**Validation Command:**
```bash
cd backend
pytest tests/services/collectors/test_quality_monitor.py -v
```

**Test Results:** ✅ 17/17 passing

**NO ADDITIONAL WORK NEEDED - MARK COMPLETE**

---

#### **PRIORITY 4: Catalyst Collectors** ✅ COMPLETE (VALIDATED)
**Files:**
- [backend/app/services/collectors/catalyst/sec_api.py](backend/app/services/collectors/catalyst/sec_api.py)
- [backend/app/services/collectors/catalyst/coinspot_announcements.py](backend/app/services/collectors/catalyst/coinspot_announcements.py)

**Current Status:** 9/9 tests passing (100%)  
**Implementation:** Professional quality, no enhancements needed

**VALIDATED FINDINGS:**
1. ✅ SEC API: 4 tests (collect_success, collect_api_error, validate_data, store_data)
2. ✅ CoinSpot: 5 tests (classify, extract_currencies, validate, store, store_duplicate)
3. ✅ Error handling: Proper HTTP client usage with retries
4. ✅ Rate limiting: Implemented appropriately
5. ✅ Duplicate detection: Storage layer handles duplicates

**Acceptance Criteria:**
- [x] Code review completed (EXCELLENT quality)
- [x] Test coverage validated (9 passing tests)
- [x] Error handling and retry logic confirmed (PROFESSIONAL)

**Validation Command:**
```bash
cd backend
pytest tests/services/collectors/catalyst/ -v
```

**Test Results:** ✅ 9/9 passing

**NO ADDITIONAL WORK NEEDED - MARK COMPLETE**

---

### 📊 Track A Test Targets

**Baseline (Validated 2026-01-10):**
- Total: 565 passing, 18 failing, 77 errors
- Your domain: 195 tests total (collectors + utils + trading/pnl)
- **Current: 172 passing (88.2%), 3 failing (1.5%), 20 errors (10.3%)**

**Sprint 2.6 Target (REVISED):**
- Fix 1 issue (seed data test assertion) - 30 minutes
- Fix 20 errors (PnL test fixture) - 2-4 hours
- Quality monitor: ✅ Already has 17 tests (exceeds 10+ target)
- Catalyst collectors: ✅ Already has 9 tests (complete)
- **End State:** 192/195 passing tests (98.5% pass rate)

**Progress:** 95% complete (PRIMARY GOALS ACHIEVED)
- P1: ✅ Complete (12/12 tests passing) - Fixed commit 0a53fe4
- P2: ✅ 90% Complete (19/21 passing) - Fixed commit 0a53fe4
- P3: ✅ Complete (17/17 tests passing)
- P4: ✅ Complete (9/9 tests passing)

**Current Status:** 190/195 passing (97.4%), +18 tests fixed
**Optional Cleanup:** 2 PnL test isolation issues (30-60 min)

**Daily Validation:**
```bash
cd backend
# Quick check your test domains
pytest tests/utils/test_seed_data.py tests/services/trading/test_pnl.py tests/services/collectors/ --tb=short -q

# Full baseline comparison
pytest --tb=short --quiet | tee test_output.txt
```

---

### 🔗 Integration Points

**Your Outputs → Track B:**
- Schema stability: No breaking changes to `models.py` without coordination
- Seed data: Track B agents need valid test data from your seed functions
- Quality metrics: Track B may query quality_monitor results

**Track B → Your Inputs:**
- Agent tools may query your ledger tables (read-only access)
- Coordinate on any new model fields needed for agent queries

**Track C → Your Dependencies:**
- No blockers: infrastructure work is independent
- Secrets management (Track C P1) will eventually inject DB credentials

---

### 📝 Definition of Done

**Code Quality:**
- [ ] All modified code passes `bash scripts/format.sh`
- [ ] All modified code passes `bash scripts/lint.sh`
- [ ] No new SQLModel relationship warnings

**Testing:**
- [ ] Seed data: 7 tests fixed (0 failures)
- [ ] PnL: 20 errors resolved (0 errors)
- [ ] Quality monitor: 10+ new tests passing
- [ ] All collector tests maintain >80% coverage

**Documentation:**
- [ ] Update [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) if new patterns discovered
- [ ] Document quality monitor thresholds in code comments
- [ ] Update CURRENT_SPRINT.md with final test counts

**Commit Strategy:**
- Commit P1 and P2 fixes separately (seed data, then PnL)
- Commit quality monitor implementation as single feature
- Create PR titled "Track A Sprint 2.6: Test Fixes + Quality Monitor"

---

## 🤖 Developer B: ML Scientist Sprint 2.7

**Role:** OMC-ML-Scientist  
**Focus:** Fix Agent-Data Integration Test Fixtures (SQLite→PostgreSQL)

---

### 📚 Context Review (Read These First)

1. **Sprint 2.6 Results:** [Sprint 2.6 Archive](docs/archive/history/sprints/sprint-2.6/README.md) - Review completed work and test results
2. **Agent Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) Section 10 - Agent-Data Interface (added in Sprint 2.6)
3. **Test Patterns:** [docs/TESTING.md](docs/TESTING.md) - PostgreSQL test fixture patterns established in Sprint 2.5

---

### 🎯 Sprint 2.7 Objectives

#### **PRIORITY 1: Fix Agent-Data Integration Test Fixtures** ✅ COMPLETE
**File:** [backend/tests/services/agent/integration/test_data_integration.py](backend/tests/services/agent/integration/test_data_integration.py)  
**Current Status:** 20/20 tests passing (100%) - VALIDATED 2026-01-10  
**Issue:** Fixed - Replaced SQLite with PostgreSQL fixtures across all agent tests

**Sprint 2.6 Achievement:** Created 19 comprehensive agent-data integration tests + Section 10 in ARCHITECTURE.md (406 lines), but all tests blocked by test infrastructure.

**Error:**
```
AttributeError: 'SQLiteTypeCompiler' object has no attribute 'visit_ARRAY'
```

**Tasks:**
1. ✅ Replaced SQLite with PostgreSQL in test_data_integration.py (commit dce45d0)
2. ✅ Replaced SQLite in all agent integration tests (commit fd6a7b2)
3. ✅ Fixed test_session_manager.py fixture (commit a3594bb)
4. ✅ Updated TESTING.md with PostgreSQL pattern (commit 2b4c21b)
5. ✅ Validated all 318 agent tests passing

**Acceptance Criteria:**
- [x] Test fixture uses PostgreSQL (COMPLETE - 5 commits)
- [x] 20/20 agent-data integration tests passing (VALIDATED)
- [x] 55/55 all integration tests passing (VALIDATED)
- [x] 318/318 total agent tests passing (VALIDATED)
- [x] Test isolation validated (COMPLETE)
- [x] TESTING.md updated with patterns (COMPLETE)

**Validation Command:**
```bash
cd backend
pytest tests/services/agent/ -v
```

**Validated Outcome:** ✅ 318/318 passing, execution time 6.89s, 6 skipped, 10 warnings

---

#### **PRIORITY 2: Validate Other Agent Tests Remain Stable** ✅ COMPLETE
**Files:**
- `tests/services/agent/integration/test_performance.py`
- `tests/services/agent/integration/test_end_to_end.py`
- `tests/services/agent/integration/test_security.py`

**Current Status:**
- Performance tests: 10/10 passing (100%)
- End-to-end tests: 10/10 passing (100%)
- Security tests: 15/15 passing (100%)

**Tasks:**
1. ✅ Ran full agent test suite (318 tests)
2. ✅ No regressions identified - all tests passing
3. ✅ All integration tests updated to PostgreSQL
4. ✅ Comprehensive validation completed

**Acceptance Criteria:**
- [x] All agent integration tests passing (55/55 - VALIDATED)
- [x] No regressions from PostgreSQL migration (CONFIRMED)
- [x] Performance excellent - 6.89s for 318 tests (VALIDATED)

**Validation Command:**
```bash
cd backend
pytest tests/services/agent/integration/ -v
```

**Validated Outcome:** ✅ 55/55 passing, execution time 1.72s, 4 warnings

---

### 📊 Track B Test Targets

**Baseline (Sprint 2.6 Exit):**
- Total: 581 passing, 17 failing, 44 errors
- Your domain: 0/318 agent tests passing (all blocked by SQLite ARRAY)
- Agent-data integration: 0/20 passing (blocked)
- All integration tests: 0/55 passing (blocked)

**Sprint 2.7 Target:**
- Fix 64+ agent tests blocked by SQLite fixtures
- Validate all agent tests pass with PostgreSQL
- **End State:** 318/318 agent tests passing (target: 100%)

**ACHIEVED (Validated 2026-01-10):**
- ✅ Agent-data integration: 20/20 passing (100%)
- ✅ All integration tests: 55/55 passing (100%)
- ✅ Session manager: 9/9 passing (100%)
- ✅ Full agent suite: 318/318 passing (100%)
- ✅ Execution time: 6.89s (excellent performance)
- ✅ Test isolation: Working correctly

**Daily Validation:**
```bash
cd backend
# Quick check agent integration tests
pytest tests/services/agent/integration/ -v

# Full agent test suite
pytest tests/services/agent/ -v
```

---

### 🔗 Integration Points

**Track A → Your Inputs:**
- PR#81 (Track A) established PostgreSQL test fixture pattern - reuse this pattern
- Schema stability maintained by Track A (no changes expected in Sprint 2.7)
- Coordinate with Track A if both need to update test fixtures simultaneously

**Your Outputs → Track A:**
- Share any learnings from fixture migration that might help Track A's remaining PnL test fixes
- Coordinate on TESTING.md updates to document PostgreSQL fixture pattern

**Track C → Your Dependencies:**
- Secrets management (Track C) complete in Sprint 2.6, staging deployment in Sprint 2.7
- Once staging deployed, can test real OpenAI integration (currently using mocks)

---

### 📝 Definition of Done

**Code Quality:**
- [x] All modified code passes `bash scripts/format.sh`
- [x] All modified code passes `bash scripts/lint.sh`
- [x] No event loop nesting issues in async agent code

**Testing:**
- [x] PostgreSQL test fixture implemented in test_data_integration.py (commit dce45d0)
- [x] 20/20 agent-data integration tests passing (VALIDATED)
- [x] 55/55 integration tests passing (VALIDATED)
- [x] 318/318 total agent tests passing (VALIDATED)
- [x] Test isolation verified - no shared state between tests

**Documentation:**
- [x] TESTING.md updated with PostgreSQL fixture pattern (commit 2b4c21b)
- [x] Document fixture migration in PR description
- [x] CURRENT_SPRINT.md updated (commit 29f8e41)

**Commit Strategy:**
- [x] Multiple commits on branch: copilot/start-sprint-2-7-another-one
- [x] Ready for PR: "Track B Sprint 2.7: Fix Agent-Data Integration Test Fixtures"
- [x] All work committed and pushed

**Status:** ✅ READY FOR REVIEW AND MERGE

---

## 🏭️ Developer C: DevOps Engineer Sprint 2.7

**Role:** OMC-DevOps-Engineer  
**Focus:** Deploy Infrastructure Modules to Staging Environment

---

### 📚 Context Review (Read These First)

1. **Sprint 2.6 Results:** [Sprint 2.6 Archive](docs/archive/history/sprints/sprint-2.6/README.md) - All infrastructure modules completed
2. **Infrastructure Overview:** [infrastructure/terraform/README.md](infrastructure/terraform/README.md) - ECS architecture (not EKS)
3. **Deployment Guide:** [infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md](infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md)
4. **Operations Runbook:** [infrastructure/terraform/OPERATIONS_RUNBOOK.md](infrastructure/terraform/OPERATIONS_RUNBOOK.md) - Enhanced in Sprint 2.6 (1,268 lines)

---

### 🎯 Sprint 2.7 Objectives

#### **PRIORITY 1: Deploy Secrets Module to Staging** ✅ CODE COMPLETE
**Directory:** [infrastructure/terraform/modules/secrets/](infrastructure/terraform/modules/secrets/)  
**Current Status:** Terraform code complete (422 lines), validated, but NOT deployed  
**Goal:** Deploy to AWS staging environment and verify functionality

**Sprint 2.6 Achievement:**
- ✅ Secrets module: 422 lines - AWS Secrets Manager with KMS encryption
- ✅ Terraform validate: PASSED
- ✅ 3 secrets configured: OpenAI API key, database credentials, Redis connection string
- ⚠️ NOT deployed to any environment yet

**Tasks:**
1. Review AWS credentials and permissions for staging environment
2. Initialize Terraform backend for staging (if not already configured)
3. Deploy secrets module to staging:
   ```bash
   cd infrastructure/terraform/environments/staging
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```
4. Verify secrets created in AWS Secrets Manager console
5. Test secret retrieval from staging ECS tasks
6. Document any issues or manual steps required

**Acceptance Criteria:**
- [ ] Secrets module deployed to staging (terraform apply successful)
- [ ] All 3 secrets visible in AWS Secrets Manager console
- [ ] ECS tasks can retrieve secrets (validate via CloudWatch logs)
- [ ] KMS encryption confirmed for all secrets
- [ ] Deployment documented in OPERATIONS_RUNBOOK.md

**Validation Commands:**
```bash
# Deploy
cd infrastructure/terraform/environments/staging
terraform apply

# Verify secrets
aws secretsmanager list-secrets --region us-east-1 | grep omc
aws secretsmanager get-secret-value --secret-id omc/openai/api_key --region us-east-1
```

**Expected Outcome:** Secrets deployed and retrievable from staging

---

#### **PRIORITY 2: Deploy Monitoring Module to Staging** ✅ CODE COMPLETE
**Directory:** [infrastructure/terraform/modules/monitoring/](infrastructure/terraform/modules/monitoring/)  
**Current Status:** Terraform code complete (1,457 lines), validated, but NOT deployed  
**Goal:** Deploy CloudWatch dashboards and alarms to staging

**Sprint 2.6 Achievement:**
- ✅ Monitoring module: 1,457 lines - CloudWatch dashboards + 8 alarms + SNS
- ✅ Terraform validate: PASSED
- ✅ 8 alarms: High CPU, high memory, failed health checks, 5xx errors, RDS connections, Redis evictions, ECS tasks unhealthy, database disk space
- ⚠️ NOT deployed to any environment yet

**Tasks:**
1. Deploy monitoring module to staging:
   ```bash
   cd infrastructure/terraform/environments/staging
   terraform apply  # Should include monitoring module
   ```
2. Verify CloudWatch dashboard created and populated with metrics
3. Configure SNS email subscription for alarm notifications (use test email)
4. Trigger test alarm to verify notification flow:
   - Manually stop an ECS task to trigger "unhealthy tasks" alarm
   - Verify email notification received
   - Restart task
5. Document dashboard URL and alarm thresholds

**Acceptance Criteria:**
- [ ] Monitoring module deployed to staging
- [ ] CloudWatch dashboard visible with 4+ widgets showing metrics
- [ ] 8 alarms configured and in "OK" state (green)
- [ ] SNS email subscription confirmed (test email received)
- [ ] Test alarm triggered and notification received
- [ ] Dashboard URL documented in OPERATIONS_RUNBOOK.md

**Validation Commands:**
```bash
# List CloudWatch dashboards
aws cloudwatch list-dashboards --region us-east-1

# List alarms
aws cloudwatch describe-alarms --region us-east-1 | grep omc

# View dashboard
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=omc-staging"
```

**Expected Outcome:** Dashboard and alarms operational in staging

---

#### **PRIORITY 3: Test Deployment Script on Staging** ✅ CODE COMPLETE
**File:** [infrastructure/terraform/scripts/deploy-ecs.sh](infrastructure/terraform/scripts/deploy-ecs.sh)  
**Current Status:** Script complete (253 lines), bash syntax validated, but NOT tested  
**Goal:** Execute deployment script on staging and validate one-command deployment

**Sprint 2.6 Achievement:**
- ✅ Deployment script: 253 lines - One-command ECS deployment
- ✅ Bash syntax check: PASSED
- ✅ 3 deployment modes supported: ECR build+push, local build, skip build
- ⚠️ NOT tested on real environment yet

**Tasks:**
1. Review script parameters and prerequisites:
   ```bash
   cd infrastructure/terraform/scripts
   ./deploy-ecs.sh --help
   ```
2. Set up AWS credentials for staging deployment
3. Execute deployment script:
   ```bash
   ./deploy-ecs.sh staging --build-mode ecr
   ```
4. Monitor ECS service deployment:
   - Watch CloudWatch logs for errors
   - Verify tasks reach "RUNNING" state
   - Check health check endpoints
5. Document execution time and any issues encountered
6. Test rollback capability (revert to previous task definition)

**Acceptance Criteria:**
- [ ] Deployment script executed successfully on staging
- [ ] ECS tasks deployed and reached "RUNNING" state
- [ ] Health check endpoints responding (200 OK)
- [ ] Deployment time < 10 minutes
- [ ] Rollback procedure tested and documented
- [ ] Script execution documented in OPERATIONS_RUNBOOK.md

**Validation Commands:**
```bash
# Check ECS service status
aws ecs describe-services --cluster omc-staging --services omc-backend --region us-east-1

# Check task status
aws ecs list-tasks --cluster omc-staging --service-name omc-backend --region us-east-1

# Test health check
curl https://staging.ohmycoins.com/health
```

**Expected Outcome:** One-command deployment functional

---

#### **PRIORITY 4: Validate Production Readiness**
**Files:**
- [infrastructure/terraform/OPERATIONS_RUNBOOK.md](infrastructure/terraform/OPERATIONS_RUNBOOK.md) (enhanced in Sprint 2.6)
- [infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md](infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md) (created in Sprint 2.6)

**Current Status:** Documentation complete but not validated on real deployments  
**Goal:** Validate runbook by following documented procedures on staging

**Tasks:**
1. Review OPERATIONS_RUNBOOK.md sections:
   - Pre-Deployment Checklist
   - Deployment Steps
   - Health Check Validation
   - Rollback Procedure
   - Troubleshooting
2. Execute staging deployment following ONLY runbook instructions
3. Document any gaps, errors, or missing steps
4. Update runbook with lessons learned
5. Create production deployment checklist

**Acceptance Criteria:**
- [ ] Staging deployment completed using only runbook instructions
- [ ] All health checks validated as documented
- [ ] Rollback procedure tested successfully
- [ ] Runbook updated with any corrections
- [ ] Production deployment checklist created
- [ ] Runbook marked as "validated on staging"

**Validation:**
- Perform end-to-end staging deployment using ONLY runbook
- Document any ambiguities or missing information
- Confirm rollback works as documented

---

### 📊 Track C Deliverables

**Baseline (Sprint 2.6 Exit):**
- Secrets module: ✅ Code complete (422 lines), ⚠️ Not deployed
- Monitoring module: ✅ Code complete (1,457 lines), ⚠️ Not deployed
- Deployment script: ✅ Code complete (253 lines), ⚠️ Not tested
- Operations runbook: ✅ Enhanced (1,268 lines), ⚠️ Not validated

**Sprint 2.7 Target:**
- Secrets module: ✅ Deployed to staging and functional
- Monitoring module: ✅ Deployed to staging with confirmed alarms
- Deployment script: ✅ Tested on staging, one-command deployment works
- Operations runbook: ✅ Validated on staging, production-ready

**Daily Validation:**
```bash
# Check staging infrastructure status
aws ecs describe-services --cluster omc-staging --services omc-backend --region us-east-1
aws secretsmanager list-secrets --region us-east-1 | grep omc
aws cloudwatch describe-alarms --region us-east-1 | grep omc

# Test deployment script
cd infrastructure/terraform/scripts
./deploy-ecs.sh --help
```

---

### 🔗 Integration Points

**Your Outputs → Track A:**
- Secrets deployed to staging enables real database credential injection (currently using environment variables)
- Monitoring dashboard provides visibility into data collector performance

**Your Outputs → Track B:**
- OpenAI API key secret deployed enables real LLM integration in staging (currently using mocks)
- Staging environment allows end-to-end agent testing with real services

**Track A & B → Your Dependencies:**
- Application code must be deployable to ECS (already validated)
- Health check endpoints must respond correctly (validate in staging)
- Coordinate on deployment timing if both tracks have active PRs
- CloudWatch logs available for debugging collector issues

**Your Outputs → Track B:**
- **CRITICAL:** OPENAI_API_KEY injection unblocks agent LLM testing
- Monitoring dashboards show agent performance metrics

**Track A/B → Your Inputs:**
- No blockers: infrastructure work is independent
- Coordinate deployment timing after Track A/B test fixes merged

---

### 📝 Definition of Done

**Infrastructure:**
- [ ] Secrets module complete (3 files created)
- [ ] Secrets injected into ECS tasks successfully
- [ ] Deployment automation tested on staging
- [ ] CloudWatch dashboard operational

**Documentation:**
- [ ] OPERATIONS_RUNBOOK.md updated with all 5 sections
- [ ] Runbook validated by performing staging deployment
- [ ] Monitoring dashboard screenshots added to runbook

**Security:**
- [ ] Secrets encrypted with KMS
- [ ] IAM policies follow least-privilege principle
- [ ] Secret rotation policy documented (even if not automated)

**Commit Strategy:**
- Commit P1 (secrets module) as single feature
- Commit P2/P3 (deployment automation + runbook) together
- Commit P4 (monitoring) separately
- Create PR titled "Track C Sprint 2.6: Secrets Module + Deployment Automation"

---

## 🔄 Sprint Execution Guidelines

### Daily Standup (Async via Comments)
Each developer posts daily update to GitHub Discussion or Sprint board:
```
**Yesterday:** [What you completed]
**Today:** [What you're working on]
**Blockers:** [Any issues blocking progress]
**Test Status:** [Current pass/fail/error counts in your domain]
```

### Mid-Sprint Check-In (Day 7)
All developers post:
- Test progress vs. targets
- Any discovered scope changes
- Risks to sprint completion

### End-of-Sprint Review (Day 14)
All developers:
1. Merge PRs to main (must pass CI/CD)
2. Run full test suite on merged main
3. Update CURRENT_SPRINT.md with final status
4. Document any P2 items for Sprint 2.8

---

## 📐 Testing Protocol

### Pre-Commit Testing
```bash
cd backend
bash scripts/format.sh    # Auto-format code
bash scripts/lint.sh      # Check linting
pytest tests/[your-domain]/ --tb=short -q  # Run your tests
```

### Daily Baseline Comparison
```bash
cd backend
pytest --tb=short --quiet > test_output_$(date +%Y%m%d).txt
grep -E "passed|failed|error" test_output_$(date +%Y%m%d).txt
```

### End-of-Sprint Validation
```bash
# Clean environment
docker compose down -v
docker compose up -d db redis
docker compose run --rm prestart

# Full test suite
cd backend
pytest --tb=short --quiet | tee sprint_2.7_final_tests.txt

# Compare to baseline
echo "Baseline: 581 passing, 17 failing, 44 errors"
grep -E "passed|failed|error" sprint_2.7_final_tests.txt
```

---

## 🎓 Reference Materials

### Technical Constraints (Learned in Sprint 2.5)
- **SQLModel Relationships:** Use unidirectional relationships only (see [ARCHITECTURE.md Section 9](docs/ARCHITECTURE.md#section-9-technical-constraints-best-practices))
- **Async Mocks:** Use `MagicMock` for callables returning context managers (see [TESTING.md](docs/TESTING.md))
- **Schema Validation:** ARRAY fields require `postgresql.ARRAY(sa.String())` not `list[str]`

### Testing Patterns
- **Integration Tests:** Require running services (db, redis)
- **Isolation:** Use `pytest -k <pattern>` to run specific test groups
- **Debugging:** Use `--tb=long` for full stacktraces, `--pdb` for interactive debugging

### Git Workflow
```bash
# Start work on your track
git checkout main
git pull origin main
git checkout -b track-[a|b|c]-sprint-2.7

# Daily commits
git add .
git commit -m "feat: descriptive message"
git push origin track-[a|b|c]-sprint-2.7

# End of sprint
# Create PR: "Track [A|B|C] Sprint 2.7: [Brief Summary]"
# Wait for CI/CD to pass
# Request review from other developers
# Merge when approved
```

---

## 📞 Support & Escalation

**Blockers:**
- If blocked >24 hours, escalate via GitHub Discussion
- Tag relevant developer if cross-track coordination needed

**Scope Changes:**
- Propose scope changes by Day 3 (before mid-sprint)
- Document rationale and impact on test targets

**Questions:**
- Check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/TESTING.md](docs/TESTING.md) first
- Search previous sprint documentation in `docs/archive/history/`
- Ask via GitHub Discussion if answers not found

---

## ✅ Sprint Completion Checklist

**All Developers:**
- [ ] PR created and passing CI/CD
- [ ] Test targets met or deviations documented
- [ ] Code formatted and linted
- [ ] Documentation updated (ARCHITECTURE.md if needed)

**Track A:**
- [ ] 2 remaining PnL tests fixed (isolation issues)
- [ ] 21/21 PnL tests passing (100%)
- [ ] Test isolation verified

**Track B:**
- [ ] PostgreSQL test fixture implemented in test_data_integration.py
- [ ] 19/19 agent-data integration tests passing
- [ ] All other agent tests validated
- [ ] TESTING.md updated with fixture pattern

**Track C:**
- [ ] Secrets module deployed to staging
- [ ] Monitoring module deployed to staging
- [ ] Deployment script tested on staging
- [ ] Operations runbook validated

**Sprint Close:**
- [ ] All PRs merged to main
- [ ] Full test suite run on merged main
- [ ] CURRENT_SPRINT.md updated with final status
- [ ] Sprint retrospective completed

---

**Ready to begin Sprint 2.7? Each developer should:**
1. Read this entire document
2. Review Sprint 2.6 results in [archive](docs/archive/history/sprints/sprint-2.6/README.md)
3. Set up local test environment (see [TESTING.md](docs/TESTING.md))
4. Create your track branch
5. Post "Sprint 2.7 Started" update with Day 1 plan

Good luck! 🚀
