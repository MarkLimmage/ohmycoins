# Oh My Coins (OMC) - Project Roadmap

**Status**: Active Development (Integration & Deployment)  
**Last Updated**: 2026-01-10  
**Current Sprint**: Sprint 2.7 (2026-01-11 to 2026-01-25)

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
        - ⚠️ Tests blocked by SQLite ARRAY compatibility (Sprint 2.7 fix)
    *   [ ] Agent -> Trading Handoff (Artifact promotion) (**Future**)
    *   [ ] System-wide Integration Tests (Staging) (**Sprint 2.7 in progress**)

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

### Phase 3: Agentic Data Science System (**Sprint 2.6 Complete**)
*   **Owner**: Developer B
*   **Outcome**: Autonomous ReAct agents capable of planning, analysis, and model training.
*   **Sprint 2.6 Additions:**
    - ✅ Agent-data integration implemented (8 tools covering all 4 ledgers)
    - ✅ Section 10 added to ARCHITECTURE.md (Agent-Data Interface, 406 lines)
    - ✅ 19 comprehensive integration tests created
    - ⚠️ All 19 tests blocked by SQLite ARRAY incompatibility (Sprint 2.7 fix)
    - 📊 Track B: 90% complete - Functional code, test infrastructure issue

### Recent Sprints
- **Sprint 2.6** (2026-01-10): Test hardening, 4-ledger quality monitoring, agent-data integration, infrastructure modules
  - Final: 581/686 tests passing (84.7%), 17 failing, 44 errors
  - [Sprint 2.6 Archive](docs/archive/history/sprints/sprint-2.6/README.md)

## 4. Future Roadmap

### Phase 4: Strategy Execution (The Floor)
*   **Planned Start**: Week 14
*   **Scope**: Live paper trading, risk management enforcement, and gradual capital deployment.

### Phase 5: Dashboard & Analytics
*   **Planned Start**: Week 16
*   **Scope**: Advanced visualization for Agent decisions and P&L tracking.
