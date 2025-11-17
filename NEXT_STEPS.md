# Oh My Coins (OMC!) - Next Steps & Parallel Development Plan

**Generated:** 2025-11-17  
**Status Review Date:** 2025-11-16  
**Current Branch:** main

---

## Executive Summary

This document provides a **prioritized, actionable plan** for progressing the Oh My Coins platform based on the current state:

- ✅ **Phase 1 & 2**: Complete (100%) - Foundation, data collection, and user authentication
- 🔄 **Phase 2.5**: Partially complete (~40%) - Comprehensive data collection framework started
- 🔄 **Phase 3**: Foundation only (~15%) - Agentic AI system scaffolded

**Key Finding:** Multiple high-value work streams can be progressed **in parallel** to significantly reduce time-to-market.

---

## Priority 1: Complete Phase 2.5 Foundation (High ROI, Low Cost)

### Why This Matters
Phase 2.5 provides the **data foundation** that makes the Agentic system (Phase 3) significantly more effective. Without comprehensive data, algorithms are limited to price-only analysis.

### Current Status: ~40% Complete
**Completed:**
- ✅ Database schema (all 4 ledgers)
- ✅ Collector framework and base classes
- ✅ DeFiLlama collector (Glass Ledger)
- ✅ CryptoPanic collector (Human Ledger)
- ✅ Collection orchestrator

**Gaps:**
- ❌ Catalyst Ledger (0% complete) - **HIGHEST PRIORITY**
- ❌ Human Ledger completion (Reddit API)
- ❌ Data quality monitoring

### Recommended Actions (4-6 weeks)

#### Week 1-2: Catalyst Ledger (CRITICAL)
**Priority: HIGHEST** - Catalysts drive immediate market reactions

1. **SEC API Integration** (Week 1)
   - Monitor crypto-related companies (Coinbase, MicroStrategy, BlackRock)
   - Detect Form 4, 8-K, 10-K filings
   - Implementation: `backend/app/services/collectors/catalyst/sec_api.py`
   - Tests: `backend/tests/services/collectors/catalyst/test_sec_api.py`
   - **Estimated Effort**: 2-3 days
   - **Cost**: $0 (free SEC EDGAR API)

2. **CoinSpot Announcements Scraper** (Week 2)
   - New token listings (the "CoinSpot Effect")
   - Exchange maintenance announcements
   - Implementation: Playwright-based scraper
   - File: `backend/app/services/collectors/catalyst/coinspot_announcements.py`
   - Tests: `backend/tests/services/collectors/catalyst/test_coinspot_announcements.py`
   - **Estimated Effort**: 3-4 days
   - **Cost**: $0 (scraping public website)

**Deliverables:**
- Catalyst Ledger operational (100% complete)
- 2 new collector services
- 2 new test suites
- Integration with orchestrator

---

#### Week 3: Human Ledger - Reddit Integration
**Priority: HIGH** - Sentiment analysis is predictive

1. **Reddit API Collector**
   - Monitor key subreddits (r/CryptoCurrency, r/Bitcoin, r/ethereum, etc.)
   - Track post sentiment and engagement
   - Implementation: PRAW-based collector
   - File: `backend/app/services/collectors/human/reddit.py`
   - Tests: `backend/tests/services/collectors/human/test_reddit.py`
   - **Estimated Effort**: 3-4 days
   - **Cost**: $0 (free Reddit API)

**Deliverables:**
- Human Ledger at 50% completion (2 of 4 sources)
- Reddit collector operational
- Test coverage for Reddit integration

---

#### Week 4: Data Quality & Monitoring
**Priority: MEDIUM** - Ensures data reliability

1. **Data Quality Checks**
   - Completeness validation
   - Timeliness monitoring
   - Accuracy verification
   - Implementation: `backend/app/services/collectors/quality_monitor.py`
   - **Estimated Effort**: 2-3 days

2. **Collection Metrics Dashboard**
   - Collection success rates
   - Latency monitoring
   - Error tracking
   - Implementation: Extend existing monitoring
   - **Estimated Effort**: 2 days

**Deliverables:**
- Data quality monitoring system operational
- Alert system for collection failures
- Metrics dashboard

---

#### Week 5-6: Testing & Integration (Optional Buffer)
**Priority: HIGH** - Ensures stability

1. **Integration Testing**
   - End-to-end collector testing
   - Data quality validation
   - Performance testing (24/7 operation)
   - Error handling validation
   - **Estimated Effort**: 5 days

2. **Documentation**
   - Complete Phase 2.5 documentation
   - Collector configuration guides
   - Troubleshooting documentation
   - **Estimated Effort**: 2-3 days

**Deliverables:**
- Phase 2.5 at 80%+ completion
- Comprehensive test coverage
- Production-ready collectors
- Complete documentation

---

## Priority 2: Advance Phase 3 Agentic System

### Why This Matters
The Agentic AI system is the **differentiator** that enables autonomous algorithm development. With Phase 2.5 data, it can build truly predictive models.

### Current Status: ~15% Complete (Foundation Only)
**Completed:**
- ✅ Database schema for sessions
- ✅ Session manager
- ✅ Basic project structure
- ✅ Some tests

**Gaps:**
- ❌ Complete agent implementations (0%)
- ❌ LangGraph/LangChain integration (0%)
- ❌ Agent tools and capabilities (0%)
- ❌ ReAct loop (0%)
- ❌ Human-in-the-loop features (0%)
- ❌ Reporting system (0%)

### Recommended Actions (8-12 weeks)

#### Phase 3A: Core Agent Implementation (Weeks 1-6)

**Week 1-2: LangGraph Foundation**
1. Install and configure LangGraph/LangChain
2. Set up Redis for agent state management
3. Create AgentState model and workflow nodes
4. Implement basic ReAct loop structure
5. **Estimated Effort**: 5-7 days
6. **Cost**: OpenAI/Anthropic API (~$50-100/month during development)

**Week 3-4: Data Agents**
1. Complete DataRetrievalAgent implementation
   - Tool: fetch_price_data
   - Tool: fetch_sentiment_data (Phase 2.5 data)
   - Tool: fetch_on_chain_metrics (Phase 2.5 data)
   - Tool: fetch_catalyst_events (Phase 2.5 data)
   - Tool: get_available_coins
   - Tool: get_data_statistics
2. Implement DataAnalystAgent
   - Tool: calculate_technical_indicators
   - Tool: analyze_sentiment_trends
   - Tool: analyze_on_chain_signals
   - Tool: detect_catalyst_impact
   - Tool: clean_data
   - Tool: perform_eda
3. **Estimated Effort**: 10 days

**Week 5-6: Modeling Agents**
1. Implement ModelTrainingAgent
   - Tool: train_classification_model
   - Tool: train_regression_model
   - Tool: cross_validate_model
2. Implement ModelEvaluatorAgent
   - Tool: evaluate_model
   - Tool: tune_hyperparameters
   - Tool: compare_models
   - Tool: calculate_feature_importance
3. **Estimated Effort**: 10 days

**Deliverables:**
- Core agents operational
- Basic workflow execution
- Agent tools implemented
- Test coverage for agents

---

#### Phase 3B: Orchestration & HiTL (Weeks 7-10)

**Week 7-8: ReAct Loop & Orchestration**
1. Complete LangGraph state machine
2. Implement ReAct (Reason-Act-Observe) loop
3. Connect all agents to orchestrator
4. End-to-end workflow testing
5. **Estimated Effort**: 10 days

**Week 9-10: Human-in-the-Loop**
1. Implement clarification system
2. Implement choice presentation
3. Implement user override mechanism
4. Add approval gates
5. **Estimated Effort**: 10 days

**Deliverables:**
- Complete agentic workflow operational
- Human-in-the-loop features
- Integration testing complete

---

#### Phase 3C: Reporting & Completion (Weeks 11-12)

**Week 11-12: Final Features**
1. Implement ReportingAgent
2. Implement artifact management
3. Implement secure code sandbox
4. API endpoints for agent sessions
5. Comprehensive testing
6. Documentation
7. **Estimated Effort**: 10 days

**Deliverables:**
- Phase 3 complete (100%)
- Autonomous multi-agent system operational
- Complete documentation

---

## Priority 3: Infrastructure & DevOps (Parallel Track)

### Why This Matters
Production infrastructure can be prepared **in parallel** while features are being developed.

### Recommended Actions (4-8 weeks, can start anytime)

#### Infrastructure as Code (2-3 weeks)
1. **AWS Infrastructure Design**
   - ECS/EKS for microservices
   - RDS for PostgreSQL
   - ElastiCache for Redis
   - S3 for algorithm storage
   - CloudWatch for monitoring

2. **Terraform/CloudFormation Implementation**
   - VPC and security groups
   - Load balancers
   - Auto-scaling policies
   - **Estimated Effort**: 10-15 days

#### CI/CD Enhancements (1-2 weeks)
1. **Production Deployment Pipeline**
   - Build and push Docker images to ECR
   - Deploy to ECS/EKS
   - Database migrations
   - Health checks
   - Blue-green deployment
   - **Estimated Effort**: 5-10 days

#### Security & Monitoring (2-3 weeks)
1. **Security Hardening**
   - Secrets management (AWS Secrets Manager)
   - WAF rules
   - Encryption at rest and in transit
   - **Estimated Effort**: 5-10 days

2. **Monitoring Setup**
   - CloudWatch dashboards
   - Log aggregation
   - Alert configuration
   - **Estimated Effort**: 3-5 days

**Deliverables:**
- Production-ready AWS infrastructure
- Automated deployment pipeline
- Security measures in place
- Monitoring and alerting

---

## Parallel Development Strategies

### Strategy A: Single Developer (Conservative)
**Timeline: 20-24 weeks**

```
Weeks 1-6:   Phase 2.5 Completion (Priority 1)
Weeks 7-18:  Phase 3 Implementation (Priority 2)
Weeks 19-24: Phase 3 Testing & Integration
Throughout:  Infrastructure work in spare time
```

**Pros:**
- Lower coordination overhead
- Deep knowledge of entire system
- Lower risk of integration issues

**Cons:**
- Longer overall timeline
- Single point of failure
- Limited parallelization

---

### Strategy B: Two-Developer Team (Recommended)
**Timeline: 12-16 weeks**

**Developer 1: Data & Quality**
```
Weeks 1-2:  Catalyst Ledger (SEC API, CoinSpot scraper)
Weeks 3:    Human Ledger (Reddit API)
Weeks 4:    Data Quality & Monitoring
Weeks 5-6:  Integration Testing & Documentation
Weeks 7+:   Support Phase 3 integration, Phase 6 prep
```

**Developer 2: Agentic System**
```
Weeks 1-2:  LangGraph Foundation & Setup
Weeks 3-4:  Data Agents (Retrieval, Analyst)
Weeks 5-6:  Modeling Agents (Training, Evaluator)
Weeks 7-8:  Orchestration & ReAct Loop
Weeks 9-10: Human-in-the-Loop Features
Weeks 11-12: Reporting & Completion
Weeks 13-16: Integration with Phase 2.5 data, Testing
```

**Coordination Points:**
- Week 1: Align on data schemas and APIs
- Week 4: Dev 1 provides Phase 2.5 data access to Dev 2
- Week 6: Mid-sprint sync and integration testing
- Week 12: Full integration testing

**Pros:**
- Fastest path to completion
- Balanced workload
- Good knowledge sharing
- Manageable coordination

**Cons:**
- Requires coordination
- Integration testing critical
- Both developers need broad skills

---

### Strategy C: Three-Developer Team (Maximum Parallelization)
**Timeline: 10-14 weeks**

**Developer 1: Data Infrastructure**
```
Weeks 1-4:  Phase 2.5 Completion
Weeks 5-10: Support integration, prepare for Phase 6
```

**Developer 2: Agentic System**
```
Weeks 1-12: Phase 3 Full Implementation
Weeks 13-14: Integration Testing
```

**Developer 3: Infrastructure & DevOps**
```
Weeks 1-2:  AWS Infrastructure Design
Weeks 3-6:  Infrastructure as Code Implementation
Weeks 7-8:  CI/CD Pipeline Enhancement
Weeks 9-10: Security & Monitoring
Weeks 11-14: Support deployment, testing
```

**Coordination Points:**
- Week 1: Architecture alignment meeting
- Weeks 2, 6, 10: Sprint syncs
- Week 12: Full integration week

**Pros:**
- Fastest overall timeline
- Specialized roles
- Infrastructure ready early
- Production deployment possible at completion

**Cons:**
- Highest coordination overhead
- Risk of integration challenges
- Requires experienced team
- Higher communication burden

---

## Critical Path Analysis

### Sequential Dependencies (Cannot Parallelize)
1. Phase 2.5 data collection **MUST** be complete before Phase 3 can fully leverage multi-source analysis
2. Phase 3 (Agentic) or Phase 4 (Manual Lab) **MUST** be complete before Phase 5 (Promotion)
3. Phase 5 (Promotion) **MUST** be complete before Phase 6 (Floor Trading)

### Can Be Done in Parallel
- Phase 2.5 (Data) + Phase 3 (Agentic) - Phase 3 starts with price data, gets enhanced mid-development
- Phase 9 (AWS Infrastructure) - Can be prepared while features are being developed
- Phase 10 (Testing) - Ongoing throughout all phases
- Documentation - Can be written alongside development

---

## Recommended Immediate Next Steps

### This Week (Week 1)
**High Priority:**
1. ✅ Review and validate this NEXT_STEPS.md document
2. ✅ Decide on development strategy (A, B, or C)
3. ✅ Assign developers to tracks (if multi-developer)
4. 🔲 Start Catalyst Ledger implementation (SEC API)

**Medium Priority:**
5. 🔲 Set up LangGraph/LangChain environment (if Phase 3 parallel track)
6. 🔲 Review and update ROADMAP.md with current status

**Low Priority:**
7. 🔲 Begin AWS infrastructure design (if DevOps track)

### Next Week (Week 2)
1. 🔲 Complete SEC API integration
2. 🔲 Start CoinSpot announcements scraper
3. 🔲 LangGraph foundation complete (if Phase 3 parallel)
4. 🔲 First integration checkpoint meeting

---

## Success Metrics

### Phase 2.5 Completion
- [ ] SEC API collecting events daily
- [ ] CoinSpot scraper detecting new listings within 5 minutes
- [ ] Reddit API collecting sentiment every 15 minutes
- [ ] Data quality monitoring operational
- [ ] 100+ catalyst events collected
- [ ] 1000+ sentiment records per day
- [ ] All collectors at 95%+ uptime

### Phase 3 Foundation
- [ ] LangGraph workflow executing end-to-end
- [ ] At least one complete agent workflow (data retrieval → analysis → training → evaluation → report)
- [ ] Natural language query working: "Build me a model to predict Bitcoin price movements"
- [ ] Human-in-the-loop interaction functioning
- [ ] Session management working
- [ ] Artifact storage operational

### Infrastructure
- [ ] AWS infrastructure provisioned via IaC
- [ ] CI/CD pipeline deploying to staging
- [ ] Monitoring and alerting configured
- [ ] Security audit passed
- [ ] Load testing completed

---

## Risk Mitigation

### Technical Risks
1. **Web Scraping Fragility** (CoinSpot announcements)
   - Mitigation: Defensive parsing, monitoring, fallback to manual checks
   - Contingency: If scraper breaks, implement webhook if available

2. **LLM API Costs** (Phase 3)
   - Mitigation: Usage monitoring, rate limits, budget alerts
   - Contingency: Switch to cheaper models for dev/test, optimize prompts

3. **Integration Complexity** (Parallel development)
   - Mitigation: Clear API contracts, mock interfaces, frequent integration testing
   - Contingency: Integration sprints, feature flags, incremental rollout

### Timeline Risks
4. **Scope Creep**
   - Mitigation: Strict adherence to this plan, defer nice-to-haves
   - Contingency: Phase 2.5 Tier 1 only (skip Tier 2/3), simplified Phase 3

5. **Developer Availability**
   - Mitigation: Modular design, clear documentation, knowledge sharing
   - Contingency: De-scope to Strategy A (single developer), extend timeline

---

## Long-Term Roadmap (After Current Priorities)

### Phase 6-7: The Floor (6-10 weeks)
- Live trading execution
- Management dashboard
- P&L tracking
- **Prerequisite**: Phase 3 or 4 complete

### Phase 8: Advanced Features (4-6 weeks)
- Paper trading mode
- A/B testing
- WebSocket real-time updates
- **Can start**: After Phase 6-7 basics complete

### Phase 11: User Experience (8-12 weeks)
- UI/UX enhancements
- Mobile responsiveness
- Onboarding experience
- **Can start**: After user feedback from earlier phases

---

## Conclusion

The Oh My Coins platform has a **solid foundation** (Phases 1-2 complete) and **clear path forward**:

1. **Short-term (4-6 weeks)**: Complete Phase 2.5 data foundation
2. **Medium-term (8-12 weeks)**: Build out Phase 3 agentic system
3. **Long-term (16-24 weeks)**: Deploy to production with live trading

**Key Success Factor**: Leverage parallel development to reduce timeline from **40+ weeks sequential** to **12-20 weeks with 2-3 developers**.

**Next Action**: Review this document with the team, select a development strategy, and begin Week 1 implementation.

---

## Appendix: Resource Requirements

### Development Team
- **Minimum**: 1 full-stack developer (20-24 weeks)
- **Recommended**: 2 full-stack developers (12-16 weeks)
- **Optimal**: 2 full-stack + 1 DevOps (10-14 weeks)

### External Services
- **Phase 2.5**: $0/month (free tier sources only)
- **Phase 3**: $50-150/month (OpenAI/Anthropic API)
- **Phase 9**: $200-500/month (AWS infrastructure - estimate)
- **Optional**: $60/month (Nansen + Newscatcher for Phase 2.5 Tier 2)

### Infrastructure
- PostgreSQL database (sufficient storage for time-series data)
- Redis (for Phase 3 state management)
- Docker & Docker Compose (development)
- AWS account (production deployment)

### Tools & Libraries
- Python 3.11+
- FastAPI, SQLModel, Alembic
- LangChain, LangGraph
- pandas, scikit-learn, xgboost
- pytest, httpx, aioresponses
- Playwright (for scrapers)
- PRAW (Reddit API)
