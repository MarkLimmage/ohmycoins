# Oh My Coins (OMC) - Project Roadmap

**Status**: Active Development (Production Readiness)  
**Last Updated**: 2026-01-17  
**Current Sprint**: Sprint 2.10 (Planning - Production Readiness & Testing)  
**Previous Sprint**: Sprint 2.9 Complete ✅ (P&L fixes + BYOM Agent Integration)

## 1. Project Overview
This roadmap tracks the development of the OMC platform across its three parallel tracks:
*   **Track A**: Data Collection & Backend (The 4 Ledgers, Trading Engine)
*   **Track B**: Agentic AI (The Lab)
*   **Track C**: Infrastructure (AWS/ECS)

## 2. Active Phases

### Phase 9: Infrastructure & Production Readiness (Weeks 1-12)
*   **Owner**: Developer C
*   **Goal**: Zero-downtime, scalable ECS environment.
*   **Status**:
    *   [x] Week 1-2: VPC & Network Architecture
    *   [x] Week 3-4: ECS Cluster & Task Definitions
    *   [x] Week 5-6: RDS & ElastiCache (Redis)
    *   [x] Week 7-8: Monitoring (CloudWatch/Prometheus) & Logging
    *   [x] Week 9-10: Staging Environment Deployment
    *   [x] Week 11-12: Production Rollout & Secrets Management (**Sprint 2.6 Complete**)
        - ✅ Terraform secrets module complete (422 lines)
        - ✅ Terraform monitoring module complete (1,457 lines - 8 alarms, CloudWatch dashboard)
        - ✅ Deployment script complete (253 lines - one-command ECS deployment)
        - ✅ Operations runbook enhanced (1,268 lines)
        - 🔄 Staging deployment in progress (Sprint 2.7)

### Integration Phase (Weeks 7-13)
*   **Owner**: All Developers
*   **Goal**: Seamless end-to-end operation.
*   **Status**:
    *   [x] Data -> Agent Handoff (DB Schema alignment) (**Sprint 2.5 Complete**)
    *   [x] Agent -> Data Integration (4-ledger query tools) (**Sprint 2.6 Complete**)
        - ✅ 8 data retrieval tools implemented (all 4 ledgers)
        - ✅ 19 integration tests created
        - ✅ All 318 agent tests passing (Sprint 2.7 - SQLite→PostgreSQL migration complete)
    *   [ ] Agent -> Trading Handoff (Artifact promotion) (**Future**)
    *   [ ] System-wide Integration Tests (Staging) (**Sprint 2.8 pending**)

## 3. Completed Phases

### Phase 2.5: Comprehensive Data Collection (**Sprint 2.6 Complete**)
*   **Owner**: Developer A
*   **Outcome**: Fully operational 4-Ledger collectors (Glass, Human, Catalyst, Exchange).
*   **Sprint 2.6 Additions:**
    - ✅ SEC API collector production-ready (4 tests passing)
    - ✅ CoinSpot announcements collector production-ready (5 tests passing)
    - ✅ Quality monitor implemented (17 tests passing, exceeds requirements)
    - ✅ Seed data tests fixed (12/12 passing)
    - ✅ PnL tests: 19/21 passing (90% - 2 isolation issues remaining)
    - 📊 Track A: 95% complete - 190/195 tests passing

### Phase 3: Agentic Data Science System (**Sprint 2.7 Complete** ✅)
*   **Owner**: Developer B
*   **Outcome**: Autonomous ReAct agents capable of planning, analysis, and model training.
*   **Sprint 2.6 Additions:**
    - ✅ Agent-data integration implemented (8 tools covering all 4 ledgers)
    - ✅ Section 10 added to ARCHITECTURE.md (Agent-Data Interface, 406 lines)
    - ✅ 19 comprehensive integration tests created
*   **Sprint 2.7 Completion:**
    - ✅ SQLite→PostgreSQL fixture migration complete
    - ✅ All 318 agent tests passing (100%)
    - ✅ TESTING.md enhanced with PostgreSQL fixture patterns
    - 📊 Track B: 100% complete - All test infrastructure stable

### Recent Sprints
- **Sprint 2.9** (2026-01-17): P&L Test Fixes + BYOM Agent Integration ✅
  - Final: Both Track A and Track B complete (100%)
  - Track A: 33/33 tests passing (P&L + seed data fixes)
  - Track B: 342/344 agent tests passing (BYOM integration, Anthropic support)
  - Track C: Deferred to Sprint 2.10
  - P&L: Critical test failures resolved, production-ready ✅
  - BYOM: Agent integration complete, 3 LLM providers working ✅
  - [Sprint 2.9 Archive](docs/archive/history/sprints/sprint-2.9/)
- **Sprint 2.8** (2026-01-17): BYOM Foundation + Test Stabilization 🟡
  - Final: 646/704 tests passing (91.8%), 58 failing
  - Track A: 10/11 seed data tests fixed (90% - UUID pattern applied)
  - Track B: 43/43 BYOM tests passing (100% - Foundation complete)
  - Track C: Not started
  - BYOM: Database schema, encryption, LLM Factory, 5 API endpoints ✅
  - [Sprint 2.8 Archive](docs/archive/history/sprints/sprint-2.8/SPRINT_2.8_FINAL_REPORT.md)
- **Sprint 2.7** (2026-01-10): Test infrastructure fixes, PostgreSQL migration, deployment documentation ✅
  - Final: 645/661 tests passing (97.6%), 16 failing, 0 errors
  - Track A: 13/13 PnL tests passing (UUID isolation fix)
  - Track B: 318/318 agent tests passing (SQLite→PostgreSQL migration)
  - Track C: Comprehensive staging deployment documentation
  - [Sprint 2.7 Archive](docs/archive/history/sprints/sprint-2.7/SPRINT_2.7_FINAL_REPORT.md)
- **Sprint 2.6** (2026-01-10): Test hardening, 4-ledger quality monitoring, agent-data integration, infrastructure modules
  - Final: 581/686 tests passing (84.7%), 17 failing, 44 errors
  - [Sprint 2.6 Archive](docs/archive/history/sprints/sprint-2.6/README.md)

## 4. Future Roadmap

### Bring Your Own Model (BYOM) Feature (Sprints 2.8-2.9) ✅
*   **Completed**: Sprint 2.9 (Agent Integration Complete)
*   **Owner**: Developer B (Agent Track) with Backend Support from Developer A
*   **Scope**: Enable users to configure custom LLM providers (OpenAI, Google Gemini, Anthropic Claude) for agent execution
*   **Status**: 
    *   [x] Sprint 2.8 (Foundation - 8 hours): Database schema, encryption, OpenAI + Google support ✅
        - UserLLMCredentials table with AES-256 encryption
        - LLM Factory (OpenAI + Google Gemini)
        - 5 API endpoints (create, list, set default, delete, validate)
        - 43/43 tests passing (100%)
    *   [x] Sprint 2.9 (Agent Integration - 8 hours): Agent orchestrator integration, Anthropic support ✅
        - LangGraphWorkflow accepts user_id/credential_id
        - AgentOrchestrator session tracking
        - Anthropic Claude support added
        - Backward compatibility maintained
        - 342/344 agent tests passing (99.4%)
    *   [ ] Sprint 2.10 (UI/UX - 6-8 hours): Frontend credential management, provider selection UI
    *   [ ] Sprint 2.10 (User Experience - 20-24 hours): Frontend LLM settings page, session creation modal extension
    *   [ ] Sprint 2.11 (Production Hardening - 12-16 hours): Cost tracking, key rotation, monitoring, security audit
*   **Total Effort**: 56-72 hours across 4 sprints (8 hours completed)
*   **Requirements**: [BYOM User Stories](docs/requirements/BYOM_USER_STORIES.md), [BYOM EARS Requirements](docs/requirements/BYOM_EARS_REQUIREMENTS.md)
*   **Architecture**: [Section 11: BYOM Architecture](docs/ARCHITECTURE.md#11-bring-your-own-model-byom-architecture)

### Phase 4: Strategy Execution (The Floor)
*   **Planned Start**: Week 14
*   **Scope**: Live paper trading, risk management enforcement, and gradual capital deployment.

### Phase 5: Dashboard & Analytics
*   **Planned Start**: Week 16
*   **Scope**: Advanced visualization for Agent decisions and P&L tracking.
