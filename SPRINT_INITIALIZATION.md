# Sprint 2.6 Initialization

**Sprint Status:** READY TO START  
**Sprint Dates:** 2026-01-10 to 2026-01-24 (2 weeks)  
**Pre-Sprint Baseline:** 565 passing, 18 failing, 77 errors (merged main branch)

---

## 🎯 Sprint 2.6 Objectives

**Primary Goal:** Achieve production readiness through test hardening, 4-ledger completion, and infrastructure finalization.

**Success Criteria:**
- Test suite: <10 failing tests, <20 errors (currently: 18 failing, 77 errors)
- All 4 ledgers operational with quality monitoring implemented
- Agent-data integration functional (agent can query all ledgers)
- Terraform secrets module complete and deployed
- Production deployment runbook validated

**Key Dependencies:**
- Track A → Track B: Schema stability maintained, seed data fixes enable agent testing
- Track B → Track A: Agent tools require ledger data access patterns
- Track C: Secrets management unblocks OpenAI integration for all agent tests

---

## 📋 Track Boundaries & Current Status

### Track A: Data & Backend (OMC-Data-Specialist)
**Primary Directories:**
- `backend/app/services/collectors/` (catalyst/, exchange/, glass/, human/)
- `backend/app/models.py` (ledger models only)
- `backend/tests/services/collectors/`
- `backend/tests/utils/test_seed_data.py`

**Current Assets:**
- ✅ SEC API collector: `collectors/catalyst/sec_api.py`
- ✅ CoinSpot announcements: `collectors/catalyst/coinspot_announcements.py`
- ✅ Quality monitor skeleton: `collectors/quality_monitor.py`
- ⚠️ Seed data tests: 7 failures (idempotency issues)
- ⚠️ PnL tests: 20 errors (calculation/session issues)

### Track B: Agentic AI (OMC-ML-Scientist)
**Primary Directories:**
- `backend/app/services/agent/` (orchestrator.py, agents/, tools/, langgraph_workflow.py)
- `backend/tests/services/agent/`

**Current Assets:**
- ✅ Orchestrator: run_workflow(), execute_step(), get_session_state()
- ✅ Integration tests: 19/20 passing
- ⚠️ Redis performance test: 1 failure (async context issue)
- ⚠️ Security tests: 4 errors (needs investigation)

### Track C: Infrastructure (OMC-DevOps-Engineer)
**Primary Directories:**
- `infrastructure/terraform/modules/secrets/` (currently EMPTY)
- `infrastructure/terraform/environments/`
- `.github/workflows/`

**Current Assets:**
- ✅ ECS base deployment: VPC, RDS, Redis, ECS modules complete
- ✅ Environment template: `.env.template` exists
- ✅ Configuration files: `pytest.ini`, deployment docs
- ⚠️ Secrets module: Empty directory (main.tf, variables.tf, outputs.tf needed)

---

## 🔧 Developer A: Data Specialist Sprint 2.6

**Role:** OMC-Data-Specialist  
**Focus:** Fix Test Regressions + Complete 4-Ledger Quality Monitoring

---

### 📚 Context Review (Read These First)

1. **Sprint History:** [CURRENT_SPRINT.md](CURRENT_SPRINT.md) lines 80-216 - Review P2 follow-up items from Sprint 2.5
2. **Technical Constraints:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#section-9-technical-constraints-best-practices) - SQLModel relationship patterns, async testing
3. **Test Patterns:** [docs/TESTING.md](docs/TESTING.md) lines 1-50 - Async mock patterns, known issues

---

### 🎯 Sprint 2.6 Objectives

#### **PRIORITY 1: Fix Seed Data Test Assertion** ✅ COMPLETE
**File:** [backend/tests/utils/test_seed_data.py](backend/tests/utils/test_seed_data.py) line 50  
**Current Status:** 11/12 tests passing (91.7%)  
**Issue:** Test assertion bug (NOT code bug) - expects delta count instead of absolute count

**VALIDATED FINDING:** Code implementation is CORRECT. Idempotency properly implemented (lines 88-98 in seed_data.py). Test needs minor fix.

**Tasks:**
1. ~~Investigate seed data generation logic~~ ✅ Code is correct
2. Fix test assertion at line 50:
   ```python
   # Current (fails): assert final_count == initial_count + 5
   # Fix: assert final_count == 5  # Absolute count
   ```
3. Alternatively, clear database before test for clean state

**Acceptance Criteria:**
- [ ] `test_generate_users` assertion fixed (30 minutes work)
- [x] Code handles existing superuser gracefully (already confirmed)
- [x] No relationship warnings (already passing)

**Validation Command:**
```bash
cd backend
pytest tests/utils/test_seed_data.py::TestSeedData::test_generate_users -v
```

**Expected Outcome:** 12/12 passing (currently 11/12)

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

## 🤖 Developer B: ML Scientist Sprint 2.6

**Role:** OMC-ML-Scientist  
**Focus:** Agent-Data Integration + Fix Remaining Test Issues

---

### 📚 Context Review (Read These First)

1. **Sprint History:** [CURRENT_SPRINT.md](CURRENT_SPRINT.md) lines 80-216 - Review Track B accomplishments and P2 items
2. **Agent Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Section on agent system design
3. **Test Status:** [docs/TESTING.md](docs/TESTING.md) - Current 19/20 integration test pass rate

---

### 🎯 Sprint 2.6 Objectives

#### **PRIORITY 1: Fix Redis Performance Test** (P2 from Sprint 2.5)
**File:** [backend/tests/services/agent/integration/test_performance.py](backend/tests/services/agent/integration/test_performance.py)  
**Test:** `test_session_state_retrieval_performance`  
**Current Status:** 1 test failing  
**Issue:** Redis connection from async context - wrong number of arguments for `get_session_state()`

**Tasks:**
1. Review orchestrator.py `get_session_state()` method signature (updated in Sprint 2.5)
2. Fix test to use correct calling convention: `get_session_state(session_id)` or `get_session_state(db, session_id)`
3. Ensure Redis client is properly awaited in async context
4. Validate session_manager is used correctly

**Acceptance Criteria:**
- [ ] `test_session_state_retrieval_performance` passes
- [ ] Redis client properly handles async/sync contexts
- [ ] Performance benchmarks meet <500ms target

**Validation Command:**
```bash
cd backend
pytest tests/services/agent/integration/test_performance.py::test_session_state_retrieval_performance -v --tb=long
```

**Expected Outcome:** 1/1 passing (currently 0/1)

---

#### **PRIORITY 2: Investigate Security Test Errors**
**File:** [backend/tests/services/agent/integration/test_security.py](backend/tests/services/agent/integration/test_security.py) (presumed)  
**Current Status:** 4 errors in agent test domain  
**Issue:** Unknown - requires investigation

**Tasks:**
1. Identify which tests are generating the 4 errors
2. Capture full error stacktraces
3. Fix or document if tests are aspirational (not yet implemented)
4. Add security validation patterns to agent tools

**Acceptance Criteria:**
- [ ] 4 security-related errors resolved or documented
- [ ] Agent input validation tested
- [ ] Rate limiting patterns validated

**Validation Command:**
```bash
cd backend
pytest tests/services/agent/ -k security -v --tb=long
```

**Expected Outcome:** 0 errors, tests pass or are explicitly marked as xfail

---

#### **PRIORITY 3: Agent-Data Integration**
**Files:**
- [backend/app/services/agent/tools/data_retrieval.py](backend/app/services/agent/tools/data_retrieval.py) (create or enhance)
- [backend/app/services/agent/agents/retrieval.py](backend/app/services/agent/agents/retrieval.py)

**Current Status:** Agent tools exist but may not query all 4 ledgers  
**Goal:** Ensure agents can query Glass, Human, Catalyst, Exchange ledgers

**Tasks:**
1. Review existing data retrieval tools
2. Create tools to query each ledger:
   - `get_price_data(symbol, timeframe)` → Glass ledger
   - `get_sentiment_data(symbol, source)` → Human ledger
   - `get_catalyst_events(symbol, event_type)` → Catalyst ledger
   - `get_order_history(user_id)` → Exchange ledger
3. Implement SQLModel queries using unidirectional relationship pattern (see Sprint 2.5 learnings)
4. Create integration tests: `tests/services/agent/integration/test_data_integration.py`

**Acceptance Criteria:**
- [ ] 4 data retrieval tools implemented (one per ledger)
- [ ] Tools handle missing data gracefully
- [ ] 10+ integration tests validate agent can query all ledgers
- [ ] No SQLModel relationship warnings

**Validation Command:**
```bash
cd backend
pytest tests/services/agent/integration/test_data_integration.py -v
```

**Expected Outcome:** 10+ new passing tests for data integration

---

#### **PRIORITY 4: Document Agent Query Capabilities**
**File:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Add Section 10: Agent-Data Interface

**Tasks:**
1. Document available agent tools and their parameters
2. Provide example queries for each ledger
3. Document data access patterns and performance considerations
4. Link to test files showing usage examples

**Acceptance Criteria:**
- [ ] Section 10 added to ARCHITECTURE.md
- [ ] All 4 ledgers documented with example queries
- [ ] Performance guidelines documented (<1s per query target)

**Validation:**
- Review by Track A developer for accuracy
- Validate examples work in actual agent workflow

---

### 📊 Track B Test Targets

**Baseline (Current):**
- Total: 565 passing, 18 failing, 77 errors
- Your domain: ~250 tests (agent unit + integration)
- Current pass rate: 19/20 integration tests

**Sprint 2.6 Target:**
- Fix 5 issues (1 Redis performance + 4 security errors)
- Add 10+ data integration tests
- **End State:** ~260 passing tests in your domain, 20/20 integration tests

**Daily Validation:**
```bash
cd backend
# Quick check your test domains
pytest tests/services/agent/integration/ --tb=short -q

# Full baseline comparison
pytest tests/services/agent/ --tb=short --quiet | tee test_output.txt
```

---

### 🔗 Integration Points

**Track A → Your Inputs:**
- Seed data fixes (Track A P1) will provide valid test data for your agent queries
- Quality monitor (Track A P3) results may be queryable by agents
- Schema stability maintained by Track A

**Your Outputs → Track A:**
- Document any new model fields needed for agent queries
- Coordinate on read-only access patterns for ledger tables

**Track C → Your Dependencies:**
- **CRITICAL:** Secrets management (Track C P1) needed for OPENAI_API_KEY
- Until secrets deployed, use mock LLM responses in tests

---

### 📝 Definition of Done

**Code Quality:**
- [ ] All modified code passes `bash scripts/format.sh`
- [ ] All modified code passes `bash scripts/lint.sh`
- [ ] No event loop nesting issues in async agent code

**Testing:**
- [ ] Redis performance test fixed (1 test)
- [ ] Security errors resolved (4 errors)
- [ ] Data integration tests implemented (10+ tests)
- [ ] 20/20 integration tests passing

**Documentation:**
- [ ] Section 10 added to ARCHITECTURE.md (Agent-Data Interface)
- [ ] Tool docstrings complete with parameter descriptions
- [ ] Update CURRENT_SPRINT.md with final test counts

**Commit Strategy:**
- Commit P1 (Redis fix) and P2 (security) separately
- Commit P3 (data integration) as single feature
- Create PR titled "Track B Sprint 2.6: Test Fixes + Agent-Data Integration"

---

## 🏗️ Developer C: DevOps Engineer Sprint 2.6

**Role:** OMC-DevOps-Engineer  
**Focus:** Terraform Secrets Module + Production Readiness

---

### 📚 Context Review (Read These First)

1. **Sprint History:** [CURRENT_SPRINT.md](CURRENT_SPRINT.md) lines 80-216 - Review Track C accomplishments and P2 items
2. **Infrastructure Overview:** [infrastructure/terraform/README.md](infrastructure/terraform/README.md) - ECS architecture (not EKS)
3. **Deployment Guide:** [infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md](infrastructure/terraform/DEPLOYMENT_GUIDE_TERRAFORM_ECS.md)

---

### 🎯 Sprint 2.6 Objectives

#### **PRIORITY 1: Implement Terraform Secrets Module** (P2 from Sprint 2.5)
**Directory:** [infrastructure/terraform/modules/secrets/](infrastructure/terraform/modules/secrets/) (currently EMPTY)  
**Current Status:** Directory exists but contains no files  
**Issue:** AWS Secrets Manager integration incomplete, blocking OPENAI_API_KEY injection

**Tasks:**
1. Create `modules/secrets/main.tf`:
   - Define `aws_secretsmanager_secret` resources for:
     - `omc/openai/api_key`
     - `omc/database/credentials`
     - `omc/redis/connection_string`
   - Define `aws_secretsmanager_secret_version` for initial values
   - Create IAM policy for ECS task role secret access

2. Create `modules/secrets/variables.tf`:
   - `secret_name` (string)
   - `secret_value` (string, sensitive)
   - `environment` (string: staging/production)
   - `recovery_window_in_days` (number, default 30)

3. Create `modules/secrets/outputs.tf`:
   - `secret_arn` (output)
   - `secret_name` (output)
   - `iam_policy_arn` (output for ECS task role attachment)

4. Update `environments/staging/main.tf` to use secrets module:
   ```hcl
   module "secrets" {
     source      = "../../modules/secrets"
     environment = "staging"
     secret_name = "omc/openai/api_key"
     secret_value = var.openai_api_key  # from variables
   }
   ```

5. Update ECS task definitions to inject secrets as environment variables

**Acceptance Criteria:**
- [ ] Secrets module contains main.tf, variables.tf, outputs.tf
- [ ] Module creates secrets with proper KMS encryption
- [ ] ECS task role has IAM policy attached for secret access
- [ ] Secrets injected into ECS containers as environment variables
- [ ] Manual validation: `terraform plan` in staging shows secret resources

**Validation Command:**
```bash
cd infrastructure/terraform/environments/staging
terraform init
terraform plan -out=tfplan
terraform show tfplan | grep secretsmanager
```

**Expected Outcome:** Secret resources shown in plan, no errors

---

#### **PRIORITY 2: Deployment Automation**
**Files:**
- `.github/workflows/deploy.yml` (create or enhance)
- `scripts/deploy.sh` (exists, may need updates)

**Current Status:** CI/CD pipeline exists but may not fully automate ECS deployment  
**Goal:** One-command deployment to staging/production

**Tasks:**
1. Review existing `scripts/deploy.sh` and `.github/workflows/` files
2. Enhance GitHub Actions workflow:
   - Build Docker images (backend, frontend)
   - Push to ECR
   - Update ECS service with new task definition
   - Wait for deployment stability
3. Add deployment gates:
   - Require passing tests before deployment
   - Manual approval for production
4. Create rollback procedure documentation

**Acceptance Criteria:**
- [ ] `scripts/deploy.sh` deploys to staging with single command
- [ ] GitHub Actions workflow deploys on merge to main
- [ ] Deployment waits for ECS service to stabilize
- [ ] Rollback procedure documented in OPERATIONS_RUNBOOK.md

**Validation Command:**
```bash
# Test staging deployment
bash scripts/deploy.sh staging

# Check ECS service status
aws ecs describe-services --cluster omc-staging --services omc-backend
```

**Expected Outcome:** Deployment completes successfully, ECS tasks running

---

#### **PRIORITY 3: Production Deployment Runbook**
**File:** [infrastructure/terraform/OPERATIONS_RUNBOOK.md](infrastructure/terraform/OPERATIONS_RUNBOOK.md) (exists, enhance)

**Tasks:**
1. Review and update existing runbook
2. Add sections:
   - **Pre-Deployment Checklist** (secrets configured, tests passing, backups taken)
   - **Deployment Steps** (step-by-step with exact commands)
   - **Health Check Validation** (how to verify deployment success)
   - **Rollback Procedure** (how to revert to previous version)
   - **Troubleshooting** (common issues and solutions)
3. Validate runbook by performing staging deployment following documented steps

**Acceptance Criteria:**
- [ ] Runbook contains all 5 sections
- [ ] Commands tested and validated on staging
- [ ] Rollback procedure successfully executed (test)
- [ ] Health check endpoints documented with expected responses

**Validation:**
- Perform end-to-end staging deployment using only runbook instructions
- Document any gaps or errors found

---

#### **PRIORITY 4: CloudWatch Monitoring Setup**
**Files:**
- `infrastructure/terraform/modules/monitoring/` (create if doesn't exist)
- Update `environments/staging/main.tf` to use monitoring module

**Tasks:**
1. Create CloudWatch dashboards for:
   - ECS Container Insights (CPU, Memory, Network)
   - RDS Performance (Connections, Query Duration)
   - Redis Metrics (Hit Rate, Evictions)
   - Application Logs (Error Rate, Latency)
2. Create CloudWatch alarms for:
   - High CPU (>80% for 5 minutes)
   - High Memory (>80% for 5 minutes)
   - Failed Health Checks (>3 in 5 minutes)
   - 5xx Error Rate (>5% in 5 minutes)
3. Configure SNS topic for alarm notifications

**Acceptance Criteria:**
- [ ] CloudWatch dashboard created with 4+ widgets
- [ ] 4+ alarms configured with appropriate thresholds
- [ ] SNS topic configured (can use dummy email for now)
- [ ] Dashboard accessible via AWS console

**Validation:**
- Open CloudWatch dashboard and verify metrics are populated
- Trigger test alarm by simulating high CPU (optional)

---

### 📊 Track C Deliverables

**Baseline (Current):**
- ECS base deployment: ✅ Complete
- Secrets module: ⚠️ Empty directory
- Deployment automation: 🟡 Partial
- Monitoring: 🟡 Basic health checks only

**Sprint 2.6 Target:**
- Secrets module: ✅ Complete with 3 secrets (OpenAI, DB, Redis)
- Deployment automation: ✅ One-command staging deployment
- Runbook: ✅ Validated on staging
- Monitoring: ✅ Dashboards and alarms configured

**Daily Validation:**
```bash
# Check Terraform modules structure
ls -la infrastructure/terraform/modules/secrets/

# Validate Terraform configuration
cd infrastructure/terraform/environments/staging
terraform validate

# Check ECS service status
aws ecs describe-services --cluster omc-staging --services omc-backend --query 'services[0].deployments'
```

---

### 🔗 Integration Points

**Your Outputs → Track A:**
- Secrets management enables DB credential injection (eventually)
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
4. Document any P2 items for Sprint 2.7

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
pytest --tb=short --quiet | tee sprint_2.6_final_tests.txt

# Compare to baseline
echo "Baseline: 565 passing, 18 failing, 77 errors"
grep -E "passed|failed|error" sprint_2.6_final_tests.txt
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
git checkout -b track-[a|b|c]-sprint-2.6

# Daily commits
git add .
git commit -m "feat: descriptive message"
git push origin track-[a|b|c]-sprint-2.6

# End of sprint
# Create PR: "Track [A|B|C] Sprint 2.6: [Brief Summary]"
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
- [ ] 7 seed data tests fixed
- [ ] 20 PnL errors resolved
- [ ] Quality monitor implemented with 10+ tests

**Track B:**
- [ ] 1 Redis performance test fixed
- [ ] 4 security errors resolved
- [ ] 10+ data integration tests added
- [ ] Agent-Data Interface documented

**Track C:**
- [ ] Secrets module complete (3 files)
- [ ] Deployment automation tested
- [ ] Operations runbook validated
- [ ] CloudWatch monitoring configured

**Sprint Close:**
- [ ] All PRs merged to main
- [ ] Full test suite run on merged main
- [ ] CURRENT_SPRINT.md updated with final status
- [ ] Sprint retrospective completed

---

**Ready to begin Sprint 2.6? Each developer should:**
1. Read this entire document
2. Review the 5 context files listed in "Context Analysis Required"
3. Set up local test environment (see [TESTING.md](docs/TESTING.md))
4. Create your track branch
5. Post "Sprint 2.6 Started" update with Day 1 plan

Good luck! 🚀
