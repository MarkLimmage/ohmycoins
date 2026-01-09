# Current Sprint Plan - Parallel Development Cycle

**Status:** Active
**Cycle:** Phase 2.5 (Data), Phase 3 (Agentic), Phase 9 (Infrastructure)
**Strategy:** 3-Developer Parallel Execution (Tracks A, B, C)

---

## 📅 Sprint Overview

This sprint synchronizes three parallel tracks to achieve a fully operational data-to-decision pipeline. The primary focus is finalizing the "Single Source of Truth" (Data), activating the "Autonomous Brain" (Agent), and deploying the "Scalable Foundation" (Infrastructure/ECS).

### 🎯 Strategic Goals
1.  **Track A (Data):** Complete the Catalyst Ledger (SEC, CoinSpot) and verify 4-Ledger integrity.
2.  **Track B (Agent):** Operationalize the ReAct Loop (LangGraph) with live data access.
3.  **Track C (Infra):** Finalize ECS production architecture (replacing EKS) and secure secrets.

---

## 🛣️ Track A: Data & Backend (OMC-Data-Specialist)
**Focus:** `backend/app/services/collectors/` & `backend/app/services/trading/`
**Goal:** Achieve 100% Catalyst Ledger visibility, fix critical schema issues, and ensure trading system stability.

### 🔴 Critical Issues Requiring Immediate Attention

#### 1. **CatalystEvents Schema Mismatch** (BLOCKER)
- **File:** `backend/app/models.py` Line 440-443
- **Issue:** Model defines `currencies` field as `Column(JSON)` but database migration created it as `postgresql.ARRAY(sa.String())`
- **Impact:** 32 test failures across seed_data, collectors, and trading modules
- **Error:** `psycopg.errors.DatatypeMismatch: column "currencies" is of type character varying[] but expression is of type json`
- **Remediation:** 
  ```python
  # Change from:
  currencies: list[str] | None = Field(default=None, sa_column=Column(JSON))
  # To:
  currencies: list[str] | None = Field(default=None, sa_column=Column(postgresql.ARRAY(sa.String())))
  ```
- **Tests Affected:** `tests/utils/test_seed_data.py`, `tests/services/collectors/integration/`, `tests/services/trading/`

#### 2. **Trading Client Async Mock Handling** (HIGH)
- **Files:** `tests/services/trading/test_client.py`
- **Issue:** Mock objects not properly configured for async context managers
- **Failures:** 2 tests - `test_api_error_handling`, `test_http_error_handling`
- **Error:** `TypeError: 'coroutine' object does not support the asynchronous context manager protocol`
- **Remediation:** Update mock setup to use `AsyncMock` with proper `__aenter__` and `__aexit__` configurations

#### 3. **Trading System Database Session Issues** (HIGH)
- **Files:** `tests/services/trading/test_algorithm_executor.py`, `test_recorder.py`, `test_safety.py`
- **Issue:** 48 test errors due to pending rollback from CatalystEvents schema mismatch
- **Impact:** All trading system tests cascade failure
- **Remediation:** Fix CatalystEvents schema first, then retest trading module

### 📋 Sprint Tasks

| Priority | Task | Description | Status |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **Fix CatalystEvents Schema** | Update `models.py` line 442 to use `postgresql.ARRAY(sa.String())` instead of `JSON`. Verify with migration file `c3d4e5f6g7h8`. | [ ] In Progress |
| **CRITICAL** | **Fix Trading Test Mocks** | Update `test_client.py` async mocks to properly support context managers. | [ ] Pending |
| **High** | **Catalyst: SEC API** | Implement `sec_api.py` to track Form 4/8-K filings for major crypto holders (MSTR, COIN). | [ ] Pending |
| **High** | **Catalyst: CoinSpot** | Finalize `coinspot_announcements.py` scraper for new listings/maintenance. | [ ] Pending |
| **High** | **Verify Trading System** | Re-run all 48 trading tests after schema fix to ensure no cascading issues. | [ ] Pending |
| **Med** | **Quality Monitor** | Implement `quality_monitor.py` to flag stale or missing data across all 4 ledgers. | [ ] Pending |
| **Med** | **Add pytest.ini** | Register custom markers (`integration`, `slow`) to eliminate warnings. | [ ] Pending |
| **Low** | **Human Ledger** | Expand `reddit.py` to cover 3 additional subreddits with sentiment scoring. | [ ] Pending |

### 📊 Test Status
- **Passing:** 579 tests (Core functionality stable)
- **Failing:** 33 tests (32 from schema mismatch, 1 from documentation check)
- **Errors:** 48 tests (Cascade from schema issue in trading module)
- **Coverage:** Test infrastructure is comprehensive

**Dependencies:** Schema fix is prerequisite for all other development.

---

## 🧠 Track B: Agentic AI (OMC-ML-Scientist)
**Focus:** `backend/app/services/agent/`
**Goal:** Connect the "Brain" to the "Eyes" (Data), fix integration test failures, and enable autonomous reasoning.

### 🔴 Critical Issues Requiring Immediate Attention

#### 1. **Agent Orchestrator Integration Test Failures** (HIGH)
- **Files:** `tests/services/agent/integration/test_end_to_end.py`
- **Issue:** 8 test failures due to orchestrator method signature mismatches
- **Failures:** 
  - `test_simple_workflow_completion`
  - `test_workflow_with_price_data`
  - `test_workflow_with_error_recovery`
  - `test_workflow_with_clarification`
  - `test_workflow_with_model_selection`
  - `test_complete_workflow_with_reporting`
  - `test_workflow_session_lifecycle`
  - `test_workflow_with_artifact_generation`
- **Error:** `AttributeError: <AgentOrchestrator object> has no attribute 'X'` or method signature mismatch
- **Remediation:** Review `backend/app/services/agent/orchestrator.py` and align with test expectations or update tests to match actual implementation

#### 2. **Agent Performance Test Issues** (MEDIUM)
- **Files:** `tests/services/agent/integration/test_performance.py`
- **Issue:** 4 test failures
  - `test_large_dataset_handling` - AttributeError on orchestrator
  - `test_workflow_execution_time` - AttributeError on orchestrator
  - `test_session_state_retrieval_performance` - Wrong number of arguments for `get_session_state()`
  - `test_multiple_workflow_runs` - AttributeError on orchestrator
- **Remediation:** Fix `get_session_state()` signature and ensure orchestrator exposes expected async methods

#### 3. **Missing OPENAI_API_KEY Configuration** (MEDIUM)
- **File:** `.env` line 59
- **Issue:** `OPENAI_API_KEY=` is empty, preventing actual LLM-based agent tests
- **Impact:** Agent integration tests may fail or skip when LLM calls are required
- **Remediation:** Configure valid OpenAI API key or mock LLM responses in tests

#### 4. **Deprecated Datetime Usage** (LOW - Technical Debt)
- **Files:** `backend/app/services/agent/artifacts.py`, `agents/reporting.py`, `tools/reporting_tools.py`
- **Issue:** 50+ warnings for `datetime.utcnow()` deprecated in Python 3.12+
- **Warning:** `datetime.datetime.utcnow() is deprecated and scheduled for removal`
- **Remediation:** Replace all `datetime.utcnow()` with `datetime.now(datetime.UTC)`

#### 5. **Scalability Test Failure** (MEDIUM)
- **File:** `tests/services/agent/integration/test_performance.py::test_concurrent_workflow_execution`
- **Issue:** AttributeError prevents testing concurrent agent workflows
- **Remediation:** Ensure orchestrator supports concurrent execution patterns

### 📋 Sprint Tasks

| Priority | Task | Description | Status |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **Fix Orchestrator Integration** | Review and align `orchestrator.py` methods with integration test expectations. Address 8 end-to-end test failures. | [ ] In Progress |
| **High** | **Fix Performance Tests** | Correct `get_session_state()` signature and enable performance benchmarking. | [ ] Pending |
| **High** | **Configure LLM Provider** | Add valid `OPENAI_API_KEY` to `.env` or implement proper test mocking strategy. | [ ] Pending |
| **High** | **Data Retrieval Agent** | Implement `DataRetrievalAgent` with tools to query the 4-Ledger database (using Track A's schema). | [ ] Pending |
| **Med** | **Analyst Agent Enhancement** | Implement `DataAnalystAgent` with technical indicator tools (RSI, MACD) and sentiment alignment. | [ ] Pending |
| **Med** | **Human-in-the-Loop** | Add `clarification.py` node to ask user for guidance when confidence is low. | [ ] Pending |
| **Low** | **Update Deprecated APIs** | Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)` across agent codebase. | [ ] Pending |

### 📊 Test Status
- **Passing:** Agent core functionality (tools, artifacts, reporting) - 90%+ pass rate
- **Failing:** Integration & performance tests - 12 failures
- **Warnings:** 50+ deprecation warnings (non-blocking)
- **Coverage:** Unit tests comprehensive; integration tests need alignment

**Dependencies:** 
- Blocked by Track A schema fix for full integration testing
- Requires OPENAI_API_KEY for live agent execution tests

---

## 🏗️ Track C: Infrastructure & DevOps (OMC-DevOps-Engineer)
**Focus:** `infrastructure/terraform/` & `.github/workflows/`
**Goal:** Deploy a cost-effective, scalable ECS architecture and support local/staging test environments.

### 🟡 Configuration & Deployment Concerns

#### 1. **Missing Environment Variables** (MEDIUM)
- **File:** `.env`
- **Issues:**
  - `OPENAI_API_KEY=` is empty (required for agent system)
  - `CI` variable warning in docker-compose (cosmetic but indicates missing CI/CD configuration)
- **Impact:** Agent tests cannot run with real LLM, CI/CD pipeline may have configuration gaps
- **Remediation:** 
  - Document secrets management strategy
  - Create `.env.template` with all required variables
  - Implement AWS Secrets Manager integration for production

#### 2. **Test Marker Configuration Missing** (LOW)
- **File:** `backend/pytest.ini` (doesn't exist)
- **Issue:** 5 warnings for unregistered pytest markers (`integration`, `slow`)
- **Impact:** Test warnings clutter output, markers not officially recognized
- **Remediation:** Create `backend/pytest.ini` with marker registration

#### 3. **Docker Compose Configuration** (INFO)
- **Status:** Working correctly for local development
- **Services:** PostgreSQL 17, Redis 7, Backend, Frontend all healthy
- **Note:** No infrastructure issues detected in container orchestration

#### 4. **Missing Documentation** (LOW)
- **File:** `docs/DEPLOYMENT_STATUS.md` (referenced in test but doesn't exist)
- **Impact:** 1 test failure in `test_roadmap_validation.py`
- **Remediation:** Create deployment status document or update test expectations

### 📋 Sprint Tasks

| Priority | Task | Description | Status |
| :--- | :--- | :--- | :--- |
| **High** | **Secrets Management** | Implement AWS Secrets Manager integration for `OPENAI_API_KEY` and DB credentials. Create secrets injection for ECS tasks. | [ ] Pending |
| **High** | **Environment Template** | Create `.env.template` documenting all required environment variables with descriptions. | [ ] Pending |
| **High** | **ECS Transition** | Validate `modules/ecs/` and ensure all EKS references are archived/removed. | [ ] Pending |
| **Med** | **CI/CD Pipeline** | Update GitHub Actions to build/push Docker images to ECR and deploy to ECS Fargate. Ensure all env vars are properly injected. | [ ] Pending |
| **Med** | **Monitoring** | Configure CloudWatch dashboards for Container Insights (CPU/Memory/Latency). Add alerts for test failures. | [ ] Pending |
| **Med** | **Test Configuration** | Create `backend/pytest.ini` to register custom test markers and eliminate warnings. | [ ] Pending |
| **Low** | **Deployment Docs** | Create `docs/DEPLOYMENT_STATUS.md` to track deployment state across environments. | [ ] Pending |

### 📊 Infrastructure Status
- **Local Environment:** ✅ Fully operational (PostgreSQL, Redis, Docker Compose)
- **Database Migrations:** ✅ All 12 migrations applied successfully
- **Container Health:** ✅ All services healthy with proper health checks
- **Test Infrastructure:** ✅ 579 passing tests demonstrate stable foundation
- **Secrets:** ⚠️ Not configured for agent system testing

**Dependencies:** 
- No blockers for infrastructure work
- Can proceed with ECS deployment while Tracks A & B fix test failures
- Secrets management should be prioritized to unblock agent testing

---

## 🔗 Integration Points
*   **Data -> Agent:** Schema `backend/app/models.py` is the contract. Track A updates it; Track B reads it.
*   **Agent -> Infra:** Agents require `OPENAI_API_KEY` injected via AWS Secrets Manager (Track C).
*   **All -> Infra:** CI/CD pipeline (Track C) deploys code from Tracks A & B.

---

## 📜 Definition of Done (DoD)
1.  **Code:** Committed to `main` with passing tests (Unit + Integration).
2.  **Docs:** EARS-compliant requirements updated in `docs/`.
3.  **Deploy:** Staging environment successfully running latest build on ECS.
