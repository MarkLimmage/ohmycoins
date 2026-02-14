# Oh My Coins (OMC) - Strategic Roadmap

**Version**: 4.1
**Last Updated**: Feb 15, 2026
**Current Phase**: Sprint 2.27 (Autonomous Beta Launch)
**Status**: Active Development - Live Beta
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

### � Phase 4: Risk & Reliability (The Guard)

**Status**: Active Sprint Focus (Live Beta)  
**Objective**: Implement live risk management, P&L monitoring security, and operational stability.

**Deliverables**:
- ✅ **RiskCheckService**: Hard-coded safety layer for all orders
- ✅ **Circuit Breakers**: "Kill Switch" functionality
- ✅ **Audit Logging**: Immutable logs for all execution attempts
- ✅ **Local Monitoring**: Docker-based health checks and alert system

---

### 📋 Phase 5: Advanced Analytics & Optimization

**Status**: Future  
**Objective**: Advanced visualization, ensemble methods, and continuous optimization.

**Planned Capabilities**:
- **Algorithm Optimization**: Hyperparameter tuning, ensemble methods
- **Mobile App**: Read-only monitoring
- **Explainable AI**: Transparency for algorithm decisions

---

### 🛑 Phase 6: Operational Hardening (Sprints 2.22-2.23)

**Duration**: Weeks 35-38 (4 weeks)
**Status**: Active
**Objective**: Critical infrastructure validation and safety implementation before Live MVP.

**Planned Deliverables**:
- **Validated Staging Environment**: Accessible via URL
- **The Guard**: Pre-trade risk validation microservice
- **Closed Beta Access**: Whitelist system
- **CI/CD**: Fully automated deployment pipeline

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
- AWS ECS (Container orchestration)
- AWS RDS (PostgreSQL)
- AWS ElastiCache (Redis)
- Terraform (Infrastructure as Code)
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
- ✅ **Production Deployment** (Sprint 2.12): AWS infrastructure with DNS/SSL automation
- ✅ **Documentation Uplift** (Sprint 2.14): 4-tier architecture + AI governance

### Current Metrics (Sprint 2.14)
- **Test Coverage**: 694/702 tests passing (98.9%)
- **Production Uptime**: 99.9% (AWS ECS with health checks)
- **Documentation**: 7,000+ lines of living documentation created
- **Cost Optimization**: Resources scaled to $0 when idle

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
- ✅ Secrets management (AWS Secrets Manager)
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

### Phase 4 Success (The Floor)
- 📋 Paper trading operational with real-time P&L
- 📋 Emergency kill switch tested and documented
- 📋 Risk management enforced (stop-loss, position limits)
- 📋 Disconnected state handling validated
- 📋 Lab-to-Floor promotion workflow functional

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

**Next Review**: After Sprint 2.15 completion  
**Maintained by**: Tech Lead  
**Last Major Update**: Sprint 2.14 (Documentation Uplift)
