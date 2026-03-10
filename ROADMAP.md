# Oh My Coins (OMC) - Strategic Roadmap

**Version**: 5.4
**Last Updated**: Mar 10, 2026
**Current Phase**: Sprint 2.47 — Phase 5 In Progress
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

### ✅ Phase 2: Production Hardening & BYOM

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

**In Progress**:
- 🔄 **Backtesting Framework**: XGBoost models, proper walk-forward validation, historical simulation (Sprint 2.47)

**Planned Capabilities**:
- **Explainable AI**: SHAP values, decision path visualization (Sprint 2.48)
- **Collector Performance & Freshness** (Sprint 2.49)
- **MLflow Integration**: When experiment scale justifies it (Phase 5+)
- **Feast Feature Store**: When training-serving skew becomes a problem (Phase 5+)

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

### Sprint 2.47 - Backtesting Framework Hardening (IN PROGRESS)
*   XGBoost model integration, proper walk-forward validation, historical simulation improvements.

### Sprint 2.48 - Explainable AI (PLANNED)
*   SHAP values, decision path visualization, model transparency features.

### Sprint 2.49 - Collector Performance & Freshness (PLANNED)
*   Collector health monitoring, data freshness alerts, performance optimization.

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

### Current Metrics (Sprint 2.46)
- **Test Coverage**: >97% (959 tests, target maintained across sprints)
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

**Next Review**: After Sprint 2.47 completion
**Maintained by**: The Architect
**Last Major Update**: Sprint 2.47 (backtesting framework hardening)
