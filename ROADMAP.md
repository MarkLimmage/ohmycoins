# Oh My Coins (OMC) - Strategic Roadmap

**Version**: 6.2
**Last Updated**: Mar 2026
**Current Phase**: Sprint 2.53 — Phase 7.2 (Stage-Row Architecture & Stale Protocol)
**Status**: Active Development - Live Beta (On-Prem)
**Documentation Strategy**: [DOCUMENTATION_STRATEGY.md](docs/DOCUMENTATION_STRATEGY.md)
**Current Sprint Details**: [CURRENT_SPRINT.md](CURRENT_SPRINT.md)

---

## 1. Project Vision

Oh My Coins is transforming from a simple price-tracking application into an **autonomous, multi-agent trading platform** capable of predictive market intelligence and automated strategy generation. The platform integrates:

- **The 4 Ledgers**: Comprehensive data collection (Glass, Human, Catalyst, Exchange)
- **The Lab**: Agentic AI framework for autonomous data science workflows
- **The Floor**: Live trading execution with risk management
- **BYOM**: Bring Your Own Model for custom LLM provider integration

**Key Differentiator**: AI-first architecture where documentation drives development through a tiered specification system and AI agent governance.

**Infrastructure Pivot (Feb 2026)**: 
The project has shifted focus from AWS cloud deployment to a **high-performance local linux server (192.168.0.241)** for the remainder of the development and initial production phases. This allows for lower cost, lower latency, and tighter control during the critical agent training and strategy optimization phases. AWS code is preserved for future scaling.

---

## 2. Development Phases (Strategic View)

### ✅ Phase 1: Foundation & Infrastructure

**Status**: Complete  
**Objective**: Establish core data collection infrastructure, agent framework, and production deployment.

**Key Achievements**:
- ✅ **4 Ledgers Data Collection**: Glass, Human, Catalyst, Exchange collectors operational
- ✅ **Agent Framework**: ReAct-based autonomous agents (The Lab) with 8 data retrieval tools
- ✅ **Local Infrastructure**: Production-ready deployment (Docker/Traefik) on Local Server
- ✅ **Database Integration**: PostgreSQL with Alembic migrations, Redis for caching
- ✅ **Test Infrastructure**: High coverage (>97%)

**Documentation**:
- [SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md) - Core functional requirements
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and microservices structure
- [Sprint History](docs/archive/history/sprints/) - Detailed sprint retrospectives

---

### ✅ Phase 5: The Lab 2.0 - Agentic Data Science

**Status**: Complete (March 16, 2026)
**Objective**: Transform the trading platform into an autonomous research lab with Dagger execution and LangGraph orchestration.

**Key Achievements**:
- ✅ **Execution Sandbox**: Secured Dagger container environment for running untrusted user code.
- ✅ **Orchestration**: LangGraph state machine with strict resumption and checkpointing.
- ✅ **Observability**: MLflow tracking integration for model experiments.
- ✅ **Safety**: Statistical anomaly detection (Z-Score) and strict recursion limits.
- ✅ **Messaging**: Standardized WebSocket event protocol with sequence IDs and timestamps.

### 🔄 Phase 6: The Floor - Live Execution & Risk Management


**Status**: Complete  
**Objective**: Harden platform for production use, implement user-configurable LLM providers, expand data coverage.

**Key Achievements**:
- ✅ **BYOM Feature Complete**: OpenAI, Google Gemini, Anthropic Claude support
- ✅ **Rate Limiting & Security**: Redis-based per-user limits, OWASP alignment
- ✅ **Data Collection Enhancement**: Nansen SmartMoneyFlow model, Coinspot coverage validated

**Documentation**:
- [BYOM Requirements](docs/requirements/BYOM_EARS_REQUIREMENTS.md) - BYOM functional specifications
- [TESTING.md](docs/TESTING.md) - Comprehensive testing strategy
- [DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md) - Production deployment status

---

### ✅ Phase 3: UI/UX Foundation & Living Documentation

**Status**: Complete  
**Objective**: Establish component library, implement 4 Ledgers dashboard, create Living Documentation System with AI agent governance.

**Completed Targets**:
- ✅ **4 Ledgers Dashboard**: Real-time ticker, Sentiment heatmap, Sparklines
- ✅ **The Floor UI**: Real-time dashboard, Kill Switch, WebSocket integration
- ✅ **Parallel Development**: Piloted worktree-based multi-agent development
- ✅ **The Strategist**: Strategy Generator and Backtesting Engine
- ✅ **The Tactician**: Paper Trading Engine with Slippage metrics
- ✅ **The Optimizer**: Performance Dashboard

**Completed Focus (Infrastructure Pivot)**:
- ✅ **Local Deployment Verification**: Ensure all Phase 3 features work seamlessly on 192.168.0.241.
- ✅ **Documentation Audit**: Aligning all docs with the new on-premise reality.

---

### ✅ Phase 4: Risk & Reliability (The Guard)

**Status**: Complete (Sprint 2.36–2.40)
**Objective**: Implement live risk management, anomaly detection, alerting, and operational stability.

**Completed Deliverables**:
- ✅ **RiskCheckService**: Hard-coded safety layer for all orders
- ✅ **Circuit Breakers**: "Kill Switch" functionality
- ✅ **Audit Logging**: Immutable logs for all execution attempts
- ✅ **Local Monitoring**: Docker-based health checks on 192.168.0.241
- ✅ **Anomaly Detection**: IsolationForest pipeline integrated into LangGraph workflow (Sprint 2.36 Track A)
- ✅ **Data Explorer**: Filtering/charting at /data-explorer with backend API wiring (Sprint 2.36 Track C)
- ✅ **Alerting Service**: AlertService + AlertRule/AlertLog models + API + LangGraph integration (Sprint 2.36 Track B)
- ✅ **Collector Plugin System**: ICollector interface, CollectorRegistry, 16 plugins (Sprint 2.37)
- ✅ **Collector Observability**: Sample records viewer, RSS collector fixes (Sprint 2.38)
- ✅ **Keyword Enrichment Pilot**: NewsKeywordMatch, taxonomy module, CryptoSlate enrichment (Sprint 2.39)
- ✅ **Keyword Enrichment Rollout**: All 6 RSS collectors enriched, available-coins endpoint (Sprint 2.40)
- ✅ **Collector Cleanup**: Dead collector removal, error_rate metrics, 12h chart aggregation (Sprint 2.41)
- ✅ **Enrichment Pipeline**: IEnricher interface, KeywordEnricher, LLMEnricher (Gemini), EnrichmentPipeline, enrichment dashboard (Sprint 2.42)
- ✅ **Signal Data Model & API**: NewsEnrichment JSONB model, materialized views, 5 signal query endpoints, Lab agent tool (Sprint 2.43)

---

### 🔄 Phase 5: Advanced Analytics & Optimization

**Status**: In Progress (Sprint 2.44+)
**Objective**: Agentic data science workflows, model lifecycle, and continuous optimization.

**Completed Deliverables**:
- ✅ **Lab Live Session Experience**: AgentRunner background execution, WebSocket streaming, Lab page with session management (Sprint 2.44)
- ✅ **Agentic Data Science Pipeline**: Blueprint Card, training with visual progress, model serialization (joblib), Optuna hyperparameter search, Floor promotion UI (Sprint 2.45)

- ✅ **Model Playground**: ModelPlaygroundPanel — inference test UI, predict endpoint, artifact wiring fixes (Sprint 2.46)
- ✅ **Backtesting Framework**: XGBoost models, walk-forward validation, BacktestEngine, performance metrics (Sharpe/Sortino/drawdown), Floor UI (Sprint 2.47)

**In Progress**:
- 🔄 **Explainable AI + Feature Store**: SHAP values, decision path visualization, database-native Feature Store with materialized views (Sprint 2.48)

### ✅ Phase 5.5: The Lab 2.0 Architecture (Strategic Pivot)

**Status**: Complete (Sprint 2.50)
**Objective**: Harden "The Lab" from its Phase 3 "Flat Chat" prototype into the "Scientific Grid" architecture — a fully isolated, secure, and stateful research environment using Dagger, LangGraph, and an EventLedger-based messaging system.

**Completed Foundations (Phases 0–4)**:
- ✅ **Dagger Execution Sandbox**: Secure, containerized code execution with `omc-agent-base:latest`.
- ✅ **LangGraph Orchestrator**: `LangGraphWorkflow` state machine with PostgresSaver checkpointing.
- ✅ **React Flow & WebSocket Grid**: Real-time node-based DSLC visualization.
- ✅ **MLflow Integration**: Full experiment tracking and artifact lineage.

**Completed — Phase 5.5 "The Hardening Bridge" (Workstreams A–E)**:
- ✅ **Workstream A+: Event Sequencing** — `EventLedger` with `sequence_id`/`timestamp`, `action_request` event type.
- ✅ **Workstream B+: State Rehydration** — `GET /rehydrate` endpoint, WebSocket `?after_seq` dedup.
- ✅ **Workstream C+: Dagger-MLflow Bridge** — Disposable Script pattern, lifecycle tagging, Parquet caching.
- ✅ **Workstream D+: Statistical Health Gates** — Zero-variance kill-switch, 3-cycle circuit breaker.
- ✅ **Workstream E: Frontend Remediation** — Stage-isolated Grid, mime-type dispatcher, HITL controls, `useRehydration()` hook.

### ✅ Phase 6: Production Readiness

**Status**: Complete (Sprint 2.50)
- ✅ **PostgresSaver Migration**: `langgraph-checkpoint-postgres` — HITL sessions survive restarts.
- ✅ **Graph Consolidation**: `lab_graph.py` deleted, `LangGraphWorkflow` is sole runtime.
- ✅ **12 Production Bug Fixes**: Event pipeline, resume flow, duplicate dedup, checkpointer wiring.

### ✅ Phase 7: The Conversational Scientific Grid (v1.3)

**Status**: Initial Implementation Complete (Sprint 2.51), Enforcement In Progress (Sprint 2.52)
**Objective**: Transform the single-column "Causal Grid" into a 3-column Conversational Scientific Grid with agent narration, user messaging, mandatory scope confirmation, and HITL gates at 4 interrupt points.

**Architecture**: API_CONTRACTS.md v1.3 — 7 event types, 3-cell routing, 4 interrupts, POST /message.

**Sprint 2.51 — Initial Implementation (COMPLETE):**
- ✅ F1-F7: LangGraph scope_confirmation, model_selection, stream_chat, plan_established, POST /message, circuit breaker
- ✅ G1-G8: 3-column grid, DialoguePanel, ActivityTracker, StageOutputs, ChatInput, event router, rehydration
- ✅ Glass merge (`e368672`), Graph merge (`5ee3ef2`), production deploy

**Sprint 2.52 — v1.3.1 Enforcement (COMPLETE):**
Production testing revealed 6 backend and 8 frontend enforcement violations. See `API_CONTRACTS.md` §0.1. Merged to main at `8efcab0`. 41 PASS / 0 FAIL / 6 SKIP acceptance tests.

**Workstream F (Graph — backend enforcement):** ✅ COMPLETE
- ✅ F1: Scope confirmation fallback → `circuit_breaker_v1` (not silent fallback)
- ✅ F2: Runner publishes node `pending_events`, no generic overwrite
- ✅ F3: `task_id` mandatory on all `status_update` payloads
- ✅ F4: `plan_established` emitted even on error/fallback paths
- ✅ F5: Deduplicate runner vs node action_request events
- ✅ F6: Correct stage values in status_update emissions

**Workstream G (Glass — frontend enforcement):** ✅ COMPLETE
- ✅ G1: `sequence_id` deduplication in event router
- ✅ G2: Inline `action_request` HITL cards per subtype
- ✅ G3: Remove legacy "Resume Workflow" button
- ✅ G4: Pipeline colors (green=complete, blue=active, gray=pending)
- ✅ G5: ChatInput enabled during RUNNING/AWAITING_APPROVAL
- ✅ G6: Stage Outputs driven by pipeline selection
- ✅ G7: Rehydration/WS `after_seq` overlap fix
- ✅ G8: Differentiate agent/user/system message styling

### 🔄 Phase 7.2: Stage-Row Architecture & Stale Protocol (UPCOMING — Sprint 2.53+)

**Objective:** Transform the single 3-column grid into per-DSLC-stage rows. Each of the 7 stages gets its own collapsible 3-column row (dialogue, tasks, outputs) with stage-filtered events, stale protocol, and revision flow for revisiting completed stages.

**Design Decisions:**
- Single session with events filtered by `event.stage` per row (NOT multi-session)
- Session list moved to drawer overlay (saves horizontal space)
- ReactFlow pipeline graph removed entirely (stage row headers replace it)
- Downstream invalidation via stale protocol with user override (NOT semantic diffing)
- Collapsible desktop sidebar (48px icon rail ↔ 200px expanded)

**Phase 7.2.1 — Layout Foundations (frontend-only, ~1 sprint):**
- [ ] H1: Collapsible desktop sidebar (48px collapsed / 200px expanded, localStorage persist)
- [ ] H2: Reduce whitespace / maximize grid area (route-conditional padding)
- [ ] H3: Session list → drawer overlay (`DrawerRoot`, left slide, 350px)
- [ ] H4: Remove LabHeader (ReactFlow pipeline) — recover 150px vertical
- [ ] H5: Add `stage` field to `DialogueMessage` type + `processEvent()`
- [ ] H6: Stage lifecycle state (`staleStages`, `completedStages`, stage status derivation)
- [ ] H7: `StageRow` component (per-stage 3-column grid with status colors)
- [ ] H8: `StageRowHeader` (status icon, expand/collapse, Revise button)
- [ ] H9: `StageRowList` (replaces LabGrid — vertical list of stage rows)
- [ ] H10: Stage-filtered DialoguePanel, ActivityTracker, StageOutputs
- [ ] H11: Max-height + overflow scroll on expanded stage rows (450px)
- [ ] H12: Cleanup — remove LabHeader.tsx, LabGrid.tsx, LabStageRow.tsx (unused)

**Phase 7.2.2 — Stale Protocol (backend + frontend, ~0.5 sprint):**
- [ ] I1: Backend emits `status_update` with `status: COMPLETE` at stage transitions
- [ ] I2: Frontend processes COMPLETE status_update (stage lifecycle)
- [ ] I3: Add `revision_start` event type to schema + runner
- [ ] I4: Frontend processes `revision_start` events (stale markers, dividers)
- [ ] I5: Add optional `stage` param to `POST /messages`
- [ ] I6: ChatInput sends stage param

**Phase 7.2.3 — Revision Flow (backend + frontend, ~1 sprint):**
- [ ] J1: `POST /sessions/{id}/revise` endpoint (checkpoint rewind + stale cascade)
- [ ] J2: LangGraph checkpoint rewind logic (PostgresSaver, reset downstream flags)
- [ ] J3: Stale-aware re-run endpoints (`POST /rerun`, `POST /keep-stale`)
- [ ] J4: "Revise" button on COMPLETE stage row headers
- [ ] J5: "Re-run from here" / "Keep results" on STALE stage row headers
- [ ] J6: Revision divider in dialogue panel

**New Files:** StageRow.tsx, StageRowHeader.tsx, StageRowList.tsx, SessionDrawer.tsx
**Modified:** types.ts, LabContext.tsx, DialoguePanel.tsx, ActivityTracker.tsx, StageOutputs.tsx, ChatInput.tsx, LabDashboard.tsx, LabSessionView.tsx, Sidebar.tsx, SidebarItems.tsx, _layout.tsx, lab.tsx, agent.py, runner.py, lab_schema.py, langgraph_workflow.py, session_manager.py
**Deleted:** LabHeader.tsx, LabGrid.tsx, LabStageRow.tsx

---

---

## 7. Recent & Upcoming Sprints

### Sprint 2.36 - Advanced Analytics & Alerting (COMPLETE)
*   Anomaly detection pipeline, alerting service, data explorer with backend API wiring.

### Sprint 2.37 - Collector Rehabilitation (COMPLETE)
*   ICollector plugin system, 16 collectors ported, legacy removal.

### Sprint 2.38 - Collector Observability (COMPLETE)
*   Sample records viewer, RSS collector persistence fix.

### Sprint 2.39 - CryptoSlate Keyword Enrichment Pilot (COMPLETE)
*   NewsKeywordMatch model, keyword taxonomy, CryptoSlate enrichment, duplicate handling fix.

### Sprint 2.40 - Keyword Enrichment Rollout (COMPLETE)
*   Roll out keyword enrichment to all RSS collectors, available-coins endpoint, ledger filtering.

### Sprint 2.41 - News Collector Foundation Fix (COMPLETE)
*   Removed 5 dead collectors, centralized User-Agent, error_rate metrics, 12h chart aggregation.

### Sprint 2.42 - Enrichment Pipeline (COMPLETE)
*   IEnricher pipeline, KeywordEnricher, LLMEnricher (Gemini), EnrichmentPipeline, enrichment dashboard.

### Sprint 2.43 - Signal Data Model & Query API (COMPLETE)
*   NewsEnrichment JSONB model, EntityEnricher, materialized views, 5 signal endpoints, Lab agent tool.

### Sprint 2.44 - Lab Live Session Experience (COMPLETE)
*   AgentRunner background execution, WebSocket streaming, Lab page with session management. 925 tests.

### Sprint 2.45 - Agentic Data Science Pipeline (COMPLETE)
*   Hotfixes (WS token, recursion limit) + ModelBlueprint schema + model serialization (joblib) + Optuna hyperparameter tool + structured metric events + Blueprint Card + Training Progress Charts + Artifact Viewer + Promote Modal. 946 tests.

### Sprint 2.46 - Model Playground (COMPLETE)
*   ModelPlaygroundPanel — inference test UI, artifact wiring, promote endpoint. 959 tests.

### Sprint 2.47 - Backtesting Framework Hardening (COMPLETE)
*   XGBoost models, walk-forward validation (TimeSeriesSplit), BacktestEngine, performance metrics, Floor UI. 966 tests.

### Sprint 2.48 - Explainable AI + Feature Store (COMPLETE)
*   SHAP values, decision path visualization, model transparency features. Database-native Feature Store with 4 materialized views.

### Sprint 2.49 - Lab 2.0 Integration & Release (COMPLETE)
*   Lab 2.0 backend architecture: Dagger execution, LangGraph workflow, typing compliance, idempotent migrations.

### Sprint 2.50 - Phase 5.5 Parallel Sprint (COMPLETE)
*   Merged workstreams D→A→B→C→E. EventLedger, HITL action_request, rehydration, Scientific Grid refactor, mime-type dispatcher, useRehydration hook. PostgresSaver migration, graph consolidation, 12 production bug fixes. **1023 tests passing.** Base commit `2cd7e33` → final `7acf69b`.

### Sprint 2.51 - Conversational Scientific Grid (COMPLETE)
*   Phase 7: v1.3 Conversational Grid. Workstream F (Graph: scope_confirmation, model_selection, stream_chat narration, plan_established, POST /message, circuit breaker escalation). Workstream G (Glass: 3-column grid, DialoguePanel, ActivityTracker, StageOutputs, ChatInput, event router, rehydration). Parallel worktree sprint (omc-lab-graph, omc-lab-ui). Glass merged `e368672`, Graph merged `5ee3ef2`. Production deployed.

### Sprint 2.52 - v1.3.1 Enforcement / Gap Remediation (COMPLETE)
*   Phase 7.1: Production testing revealed 6 Severity-A contract violations and 5 Severity-B UX deficits. Backend: silent LLM fallback instead of circuit_breaker escalation, runner overwrites node events with generic action_request, missing task_id on status_update, no plan_established on error paths. Frontend: duplicate messages (no sequence_id dedup), orphan HITL button, wrong pipeline colors (yellow not green), disabled ChatInput, hardcoded Stage Outputs. Two-agent parallel sprint (fix/graph-enforcement, fix/glass-enforcement). Merged to main at `8efcab0`. 41 PASS / 0 FAIL / 6 SKIP acceptance tests.

### Sprint 2.53 - Phase 7.2: Stage-Row Architecture & Stale Protocol (UPCOMING)
*   Transform the single 3-column grid into per-stage rows (each DSLC stage = one 3-column row with dialogue, tasks, outputs). Collapsible sidebar, session drawer overlay, remove ReactFlow pipeline. Backend: stage COMPLETE signaling, revision_start event type, POST /revise endpoint, stale protocol. ~2.5 sprints across 3 phases: Layout Foundations (frontend), Stale Protocol (backend+frontend), Revision Flow (backend+frontend).

---

## 3. Documentation & Governance

### Living Documentation System

Oh My Coins employs a **4-Tier Documentation Architecture** designed to prevent documentation drift while enabling AI-driven development:

#### Tier 1: System Core (Low Change Frequency)
- **[SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md)**: Single Source of Truth for all requirements (EARS syntax)
- **[USER_JOURNEYS.md](docs/USER_JOURNEYS.md)**: 5 persona-driven workflows with E2E test linkage
- **[API_CONTRACTS.md](docs/API_CONTRACTS.md)**: API interaction patterns and UI behavior contracts
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design, microservices structure, data flow

**Owned by**: Tech Lead, Product Manager

#### Tier 2: Feature Modules (Medium Change Frequency)
- Co-located README.md files in service folders (`backend/app/services/*/README.md`)
- Co-located README.md files in feature folders (`frontend/src/features/*/README.md`)
- Feature-specific technical specifications

**Owned by**: Feature teams (updated in same PR as code changes)

#### Tier 3: UI/UX Contracts (High Change Frequency)
- **[DESIGN_SYSTEM.md](docs/ui/DESIGN_SYSTEM.md)**: Component library, interaction patterns, accessibility
- **[DATA_VISUALIZATION_SPEC.md](docs/ui/DATA_VISUALIZATION_SPEC.md)**: Chart specifications for 4 Ledgers
- **[TRADING_UI_SPEC.md](docs/ui/TRADING_UI_SPEC.md)**: Floor UI with safety mechanisms

**Owned by**: Frontend team, Design lead

#### Tier 4: Auto-Generated Documentation (Dynamic)
- **OpenAPI/Swagger**: FastAPI auto-generated API documentation
- **Storybook**: React component visual documentation
- **Database ERD**: Auto-generated schema diagrams

**Owned by**: CI/CD pipeline

### AI Agent Governance System

The project uses **Prompt-Engineered Orchestration** to coordinate AI agents:

- **4 Agent Personas**: The Architect, The Feature Developer, The UI/UX Agent, The Quality Agent
- **Tiered Access Control**: Each persona has specific read/write permissions to documentation tiers
- **Sprint Initialization Manifests (SIM)**: Structured prompts for sprint planning with context injection
- **Documentation Gates**: Automated PR checks enforcing doc-code synchronization
- **Git-Flow**: Requirement-first branching (`feat/REQ-XX-YYY-description`), atomic commits (docs → code → tests)

**See**: [DOCS_GOVERNANCE.md](docs/DOCS_GOVERNANCE.md) for complete governance framework

---

## 4. Architecture & Technical Stack

### System Architecture
```
┌─────────────────────────────────────────────────────────┐
│                     The 4 Ledgers                        │
│  (Glass, Human, Catalyst, Exchange Data Collection)     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                      The Lab                             │
│  (Agentic AI: Planning, Analysis, Model Training)       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                     The Floor                            │
│  (Trading Execution, Risk Management, P&L Monitoring)    │
└─────────────────────────────────────────────────────────┘
```

**Detailed Architecture**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Technology Stack

**Backend**:
- FastAPI (REST API)
- LangChain + LangGraph (Agent orchestration)
- PostgreSQL (Primary database)
- Redis (Caching, rate limiting)
- Celery (Background tasks)

**Frontend**:
- React + TypeScript
- TanStack Router, React Query
- Recharts, visx, lightweight-charts (Data visualization)
- Tailwind CSS (Styling)
- Storybook (Component documentation)

**Infrastructure**:
- Local Linux Server (192.168.0.241) — Docker Compose orchestration
- Traefik v3.6 reverse proxy
- PostgreSQL 17 (containerized)
- Redis 7 (containerized)
- GitHub Actions (CI/CD)

**Testing**:
- Pytest (Backend unit/integration)
- Playwright (E2E tests)
- k6 (Load testing)

---

## 5. Sprint Management

### Current Sprint
**See**: [CURRENT_SPRINT.md](CURRENT_SPRINT.md) for detailed sprint tracking, objectives, deliverables, and progress metrics.

### Sprint Archive
**See**: [docs/archive/history/sprints/](docs/archive/history/sprints/) for historical sprint retrospectives and completion reports.

### Sprint Workflow
1. **Initialization**: Create Sprint Initialization Manifest (SIM) from [template](docs/sprints/SIM_TEMPLATE.md)
2. **Context Injection**: Assign agent personas with tiered access and constraints
3. **Development**: Documentation-first workflow (docs → implementation → tests)
4. **Validation**: Automated documentation gates (Doc-Sync Check) block PRs without updates
5. **Retrospective**: Archive sprint docs, validate requirement traceability, update metrics

---

## 6. Key Milestones & Metrics

### Completed Milestones
- ✅ **4 Ledgers Operational** (Sprint 2.6): All data collectors production-ready
- ✅ **Agent-Data Integration** (Sprint 2.7): 8 tools connecting agents to 4 Ledgers
- ✅ **BYOM Complete** (Sprint 2.10): 3 LLM providers integrated
- ✅ **Production Deployment** (Sprint 2.12): Infrastructure with DNS/SSL automation
- ✅ **Documentation Uplift** (Sprint 2.14): 4-tier architecture + AI governance
- ✅ **Infrastructure Pivot** (Sprint 2.35): Migration from AWS to local Docker/Traefik stack

### Current Metrics (Sprint 2.47)
- **Test Coverage**: >97% (966 tests, target maintained across sprints)
- **Production Uptime**: Local server (192.168.0.241) with Docker health checks
- **Collectors**: 11 active plugins with enrichment pipeline (IEnricher)
- **Signal API**: 5 query endpoints with materialized views for Lab consumption
- **Lab**: Live session execution with WebSocket streaming, Model Playground, artifact management
- **Agent Framework**: Multi-track parallel development with worktree isolation

### Future Metrics (Phase 3-5)
- **Time to Find Documentation**: < 2 minutes
- **New Developer Onboarding**: < 2 days
- **PRs with Documentation Updates**: > 80%
- **User Journey E2E Test Coverage**: 100% (5/5 journeys)

---

## 7. Risk Management

### Active Risks

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Documentation Drift | HIGH | Automated Doc-Sync Check, PR template, requirement validation | ✅ Mitigated |
| API Rate Limits | MEDIUM | Redis-based rate limiting, exponential backoff, quota monitoring | ✅ Mitigated |
| WebSocket Disconnection (The Floor) | HIGH | REST API fallback, automatic algorithm pause, manual intervention protocol | ✅ Spec'd (REQ-FL-DISC-001 to 007) |
| LLM Cost Overruns (BYOM) | MEDIUM | Per-user cost tracking, budget alerts, tier-based limits | 📋 Planned (Sprint 2.15) |
| Accessibility Compliance | MEDIUM | WCAG 2.1 AA standards, table view toggles, axe-core audits | 📋 Planned (Sprint 2.15) |

### Security Posture
- ✅ AES-256 encryption for LLM credentials
- ✅ OWASP alignment (A04, A05, A07)
- ✅ Rate limiting (60 req/min per user)
- ✅ Secrets management (environment variables, AES-256 for LLM credentials)
- 📋 Penetration testing (Q2 2026)

---

## 8. Success Criteria

### Phase 3 Success (UI/UX Foundation)
- ✅ 4-tier documentation architecture operational
- ✅ AI agent governance system implemented
- 📋 Component library complete with Storybook
- 📋 4 Ledgers dashboard functional
- 📋 5 user journeys have E2E tests
- 📋 Documentation-first workflow adopted by team

### Phase 4 Success (Risk & Reliability)
- ✅ Paper trading operational with real-time P&L
- ✅ Emergency kill switch tested and documented
- ✅ Risk management enforced (stop-loss, position limits)
- ✅ Anomaly detection pipeline integrated
- ✅ Alerting service operational
- ✅ Data Explorer wired to backend APIs
- ✅ Enrichment pipeline with signal query API
- ✅ Lab-to-Floor promotion workflow (Sprint 2.46)

### Phase 5 Success (Advanced Analytics)
- 📋 Backtesting framework with 1+ year historical data
- 📋 Performance analytics dashboard
- 📋 Mobile app for monitoring
- 📋 Multi-agent coordination operational

---

## 9. References

### Core Documentation
- [SYSTEM_REQUIREMENTS.md](docs/SYSTEM_REQUIREMENTS.md) - Functional requirements (EARS syntax)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and technical architecture
- [USER_JOURNEYS.md](docs/USER_JOURNEYS.md) - 5 user workflows with E2E test linkage
- [API_CONTRACTS.md](docs/API_CONTRACTS.md) - API interaction patterns
- [DOCUMENTATION_STRATEGY.md](docs/DOCUMENTATION_STRATEGY.md) - Living documentation system
- [DOCS_GOVERNANCE.md](docs/DOCS_GOVERNANCE.md) - AI agent governance framework

### UI/UX Specifications
- [DESIGN_SYSTEM.md](docs/ui/DESIGN_SYSTEM.md) - Component library
- [DATA_VISUALIZATION_SPEC.md](docs/ui/DATA_VISUALIZATION_SPEC.md) - 4 Ledgers charts
- [TRADING_UI_SPEC.md](docs/ui/TRADING_UI_SPEC.md) - The Floor UI

### Operations
- [DEPLOYMENT_STATUS.md](docs/DEPLOYMENT_STATUS.md) - Production deployment status
- [TESTING.md](docs/TESTING.md) - Testing strategy and infrastructure
- [PROJECT_HANDOFF.md](docs/PROJECT_HANDOFF.md) - Operational context

### Sprint Management
- [CURRENT_SPRINT.md](CURRENT_SPRINT.md) - Active sprint tracking
- [SIM_TEMPLATE.md](docs/sprints/SIM_TEMPLATE.md) - Sprint Initialization Manifest template
- [Sprint Archive](docs/archive/history/sprints/) - Historical sprint retrospectives

---

**End of Strategic Roadmap**

**Next Review**: After Sprint 2.49 completion
**Maintained by**: The Architect
**Last Major Update**: Sprint 2.49 (Lab 2.0 v1.2 Architecture Alignment)
