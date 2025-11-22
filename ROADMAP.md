# Oh My Coins (OMC!) - Development Roadmap

## Progress Summary
**Last Updated**: November 20, 2025

> 📋 **NEW:** See [NEXT_STEPS.md](./NEXT_STEPS.md) for prioritized action plan and timeline  
> 🔀 **NEW:** See [PARALLEL_DEVELOPMENT_GUIDE.md](./PARALLEL_DEVELOPMENT_GUIDE.md) for parallel work opportunities

### Phase 1 Status: ✅ Complete (100%)
- ✅ **Foundation Setup**: Full-stack template integrated, Docker environment configured
- ✅ **Database Schema**: `price_data_5min` table created with optimized indexes
- ✅ **Data Collection**: Collector microservice running with 5-minute scheduler
- ✅ **Error Handling**: Comprehensive retry logic, validation, and logging
- ✅ **Testing**: 15 passing tests with unit and integration coverage
- ✅ **CI/CD**: GitHub Actions workflows for testing and Docker builds

### Phase 2 Status: ✅ Complete (100%)
- ✅ **User Profiles**: Extended user model with trading preferences
- ✅ **Credential Storage**: Secure encryption (AES-256) for API credentials
- ✅ **Coinspot Auth**: HMAC-SHA512 authentication implementation
- ✅ **Testing**: 36+ tests for encryption, auth, and credential management

### Phase 2.5 Status: ✅ Complete (100%)
- ✅ **Database Schema**: All 4 Ledgers schema created (Glass, Human, Catalyst, Exchange)
- ✅ **Collector Framework**: Base classes and orchestrator implemented
- ✅ **DeFiLlama**: Protocol fundamentals collector (Glass Ledger)
- ✅ **CryptoPanic**: News sentiment collector (Human Ledger)
- ✅ **Reddit**: Reddit API collector (Human Ledger)
- ✅ **SEC API**: SEC EDGAR filings collector (Catalyst Ledger)
- ✅ **CoinSpot Announcements**: Exchange announcements scraper (Catalyst Ledger)
- ✅ **Quality Monitoring**: Data quality monitoring system implemented
- ✅ **Metrics Tracking**: Performance metrics tracking system implemented
- ✅ **Testing**: 105+ comprehensive tests passing
- ✅ **Documentation**: Complete Phase 2.5 documentation suite

### Phase 3 Status: ✅ Weeks 1-10 Complete (83% Complete)
- ✅ **LangGraph Foundation**: State machine and workflow orchestration (Weeks 1-2)
- ✅ **Data Agents**: DataRetrievalAgent and DataAnalystAgent with 12 tools (Weeks 3-4)
- ✅ **Modeling Agents**: ModelTrainingAgent and ModelEvaluatorAgent with 7 tools (Weeks 5-6)
- ✅ **ReAct Loop**: Reasoning, conditional routing, error recovery implemented (Weeks 7-8)
- ✅ **Human-in-the-Loop**: Clarification, choice presentation, approval gates, override mechanisms (Weeks 9-10)
- ✅ **Testing**: 167+ unit tests passing (109 + 58 new HiTL tests)
- ✅ **API Endpoints**: 8 new HiTL endpoints implemented
- ✅ **Documentation**: README_LANGGRAPH.md maintained
- 🔄 **Remaining**: Reporting & Finalization (Weeks 11-12)

### Phase 9 Status: ✅ Weeks 1-8 Complete (Infrastructure)
- ✅ **Terraform Modules**: 7 production-ready modules (VPC, RDS, Redis, Security, IAM, ALB, ECS)
- ✅ **Staging Environment**: Fully deployed to AWS (November 19, 2025)
- ✅ **EKS Cluster**: OMC-test cluster with autoscaling GitHub Actions runners
- ✅ **Testing Framework**: 8 automated test suites
- ✅ **Monitoring Stack**: Prometheus, Grafana, Loki, AlertManager deployed (Weeks 7-8)
- ✅ **Application Manifests**: Backend, collectors, and agents deployment ready (Weeks 7-8)
- ✅ **CI/CD Pipeline**: Automated builds with security scanning, deployment workflows (Weeks 7-8)
- ✅ **Documentation**: Complete infrastructure documentation suite
- 🔄 **Remaining**: Production environment deployment (Weeks 9-10), Advanced features (Weeks 11-12)

**Key Achievements**:
- ✅ Complete development environment with live reload
- ✅ Automated data collection from multiple sources (5 collectors operational)
- ✅ Comprehensive data collection (4 Ledgers): Glass, Human, Catalyst, Exchange
- ✅ Robust error handling with retry logic and quality monitoring
- ✅ Extensive test coverage (214+ tests passing across all phases)
- ✅ CI/CD pipeline with linting, testing, and Docker builds
- ✅ Secure credential management with encryption
- ✅ Agentic AI system with ReAct loop and adaptive decision-making
- ✅ Production-ready AWS infrastructure with staging environment deployed
- ✅ EKS cluster with autoscaling GitHub Actions runners

---

## 🎯 Immediate Next Steps (Prioritized)

**Based on sprint review completed 2025-11-20.**
**Context:** Team of 3 developers (A, B, C) with fully operational staging environment on AWS.

### ✅ Completed Work (Current Sprint)
- ✅ Phase 2.5 (Data Collection) - 100% Complete (Developer A)
  - All 5 collectors operational (DeFiLlama, CryptoPanic, Reddit, SEC API, CoinSpot)
  - Quality monitoring and metrics tracking implemented
  - 105+ tests passing
- ✅ Phase 3 Weeks 1-11 (Agentic System) - 92% Complete (Developer B)
  - LangGraph foundation, Data Agents, Modeling Agents, ReAct loop implemented
  - Human-in-the-Loop features complete (Weeks 9-10)
  - Reporting & Artifact Management complete (Week 11)
  - 212+ tests passing (167 + 45 new)
  - 11 API endpoints implemented (8 HiTL + 3 artifact management)
- ✅ Phase 9 Weeks 1-10 (Infrastructure) - Complete (Developer C)
  - Staging environment deployed to AWS
  - Monitoring stack deployed (Prometheus, Grafana, Loki, AlertManager)
  - Application deployment manifests created
  - CI/CD pipeline with security scanning
  - Production configuration and security hardening documentation
- ✅ Phase 6 Weeks 1-6 (Trading System) - Complete (Developer A)
  - Coinspot trading API client operational
  - Order execution service with queue
  - Position management service
  - Algorithm execution engine with safety mechanisms
  - Trade recording and reconciliation
  - Execution scheduler
  - P&L calculation engine with FIFO accounting
  - P&L API endpoints (6 endpoints)
  - 146+ tests passing
  - Ready for integration testing (Weeks 7-8)

### Priority 1: Complete Phase 3 Agentic System (1 week - Developer B)
**Why:** Core differentiator for autonomous algorithm development. Foundation already built.
**Status:** 92% complete, week 12 remaining

**Weeks 9-10: Human-in-the-Loop Features** ✅ COMPLETE
- [x] Implement clarification system for ambiguous inputs
- [x] Implement choice presentation with pros/cons
- [x] Implement user override mechanism
- [x] Add configurable approval gates
- **Deliverables:** ✅ HiTL features operational, user can guide agent decisions

**Week 11: Reporting & Artifact Management** ✅ COMPLETE
- [x] Implement ReportingAgent with summary generation
- [x] Implement artifact management (models, plots, reports)
- [x] Comprehensive testing (44 new tests)
- [x] Documentation updates
- **Deliverables:** ✅ Complete reporting system with visualizations and artifact management

**Week 12: Integration Testing & Finalization** 🔄 IN PROGRESS
- [ ] End-to-end integration tests
- [ ] Performance testing
- [ ] Security testing
- [ ] Complete API documentation
- [ ] Finalize documentation
- **Deliverables:** Complete autonomous ML pipeline ready for production

### Priority 2: Complete Phase 6 Trading System (2 weeks - Developer A)
**Why:** Enable live trading capabilities, leverage completed data infrastructure
**Status:** Weeks 1-6 complete, weeks 7-8 remaining (integration & documentation)

**Weeks 1-2: Coinspot Trading Integration** ✅ COMPLETE
- [x] Implement trading API client (buy/sell endpoints)
- [x] Add order execution service with queue-based submission
- [x] Implement position management and tracking
- [x] Create comprehensive unit tests
- **Deliverables:** ✅ Trading API client operational with 47+ tests

**Weeks 3-4: Algorithm Execution Engine** ✅ COMPLETE
- [x] Create live trading executor for deployed algorithms
- [x] Implement execution scheduler
- [x] Add safety mechanisms (position limits, loss limits, emergency stop)
- [x] Implement trade recording and reconciliation
- **Deliverables:** ✅ Algorithm execution engine operational with 99+ total tests

**Weeks 5-6: P&L Calculation & APIs** ✅ COMPLETE
- [x] Implement P&L engine (realized/unrealized with FIFO accounting)
- [x] Create P&L APIs (summary, by-algorithm, by-coin, history, realized, unrealized)
- [x] Implement comprehensive performance metrics
- [x] Add comprehensive testing (47 new tests)
- **Deliverables:** ✅ P&L tracking operational with 146+ total tests

**Weeks 7-8: Integration & Documentation** 🔄 NEXT
- [ ] Integration testing in Docker environment
- [ ] End-to-end testing with real database
- [ ] Performance testing under load
- [ ] Complete documentation updates
- [ ] Deploy to staging for tester validation
- **Deliverables:** Complete trading system ready for production

### Priority 3: Production Deployment & Security (Ongoing - Developer C)
**Why:** Prepare for production deployment and ensure security hardening
**Status:** Weeks 9-10 complete, production preparation ongoing

**Weeks 9-10: Production Configuration & Security** ✅ COMPLETE
- [x] Create production Terraform configuration
- [x] Implement Kubernetes network security policies
- [x] Document security hardening procedures
- [x] Create production deployment runbook
- **Deliverables:** ✅ Production-ready configuration and security documentation

**Ongoing Activities:**
- [ ] Deploy applications to staging environment
- [ ] Configure DNS and SSL certificates
- [ ] Enable WAF on ALB for security
- [ ] Set up backup policies and disaster recovery
- [ ] Conduct security audit
- **Deliverables:** Production environment ready for go-live

### Priority 4: Quality Assurance & Testing (NEW - Tester)
**Why:** Ensure quality and reliability of all integrations and new code before production deployment
**Status:** New role - testing framework established

**Testing Strategy:**
- **End-of-Sprint Testing:** Tester validates all new code committed during each sprint
- **Integration Testing:** Validate interactions between Phase 2.5 (Data), Phase 3 (Agentic), and Phase 6 (Trading)
- **Regression Testing:** Ensure new changes don't break existing functionality
- **Environment:** Testing on staging environment with synthetic dataset

**Sprint Testing Schedule:**
- **Week 1-2:** Test Phase 3 Week 12 completion (integration tests, performance)
- **Week 3-4:** Test Phase 6 Weeks 5-6 completion (P&L calculation, trade history)
- **Week 5-6:** Integration testing across all phases on staging
- **Week 7-8:** Production readiness testing

**Test Deliverables:**
- Test plans for each sprint
- Test execution reports
- Bug/issue tracking and resolution
- Acceptance criteria validation
- Performance benchmarks

### Priority 5: Production Environment Preparation (Parallel - Developer C)
**Why:** Prepare for production deployment
**Status:** Can be done in parallel with application deployment and testing

**Ongoing Activities:**
- [ ] Configure DNS and SSL certificates
- [ ] Enable WAF on ALB for security
- [ ] Set up backup policies and disaster recovery
- [ ] Implement AWS Config rules
- [ ] Enable GuardDuty monitoring
- [ ] Conduct security audit
- **Deliverables:** Production environment ready for go-live

### Parallel Development Opportunities (All Developers + Tester)
**Can Start Simultaneously:**
- Developer A → Phase 6 Weeks 5-6 (P&L Calculation)
- Developer B → Phase 3 Week 12 (Integration Testing & Finalization)
- Developer C → Production preparation and application deployment support
- **Tester → End-of-sprint testing and validation**

**Coordination Points:**
- Week 2: Dev B completes Phase 3, Tester validates integration tests and performance
- Week 4: Dev A completes P&L system, Tester validates trading and P&L functionality
- Week 6: Integration testing on staging with all systems, Tester performs comprehensive validation
- Week 8: Production readiness review, Tester provides acceptance sign-off

**Testing Integration:**
- **Sprint-End Testing Windows:** 2-3 days at end of each 2-week sprint
- **Test Environment:** Staging with synthetic dataset matching production schema
- **Test Scope:** New features, integrations, regression, performance
- **Collaboration:** Developers support tester with bug fixes and clarifications

---

## Overview
This roadmap outlines the systematic development of Oh My Coins (OMC!), an algorithmic cryptocurrency trading platform with a seamless "Lab-to-Floor" pipeline for algorithm development, testing, and deployment.

## Foundation
**Base Template**: [tiangolo/full-stack-fastapi-template](https://github.com/tiangolo/full-stack-fastapi-template)
- FastAPI backend
- PostgreSQL database
- Vue.js frontend
- Docker containerization
- Built-in authentication and user management

---

## Phase 1: Foundation & Data Collection Service (The Collector)
**Goal**: Establish project infrastructure and implement the data pipeline that feeds The Lab.

### 1.1 Project Initialization
- [x] Initialize private repository: Oh-My-Coins-OMC
- [x] Scaffold from full-stack-fastapi-template
- [x] Configure Docker development environment
- [x] Set up PostgreSQL database from template
- [x] Configure environment variables and secrets management

### 1.2 Data Collection Service (The Collector)
- [x] Implement collector microservice
  - Public API endpoint: `https://www.coinspot.com.au/pubapi/v2/latest`
  - Parse JSON response (bid, ask, last prices)
  - Store time-series data to PostgreSQL
  - Implementation: `backend/app/services/collector.py`
- [x] Design and implement database schema for price data
  - Table: `price_data_5min` (timestamp, coin_type, bid, ask, last)
  - Indexes for efficient time-series queries
  - Migration: `2a5dad6f1c22_add_price_data_5min_table.py`
- [x] Implement 5-minute cron scheduler
  - APScheduler with AsyncIO integration
  - Automatic startup/shutdown with FastAPI lifecycle
  - Implementation: `backend/app/services/scheduler.py`
- [x] Add error handling and retry logic
  - 3 retry attempts with 5-second delays
  - HTTP timeout handling (30 seconds)
  - Data validation (positive prices, required fields)
  - Comprehensive logging with error tracking
- [x] Create monitoring and logging
  - Collection metrics (records stored, duration)
  - Error tracking with stack traces
  - Scheduler status logging
- [x] Write unit and integration tests
  - 15 tests covering all collector functionality
  - Mock tests for API interactions
  - Integration tests with real database
  - Tests: `backend/tests/services/test_collector.py`

### 1.3 DevOps Pipeline
- [x] Set up GitHub Actions workflows
  - Linting (ruff, mypy)
  - Testing (pytest with coverage)
  - Docker image builds for backend and frontend
  - Workflows: `.github/workflows/test.yml`, `.github/workflows/build.yml`
- [x] Configure Docker Compose for local development
  - Volume mounts for live code reloading
  - Automated startup script: `scripts/dev-start.sh`
- [x] Document deployment process
  - `DEVELOPMENT.md` - Developer setup guide
  - `scripts/dev-start.sh` - Automated environment setup
  - Dependency installation documentation

**Deliverables**: 
- ✅ Working data collector service running every 5 minutes
- ✅ Time-series database actively collecting historical price data
- ✅ CI/CD pipeline with automated testing and Docker builds
- ✅ Comprehensive test coverage (15 tests)
- ✅ Production-ready error handling and logging

**Phase 1 - Completed**:
- ✅ Full-stack FastAPI template integrated
- ✅ PostgreSQL database running with Docker
- ✅ `price_data_5min` table schema designed and created
- ✅ Development environment with live code reloading
- ✅ Automated startup script (`scripts/dev-start.sh`)
- ✅ Developer documentation (`DEVELOPMENT.md`)
- ✅ Collector microservice with retry logic
- ✅ APScheduler running 5-minute cron jobs
- ✅ Comprehensive error handling and logging
- ✅ Unit and integration test suite (15 tests passing)
- ✅ GitHub Actions CI/CD workflows

**Files Created/Modified**:
- `backend/app/models.py` - Added `PriceData5Min` and related models
- `backend/app/services/collector.py` - Data collection service with retry logic
- `backend/app/services/scheduler.py` - APScheduler integration
- `backend/app/main.py` - Lifecycle hooks for scheduler
- `backend/tests/services/test_collector.py` - 15 comprehensive tests
- `backend/app/alembic/versions/2a5dad6f1c22_add_price_data_5min_table.py` - Migration
- `docker-compose.override.yml` - Volume mounts for backend, prestart, and tests
- `scripts/dev-start.sh` - Automated development environment setup
- `DEVELOPMENT.md` - Developer setup and workflow documentation
- `.github/workflows/test.yml` - CI testing workflow
- `.github/workflows/build.yml` - Docker image build workflow
- `.env` - Configured for Oh My Coins project

---

## Phase 2: User Authentication & API Credential Management
**Goal**: Secure user management and encrypted storage of Coinspot API credentials.

### 2.1 User Service Enhancement
- [x] Extend template's user model with OMC-specific fields
  - Added timezone, preferred_currency, risk_tolerance, trading_experience
  - Migration: `8abf25dd5d93_add_user_profile_fields.py`
- [x] Implement user profile management API
  - GET /api/v1/users/me/profile - Read full profile
  - PATCH /api/v1/users/me/profile - Update profile with validation

### 2.2 Coinspot Credentials Management
- [x] Design database schema for API credentials
  - Table: `coinspot_credentials` (user_id, api_key_encrypted, api_secret_encrypted)
  - Encryption at rest using industry standards (Fernet/AES-256)
- [x] Implement credential CRUD APIs
  - POST /api/v1/credentials/coinspot
  - GET /api/v1/credentials/coinspot (masked)
  - PUT /api/v1/credentials/coinspot
  - DELETE /api/v1/credentials/coinspot
- [x] Implement HMAC-SHA512 signing utility for Coinspot API
- [x] Test Coinspot API authentication
  - Endpoint: `/api/v2/ro/my/balances`
  - Verify nonce and signature generation
- [x] Add credential validation endpoints
  - POST /api/v1/credentials/coinspot/validate
- [x] Write security tests
  - Encryption service tests (12 tests)
  - Coinspot auth tests (13 tests)
  - Credential API tests (11 tests)

**Deliverables**:
- ✅ Secure credential storage system
- ✅ Working Coinspot API authentication
- ✅ User profile management with trading preferences

---

## Phase 2.5: Comprehensive Data Collection - The 4 Ledgers (PREREQUISITE FOR ADVANCED FEATURES)
**Status**: 🔄 IN PROGRESS (~40% Complete)

**Goal**: Upgrade from basic price collection to comprehensive market intelligence system.

**Strategic Context**: Price data alone is a lagging indicator. To build predictive algorithms and enable the agentic system to make informed decisions, we need to collect the data that actually drives market movements. This phase implements the "4 Ledgers" framework for comprehensive cryptocurrency market intelligence.

**Reference Documents**:
- `Comprehensive_Data_REQUIREMENTS.md` - Complete specification
- `Comprehensive_Data_ARCHITECTURE.md` - Technical architecture
- `Comprehensive_Data_IMPLEMENTATION_PLAN.md` - Week-by-week implementation plan
- `Comprehensive_Data_QUICKSTART.md` - Quick reference guide
- `Comprehensive_Data_EXECUTIVE_SUMMARY.md` - Business case and ROI

### 2.5.1 The 4 Ledgers Framework

This phase implements four distinct types of market data collection:

#### Glass Ledger: On-Chain & Fundamental Data
Transparent view into blockchain networks and protocol fundamentals.

**Data Sources**:
- [x] DeFiLlama API (Free) - Protocol TVL, revenue, fees ✅ IMPLEMENTED
  - 3,000+ protocols covered
  - Real-time TVL and fundamental metrics
  - Implementation: `backend/app/services/collectors/glass/defillama.py`
  - Tests: `backend/tests/services/collectors/glass/test_defillama.py`
- [ ] Dashboard scrapers (Complexity tier)
  - Glassnode public dashboards (active addresses, transaction volumes)
  - Santiment public metrics (social volume, development activity)
  - Implementation: Playwright-based scrapers
- [ ] Nansen API (Optional, $49/mo)
  - Smart money tracking
  - Wallet labeling
  - Token holder analysis

**Database Schema**:
- [x] Table: `protocol_fundamentals` (tvl, revenue, fees, users) ✅ CREATED
- [x] Table: `on_chain_metrics` (active_addresses, transaction_volume, network_fees) ✅ CREATED
- Migration: `c3d4e5f6g7h8_add_comprehensive_data_tables_phase_2_5.py`

**Collection Frequency**: Daily updates (off-peak hours)

#### Human Ledger: Social Sentiment & Narrative
Collective opinion and emotional state of market participants.

**Data Sources**:
- [x] CryptoPanic API (Free) - Crypto news aggregation ✅ IMPLEMENTED
  - News articles from 1,000+ sources
  - Pre-categorized (bullish/bearish/neutral)
  - Implementation: `backend/app/services/collectors/human/cryptopanic.py`
- [ ] Reddit API (Free)
  - Monitor key subreddits (r/CryptoCurrency, r/Bitcoin, etc.)
  - Track post sentiment and engagement
  - Implementation: PRAW-based collector
- [ ] X (Twitter) Scraper (Complexity tier)
  - Track crypto influencers (configurable list)
  - Monitor trending hashtags
  - Playwright-based scraper with proxy rotation
  - Implementation: `backend/app/services/collectors/human/x_scraper.py`
- [ ] Newscatcher API (Optional, $10/mo)
  - Enhanced news coverage
  - Better categorization

**Database Schema**:
- [x] Table: `news_sentiment` (title, source, sentiment, published_at) ✅ CREATED
- [x] Table: `social_sentiment` (platform, content, author, sentiment, engagement) ✅ CREATED
- Migration: `c3d4e5f6g7h8_add_comprehensive_data_tables_phase_2_5.py`

**Collection Frequency**: 5-15 minute intervals

#### Catalyst Ledger: Event-Driven Data
Discrete, high-impact events that trigger immediate market reactions.

**Data Sources**:
- [ ] SEC API (Free) - Corporate filings
  - Monitor crypto-related companies (Coinbase, MicroStrategy, BlackRock)
  - Detect Form 4, 8-K, 10-K filings
  - Implementation: `backend/app/services/collectors/catalyst/sec_api.py`
- [ ] CoinSpot Announcements Scraper
  - New token listings (the "CoinSpot Effect")
  - Exchange maintenance announcements
  - Playwright-based scraper
  - Implementation: `backend/app/services/collectors/catalyst/coinspot_announcements.py`
- [ ] Corporate news tracker
  - Institutional adoption announcements
  - Partnership announcements
  - Network upgrade schedules

**Database Schema**:
- [x] Table: `catalyst_events` (event_type, entity, description, impact_score, timestamp) ✅ CREATED
- Migration: `c3d4e5f6g7h8_add_comprehensive_data_tables_phase_2_5.py`

**Collection Frequency**: Near-real-time (< 1 minute latency for critical events)

#### Exchange Ledger: Market Microstructure
Real-time price and order execution data from CoinSpot.

**Enhancement to Existing System**:
- [x] Basic price collection (already implemented in Phase 1)
- [ ] Enhanced CoinSpot API client
  - Collect bid/ask spreads
  - Track order book depth
  - Monitor volume trends
  - Implementation: Enhance `backend/app/services/collector.py`

**Database Schema**:
- [x] Enhance `price_data_5min` table with bid/ask/volume ✅ CREATED (Phase 1)
- [ ] Table: `order_book_snapshots` (optional, for advanced strategies)

**Collection Frequency**: 10-second intervals (enhanced from 5-minute)

### 2.5.2 Implementation Plan (Tiered Approach)

#### Tier 1: Zero-Budget Implementation (Weeks 1-4)
**Cost**: $0/month | **Complexity**: High (web scraping required)
**Status**: 🔄 PARTIALLY COMPLETE

- [x] Week 1: Foundation & Enhanced Exchange Ledger ✅ COMPLETE
  - [x] Create database schema for all 4 ledgers
  - [x] Implement base collector framework
  - [x] Enhance CoinSpot API client
  - [x] Set up Collection Orchestrator with APScheduler
  - Files: `backend/app/services/collectors/base.py`, `orchestrator.py`, `api_collector.py`
- [ ] Week 2: Catalyst Ledger (Highest ROI)
  - [ ] SEC API integration
  - [ ] CoinSpot announcements scraper
  - [ ] Event detection pipeline
- [x] Week 3: Glass Ledger (Free tier) ✅ PARTIAL
  - [x] DeFiLlama API integration
  - [ ] Basic dashboard scrapers
- [x] Week 4: Human Ledger (Free tier) ✅ PARTIAL
  - [x] CryptoPanic API integration
  - [ ] Reddit API integration
  - [ ] Basic sentiment analysis

**Deliverables**:
- All 4 ledgers operational with free data sources
- 8-10 new database tables
- 6+ collector services running
- Collection orchestrator managing schedules
- Basic data quality monitoring

#### Tier 2: Low-Cost Upgrade (Weeks 5-6)
**Cost**: $60/month | **Complexity**: Medium

- [ ] Week 5: Premium data sources
  - Nansen API integration ($49/mo)
  - Newscatcher API integration ($10/mo)
  - Enhanced sentiment analysis
- [ ] Week 6: Integration and optimization
  - API integration testing
  - Performance optimization
  - Rate limiting refinement

**Deliverables**:
- Enhanced data coverage
- Premium on-chain analytics
- Better news aggregation

#### Tier 3: Complexity Upgrade (Weeks 7-10)
**Cost**: $60/month | **Complexity**: Very High

- [ ] Week 7-8: X (Twitter) scraper
  - Playwright-based scraper
  - Proxy rotation setup
  - Influencer tracking system
  - Anti-bot measure handling
- [ ] Week 9: Advanced sentiment analysis
  - NLP pipeline (BERT/FinBERT)
  - Real-time sentiment scoring
  - Sentiment trend detection
- [ ] Week 10: Advanced dashboard scrapers
  - Glassnode dashboard scraper
  - Santiment dashboard scraper
  - Advanced anti-detection measures

**Deliverables**:
- Complete social media monitoring
- Advanced sentiment analysis
- Full dashboard scraping capability

### 2.5.3 Testing and Deployment (Weeks 11-12)

- [ ] Week 11: Integration testing
  - End-to-end collector testing
  - Data quality validation
  - Performance testing (24/7 operation)
  - Error handling validation
- [ ] Week 12: Deployment and monitoring
  - Production deployment
  - Monitoring dashboard setup
  - Alert configuration
  - Documentation completion

### 2.5.4 Data Quality and Monitoring

- [ ] Implement data quality checks
  - Completeness validation
  - Timeliness monitoring
  - Accuracy verification
- [ ] Create collection metrics dashboard
  - Collection success rates
  - Latency monitoring
  - Error tracking
- [ ] Set up alerting system
  - Collection failures
  - Data quality issues
  - Rate limit warnings

**Deliverables**:
- Comprehensive data collection system across all 4 ledgers
- 10+ active collector services
- 8-10 new database tables with historical data
- Data quality monitoring dashboard
- Complete documentation

**Dependencies**:
- Phase 1 (Foundation) must be complete
- PostgreSQL database with sufficient storage
- Redis for state management (shared with Agentic system)
- Optional: Proxy servers for web scraping (Tier 3)

**Budget Considerations**:
- **Tier 1**: $0/month (free sources only)
- **Tier 2**: $60/month (Nansen + Newscatcher)
- **Tier 3**: $60/month + development time for complex scrapers

**Timeline**: 10-12 weeks for complete implementation (all tiers)

**Note**: This phase provides the data foundation that makes the Agentic system (Phase 3) significantly more effective. Agentic agents can analyze sentiment, on-chain metrics, and events alongside price data to build truly predictive models.

---

## Phase 3: The Lab - Agentic Data Science Capability (ENHANCED WITH COMPREHENSIVE DATA)
**Status**: 🔄 FOUNDATION ONLY (~15% Complete)

**Goal**: Add autonomous multi-agent system for AI-powered algorithm development.

**Strategic Context**: With comprehensive data from Phase 2.5, the agentic system can analyze multiple data sources (prices, sentiment, on-chain metrics, events) to build sophisticated predictive models. Without Phase 2.5, agents are limited to price-only analysis.

### 3.0 Agentic AI System (Weeks 1-14)
This new capability transforms The Lab into an autonomous "data scientist" that can understand high-level trading goals, formulate plans, execute data science workflows, and deliver evaluated models with minimal human intervention.

**Reference Documents**:
- `AGENTIC_REQUIREMENTS.md` - Detailed requirements specification
- `AGENTIC_ARCHITECTURE.md` - Technical architecture design
- `AGENTIC_IMPLEMENTATION_PLAN.md` - Week-by-week implementation plan

#### Foundation Setup (Weeks 1-2)
**Status**: 🔄 PARTIALLY COMPLETE
- [ ] Install and configure LangChain/LangGraph framework
- [ ] Set up Redis for agent state management
- [x] Create database schema for agent sessions ✅ CREATED
  - [x] Table: `agent_sessions`
  - [x] Table: `agent_session_messages`
  - [x] Table: `agent_artifacts`
  - Migration: `c0e0bdfc3471_add_agent_session_tables.py`
- [x] Create project structure for agent system ✅ CREATED
  - Files: `backend/app/services/agent/`
- [x] Implement SessionManager for lifecycle management ✅ IMPLEMENTED
  - File: `backend/app/services/agent/session_manager.py`
  - Tests: `backend/tests/services/agent/test_session_manager.py`
- [x] Create basic AgentOrchestrator skeleton ✅ CREATED
  - File: `backend/app/services/agent/orchestrator.py`
- [ ] Implement API routes for agent sessions
  - POST /api/v1/lab/agent/sessions
  - GET /api/v1/lab/agent/sessions/{id}
  - DELETE /api/v1/lab/agent/sessions/{id}
  - WS /api/v1/lab/agent/sessions/{id}/stream

#### Data Agents (Weeks 3-4)
**Status**: 🔄 MINIMAL IMPLEMENTATION
- [x] Implement DataRetrievalAgent ✅ PARTIAL
  - File: `backend/app/services/agent/agents/data_retrieval.py`
  - Base structure created, tools not fully implemented
  - [ ] Tool: fetch_price_data (query price_data_5min)
  - [ ] Tool: fetch_sentiment_data (query news_sentiment, social_sentiment) [requires Phase 2.5]
  - [ ] Tool: fetch_on_chain_metrics (query on_chain_metrics, protocol_fundamentals) [requires Phase 2.5]
  - [ ] Tool: fetch_catalyst_events (query catalyst_events) [requires Phase 2.5]
  - [ ] Tool: get_available_coins
  - [ ] Tool: get_data_statistics
- [ ] Implement DataAnalystAgent
  - [ ] Tool: calculate_technical_indicators (SMA, EMA, RSI, MACD)
  - [ ] Tool: analyze_sentiment_trends (sentiment correlation with price) [requires Phase 2.5]
  - [ ] Tool: analyze_on_chain_signals (address activity, TVL changes) [requires Phase 2.5]
  - Tool: detect_catalyst_impact (event-driven analysis) [requires Phase 2.5]
  - Tool: clean_data (handle missing values, outliers)
  - Tool: perform_eda (exploratory data analysis)
  - Tool: create_features (feature engineering across all 4 ledgers)

#### Modeling Agents (Weeks 5-6)
- [ ] Implement ModelTrainingAgent
  - Tool: train_classification_model (LogisticRegression, RandomForest, XGBoost)
  - Tool: train_regression_model
  - Tool: cross_validate_model
  - Support for scikit-learn API
- [ ] Implement ModelEvaluatorAgent
  - Tool: evaluate_model (accuracy, F1, precision, recall, AUC-ROC)
  - Tool: tune_hyperparameters (GridSearchCV)
  - Tool: compare_models (side-by-side comparison)
  - Tool: calculate_feature_importance

#### Orchestration & ReAct Loop (Weeks 7-8)
- [ ] Implement LangGraph state machine
  - Define AgentState with all workflow states
  - Create workflow nodes (planning, retrieval, analysis, training, evaluation, reporting)
  - Define state transitions and conditional edges
- [ ] Implement ReAct (Reason-Act-Observe) loop
  - Iterative refinement capabilities
  - Model selection and hyperparameter tuning logic
  - Error handling and recovery
- [ ] Connect all agents to orchestrator
- [ ] End-to-end workflow testing

#### Human-in-the-Loop (Weeks 9-10)
- [ ] Implement clarification system
  - Detect ambiguous inputs and data issues
  - Generate clarification questions
  - Handle user responses
- [ ] Implement choice presentation
  - Present model comparison with pros/cons
  - Show performance tradeoffs
  - Provide recommendations
- [ ] Implement user override mechanism
  - Override model selection
  - Modify hyperparameters
  - Restart from specific steps
- [ ] Add approval gates
  - Configurable approval points in workflow
  - Auto-approve vs manual modes

#### Reporting & Completion (Weeks 11-12)
- [ ] Implement ReportingAgent
  - Tool: generate_summary (natural language summaries)
  - Tool: create_comparison_report
  - Tool: generate_recommendations
- [ ] Implement artifact management
  - Save trained models (.pkl, .joblib)
  - Save generated plots (.png)
  - Save final reports (Markdown/HTML)
- [ ] Implement secure code sandbox
  - RestrictedPython environment
  - Resource limits (CPU, memory, time)
  - Allowed imports whitelist
  - Safety validation

#### Testing & Documentation (Weeks 13-14)
- [ ] Comprehensive unit tests (80%+ coverage)
- [ ] Integration tests (end-to-end workflows)
- [ ] Performance testing (concurrent sessions)
- [ ] Security audit and validation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guides and tutorials
- [ ] Best practices documentation

**Deliverables**:
- Autonomous multi-agent system operational
- Natural language goal understanding
- Automated data science workflow execution
- Model training and evaluation
- Human-in-the-loop features
- Comprehensive reporting
- 80%+ test coverage
- Complete documentation

**Dependencies**:
- Phase 1 (Foundation) must be complete
- Phase 2 (User Authentication) recommended for user-specific sessions
- **Phase 2.5 (Comprehensive Data) highly recommended** - enables multi-source analysis
  - Without Phase 2.5: Limited to price-only analysis
  - With Phase 2.5: Can analyze sentiment, on-chain metrics, and catalysts
- LangChain, LangGraph (agent framework)
- OpenAI or Anthropic API (LLM provider)
- Redis (state management)
- pandas, scikit-learn, xgboost (data science)
- matplotlib, seaborn (visualization)

---

## Phase 4: The Lab - Manual Algorithm Development
**Goal**: Create a sandbox environment for manual algorithm development and backtesting.

**Note**: This phase can be implemented independently or deferred if Phase 3 (Agentic) provides sufficient algorithm development capabilities.

### 4.1 Algorithm Development Infrastructure
- [ ] Design algorithm database schema
  - Table: `algorithms` (id, user_id, name, description, type, parameters, status, created_at, updated_at)
  - Table: `algorithm_versions` (id, algorithm_id, version, code, created_at)
- [ ] Implement algorithm CRUD APIs
  - POST /api/v1/lab/algorithms
  - GET /api/v1/lab/algorithms
  - GET /api/v1/lab/algorithms/{id}
  - PUT /api/v1/lab/algorithms/{id}
  - DELETE /api/v1/lab/algorithms/{id}

### 4.2 Scikit-learn Integration
- [ ] Design algorithm interface compatible with sklearn API
  - Support for: fit(), predict(), score() methods
  - Feature engineering pipeline support
- [ ] Implement algorithm execution sandbox
  - Isolated execution environment
  - Resource limits (CPU, memory, time)
  - Safe import restrictions
- [ ] Create algorithm templates
  - Moving average crossover
  - Mean reversion
  - ML-based (regression, classification)
  - Reinforcement learning skeleton

### 4.3 Backtesting Engine
- [ ] Implement historical data query service
  - Query interface to `price_data_5min`
  - Date range filtering
  - Multiple coin support
- [ ] Design backtest execution engine
  - Simulate trades with historical data
  - Calculate P&L, Sharpe ratio, max drawdown
  - Transaction cost modeling
- [ ] Implement backtest results storage
  - Table: `algorithm_backtest_runs` (id, algorithm_id, start_date, end_date, parameters, results_json, created_at)
- [ ] Create backtest API endpoints
  - POST /api/v1/lab/backtest
  - GET /api/v1/lab/backtest/{id}
  - GET /api/v1/lab/algorithms/{id}/backtests
- [ ] Build backtest results visualization

### 4.4 Lab Frontend
- [ ] Create Vue.js components for algorithm development
  - Code editor with syntax highlighting
  - Parameter configuration interface
  - Backtest configuration form
- [ ] Implement results dashboard
  - Performance metrics display
  - P&L charts
  - Trade history table
- [ ] Add algorithm comparison tools

**Deliverables**:
- Working algorithm development platform
- Backtesting engine with historical data
- Lab frontend interface

---

## Phase 5: Algorithm Promotion & Packaging
**Goal**: Enable validated algorithms to be packaged and deployed to The Floor.

### 5.1 Algorithm Packaging System
- [ ] Define promotion criteria
  - Minimum backtest performance thresholds
  - Risk management requirements
  - Validation checklist
- [ ] Implement algorithm packaging
  - Serialize algorithm state
  - Bundle with dependencies
  - Version control
- [ ] Create promotion workflow
  - POST /api/v1/lab/algorithms/{id}/promote
  - Validation checks
  - Status transition (lab → deployable → deployed)

### 5.2 Deployment Registry
- [ ] Design deployment schema
  - Table: `deployed_algorithms` (id, algorithm_id, user_id, status, deployed_at, parameters)
- [ ] Implement deployment APIs
  - GET /api/v1/floor/available-algorithms
  - POST /api/v1/floor/deploy
  - GET /api/v1/floor/deployments

**Deliverables**:
- Algorithm promotion system
- Deployment registry

---

## Phase 6: The Floor (Live Trading Platform)
**Goal**: Execute deployed algorithms with real Coinspot API integration.

### 5.1 Coinspot Trading Integration
- [ ] Implement trading API client
  - POST /my/buy endpoint wrapper
  - POST /my/sell endpoint wrapper
  - GET /my/orders for order management
  - GET /my/balances for portfolio tracking
- [ ] Add order execution service
  - Queue-based order submission
  - Order status tracking
  - Retry logic with exponential backoff
- [ ] Implement position management
  - Real-time portfolio tracking
  - Table: `positions` (user_id, coin_type, quantity, avg_price, updated_at)

### 5.2 Algorithm Execution Engine
- [ ] Create live trading executor
  - Load deployed algorithms
  - Fetch real-time price data
  - Generate trading signals
  - Execute trades via Coinspot API
- [ ] Implement execution scheduler
  - Per-algorithm execution frequency
  - Concurrent execution management
  - Resource allocation
- [ ] Add safety mechanisms
  - Maximum position size limits
  - Daily loss limits
  - Emergency stop functionality

### 5.3 Trade Recording
- [ ] Design trade history schema
  - Table: `trades` (id, user_id, algorithm_id, coin_type, side, quantity, price, timestamp, fees, status)
- [ ] Implement trade logging
- [ ] Create trade reconciliation service
  - Match orders with Coinspot confirmations
  - Handle partial fills

### 5.4 P&L Calculation
- [ ] Implement P&L engine
  - Real-time unrealized P&L
  - Realized P&L on trade close
  - Historical P&L tracking
- [ ] Create P&L APIs
  - GET /api/v1/floor/pnl/summary
  - GET /api/v1/floor/pnl/by-algorithm
  - GET /api/v1/floor/pnl/by-coin

**Deliverables**:
- Live trading execution system
- Coinspot API integration
- P&L tracking

---

## Phase 7: The Floor - Management Dashboard
**Goal**: Provide comprehensive monitoring and control interface for live trading.

### 6.1 Dashboard Backend APIs
- [ ] Algorithm management endpoints
  - GET /api/v1/floor/algorithms (list active)
  - POST /api/v1/floor/algorithms/{id}/activate
  - POST /api/v1/floor/algorithms/{id}/pause
  - POST /api/v1/floor/algorithms/{id}/deactivate
  - PUT /api/v1/floor/algorithms/{id}/parameters
- [ ] Monitoring endpoints
  - GET /api/v1/floor/status (overall system status)
  - GET /api/v1/floor/algorithms/{id}/performance
  - GET /api/v1/floor/algorithms/{id}/recent-trades

### 6.2 Dashboard Frontend
- [ ] Create Vue.js dashboard components
  - Algorithm status cards (active, paused, P&L)
  - Real-time P&L display
  - Trade history table with filters
  - Performance charts (cumulative P&L, drawdown)
- [ ] Implement control panel
  - Activate/pause/stop buttons
  - Parameter adjustment interface
  - Emergency stop button
- [ ] Add portfolio overview
  - Current positions by coin
  - Total portfolio value
  - Allocation pie chart
- [ ] Create alert system
  - Performance alerts
  - Error notifications
  - Daily summary emails

**Deliverables**:
- Comprehensive management dashboard
- Real-time monitoring interface
- Algorithm control panel

---

## Phase 8: Advanced Features & Optimization
**Goal**: Enhance platform capabilities and performance.

### 7.1 Advanced Algorithm Features
- [ ] Add live paper trading mode
  - Simulate trades without execution
  - Testing deployed algorithms with real-time data
- [ ] Implement algorithm A/B testing
  - Run multiple versions simultaneously
  - Compare performance metrics
- [ ] Add reinforcement learning support
  - Gym-style environment
  - State/action/reward framework
  - Training on historical data

### 7.2 Performance Optimization
- [ ] Optimize database queries
  - Add appropriate indexes
  - Implement query result caching
- [ ] Implement WebSocket support
  - Real-time price updates
  - Live dashboard updates
- [ ] Add Redis caching layer
  - Cache frequently accessed data
  - Rate limiting for Coinspot API

### 7.3 Enhanced Analytics
- [ ] Advanced performance metrics
  - Sharpe ratio, Sortino ratio
  - Maximum drawdown, recovery time
  - Win rate, profit factor
- [ ] Risk analytics
  - Value at Risk (VaR)
  - Portfolio correlation analysis
- [ ] Market condition detection
  - Volatility regime classification
  - Trend identification

**Deliverables**:
- Enhanced algorithm capabilities
- Optimized system performance
- Advanced analytics tools

---

## Phase 9: Production Deployment & AWS Migration
**Goal**: Deploy production-ready system to AWS infrastructure.

### 8.1 AWS Infrastructure Setup
- [ ] Design AWS architecture
  - ECS/EKS for microservices
  - RDS for PostgreSQL
  - ElastiCache for Redis
  - S3 for algorithm storage
  - CloudWatch for monitoring
- [ ] Set up VPC and security groups
- [ ] Configure load balancers
- [ ] Set up auto-scaling policies

### 8.2 Production Deployment Pipeline
- [ ] Create production GitHub Actions workflows
  - Build and push Docker images to ECR
  - Deploy to ECS/EKS
  - Database migrations
  - Health checks
- [ ] Implement blue-green deployment
- [ ] Set up monitoring and alerting
  - CloudWatch dashboards
  - PagerDuty integration
  - Log aggregation with CloudWatch Logs

### 8.3 Security Hardening
- [ ] Security audit
  - Penetration testing
  - Dependency vulnerability scanning
- [ ] Implement secrets management
  - AWS Secrets Manager integration
  - Rotate credentials regularly
- [ ] Set up WAF rules
- [ ] Enable encryption at rest and in transit
- [ ] Configure backup strategy

### 8.4 Documentation & Training
- [ ] Complete API documentation (OpenAPI/Swagger)
- [ ] Write user guides
  - Getting started guide
  - Algorithm development tutorial
  - Trading best practices
- [ ] Create video tutorials
- [ ] Document operational runbooks

**Deliverables**:
- Production AWS deployment
- Comprehensive security measures
- Complete documentation

---

## Phase 10: Testing & Quality Assurance
**Goal**: Ensure system reliability and correctness.

### 10.1 Testing Strategy
- [ ] Unit tests (>80% coverage)
  - All service functions
  - Algorithm execution logic
  - P&L calculations
- [ ] Integration tests
  - API endpoint tests
  - Database interaction tests
  - Coinspot API mock tests
- [ ] End-to-end tests
  - Complete user workflows
  - Lab-to-Floor pipeline
  - Trading execution flows
- [ ] Load testing
  - Concurrent algorithm execution
  - High-frequency data ingestion
  - API rate limits

### 10.2 Quality Assurance
- [ ] Code review process
- [ ] Static analysis (mypy, pylint)
- [ ] Security scanning (Bandit, Safety)
- [ ] Performance profiling
- [ ] User acceptance testing

**Deliverables**:
- Comprehensive test suite
- Quality assurance processes
- Performance benchmarks

---

## Phase 11: User Interaction & User Experience (FUTURE DEVELOPMENT)
**Goal**: Enhance user experience across all system interfaces with modern, intuitive design and seamless workflows.

**Strategic Context**: While the backend systems (data collection, agentic AI, trading execution) provide the core functionality, user experience determines adoption and satisfaction. This phase focuses on making the platform accessible, intuitive, and delightful to use.

**Note**: This is a placeholder phase for future development. Specific requirements will be refined based on:
- User feedback from Phases 1-10
- Usability testing results
- Market research and competitive analysis
- Technical debt and refactoring needs

### 11.1 The Lab User Experience (PLACEHOLDER)

#### 11.1.1 Agentic Interface Enhancements
- [ ] **Natural Language Interface Improvements**
  - Enhanced prompt templates and examples
  - Auto-complete for common trading goals
  - Real-time validation and suggestions
  - Interactive tutorial for first-time users
- [ ] **Session Management UI**
  - Visual workflow progress indicators
  - Session history and replay capabilities
  - Ability to fork/clone sessions
  - Collaborative session sharing (multi-user)
- [ ] **Results Visualization**
  - Interactive charts and graphs
  - Model comparison visualizations
  - Feature importance visualizations
  - Performance metric dashboards
- [ ] **Human-in-the-Loop UX**
  - Intuitive clarification dialogs
  - Rich model comparison interfaces
  - One-click approvals and overrides
  - Context-aware help and tooltips

#### 11.1.2 Manual Development Interface (if Phase 4 implemented)
- [ ] **Code Editor Enhancements**
  - Advanced syntax highlighting
  - Auto-completion for common patterns
  - Inline documentation
  - Code snippets library
- [ ] **Algorithm Management**
  - Drag-and-drop parameter configuration
  - Visual algorithm pipeline builder
  - Version history with diff views
  - Templates gallery with previews
- [ ] **Backtesting Results**
  - Interactive P&L charts with zoom/pan
  - Trade-by-trade drill-down
  - Comparison mode (side-by-side)
  - Export to PDF/Excel functionality

### 11.2 The Floor User Experience (PLACEHOLDER)

#### 11.2.1 Trading Dashboard Redesign
- [ ] **Real-Time Monitoring**
  - Customizable dashboard layouts
  - Widget-based interface (drag-and-drop)
  - Multi-screen support
  - Dark/light mode themes
- [ ] **Algorithm Control Panel**
  - Quick start/stop toggles with confirmations
  - Visual status indicators (color-coded)
  - Performance sparklines on cards
  - Emergency stop (prominent, safe)
- [ ] **Portfolio Overview**
  - Interactive portfolio allocation charts
  - Real-time P&L updates with animations
  - Position cards with key metrics
  - Risk exposure visualization

#### 11.2.2 Notifications and Alerts
- [ ] **Alert System**
  - Customizable alert rules
  - Multi-channel notifications (email, SMS, push)
  - Alert priority levels
  - Snooze and dismiss capabilities
- [ ] **Activity Feed**
  - Real-time trade notifications
  - System events and errors
  - Performance milestones
  - Filterable and searchable

### 11.3 Mobile Experience (PLACEHOLDER)

#### 11.3.1 Responsive Design
- [ ] **Mobile-First Dashboard**
  - Touch-optimized controls
  - Swipe gestures for navigation
  - Simplified views for small screens
  - Progressive web app (PWA) support
- [ ] **Mobile Monitoring App**
  - Portfolio overview
  - Quick algorithm controls
  - Push notifications
  - Biometric authentication

#### 11.3.2 Mobile Limitations
- [ ] Define which features are mobile-accessible
- [ ] Design mobile-specific workflows
- [ ] Consider read-only vs. full-control modes

### 11.4 Onboarding and Help (PLACEHOLDER)

#### 11.4.1 User Onboarding
- [ ] **First-Time User Experience**
  - Interactive product tour
  - Step-by-step setup wizard
  - Sample algorithms and data
  - Achievement system (gamification)
- [ ] **Documentation Integration**
  - In-app help system
  - Context-sensitive documentation
  - Video tutorials
  - FAQ and troubleshooting

#### 11.4.2 Advanced User Features
- [ ] **Power User Tools**
  - Keyboard shortcuts
  - Bulk operations
  - Advanced filters and search
  - Custom views and workspaces
- [ ] **API Explorer**
  - Interactive API documentation
  - Try-it-out functionality
  - Code generation for common tasks
  - Webhook testing

### 11.5 Accessibility and Internationalization (PLACEHOLDER)

#### 11.5.1 Accessibility (a11y)
- [ ] **WCAG 2.1 AA Compliance**
  - Screen reader support
  - Keyboard navigation
  - High contrast mode
  - Adjustable font sizes
- [ ] **Inclusive Design**
  - Color-blind friendly palettes
  - Reduced motion options
  - Clear error messages
  - Alt text for all images

#### 11.5.2 Internationalization (i18n)
- [ ] **Multi-Language Support**
  - UI translations (priority languages TBD)
  - Currency localization
  - Date/time formatting
  - Right-to-left (RTL) language support
- [ ] **Regional Considerations**
  - Timezone handling
  - Regional data privacy compliance
  - Local payment methods (if applicable)

### 11.6 Performance and Optimization (PLACEHOLDER)

#### 11.6.1 Frontend Performance
- [ ] **Load Time Optimization**
  - Code splitting and lazy loading
  - Image optimization
  - CDN for static assets
  - Service workers for offline support
- [ ] **Runtime Performance**
  - Virtual scrolling for large lists
  - Debouncing and throttling
  - Optimistic UI updates
  - Efficient re-rendering

#### 11.6.2 User Experience Metrics
- [ ] **Monitoring and Analytics**
  - Page load times
  - Time to interactive
  - User interaction tracking
  - Error tracking and reporting
- [ ] **A/B Testing Framework**
  - Feature flag system
  - Experiment tracking
  - User segmentation
  - Results analysis

### 11.7 Design System (PLACEHOLDER)

#### 11.7.1 Component Library
- [ ] **Reusable Components**
  - Buttons, forms, cards
  - Charts and graphs
  - Modals and dialogs
  - Navigation components
- [ ] **Design Tokens**
  - Colors, typography, spacing
  - Consistent styling
  - Theme customization
  - Brand guidelines

#### 11.7.2 Documentation
- [ ] **Component Documentation**
  - Storybook or similar
  - Usage examples
  - Best practices
  - Accessibility notes

**Deliverables** (Future):
- Modern, intuitive user interfaces across all system components
- Mobile-responsive design with PWA support
- Comprehensive onboarding and help system
- Accessibility compliance (WCAG 2.1 AA)
- Multi-language support (i18n)
- Design system and component library
- Performance optimizations (< 3s load time)
- User experience metrics and monitoring

**Dependencies**:
- Phases 1-10 should be substantially complete before major UX work
- User feedback from early phases will inform priorities
- Design resources (UX designer, UI designer)
- User research and usability testing

**Timeline**: 8-12 weeks (estimated, will be refined)

**Budget Considerations**:
- UX/UI design resources
- User research and testing
- Frontend development effort
- Design system tooling
- Analytics and monitoring tools

**Priority Areas** (To Be Determined):
1. Critical: Dashboard usability improvements
2. High: Mobile responsiveness
3. Medium: Onboarding experience
4. Low: Advanced customization features

**Success Metrics** (To Be Defined):
- User satisfaction scores
- Task completion rates
- Time to complete common workflows
- Mobile usage metrics
- Accessibility audit scores
- Page load performance

---

## Success Criteria
- ✅ Data collector ingesting prices every 5 minutes
- [ ] Comprehensive data collection (4 Ledgers: Glass, Human, Catalyst, Exchange)
- [ ] Agentic AI system operational with natural language interface
- [ ] Users can develop and backtest algorithms in The Lab (manual or agentic)
- [ ] Algorithms can be promoted from Lab to Floor
- [ ] Live trading execution with Coinspot API
- [ ] Real-time P&L tracking and dashboard
- ✅ Secure credential management
- [ ] Production deployment on AWS
- [ ] Comprehensive documentation
- [ ] Modern, intuitive user experience (Phase 11)

---

## Timeline Estimates

### Core Development Phases
- **Phase 1-2**: 3-4 weeks (Foundation & Authentication) ✅ **COMPLETE**
- **Phase 2.5**: 10-12 weeks (Comprehensive Data Collection - The 4 Ledgers)
  - Tier 1 (Free): 4 weeks
  - Tier 2 (Low-Cost): +2 weeks
  - Tier 3 (Complexity): +4 weeks
  - Testing & Deployment: +2 weeks
- **Phase 3**: 14 weeks (Agentic AI System)
- **Phase 4**: 6-8 weeks (Manual Lab Development) - *Optional, can be deferred*
- **Phase 5**: 2-3 weeks (Algorithm Promotion & Packaging)
- **Phase 6**: 6-8 weeks (The Floor - Live Trading)
- **Phase 7**: 4-6 weeks (The Floor - Management Dashboard)
- **Phase 8**: 4-6 weeks (Advanced Features & Optimization)
- **Phase 9**: 4-6 weeks (AWS Deployment)
- **Phase 10**: Ongoing (Testing & QA)
- **Phase 11**: 8-12 weeks (User Experience Enhancements) - *Future*

### Recommended Implementation Order
1. **Phase 2.5 (Comprehensive Data)** - Enables better algorithms
2. **Phase 3 (Agentic AI)** - Leverages comprehensive data
3. **Phase 6-7 (The Floor)** - Enable live trading
4. **Phase 9 (AWS Deployment)** - Production infrastructure
5. **Phase 11 (UX)** - Polish and refinement

### Timeline Options

**Option A: Comprehensive Approach (Recommended)**
- Complete Phase 2.5 → Phase 3 → Phase 6-7 → Phase 9
- Timeline: 40-50 weeks (10-12 months)
- Result: Full-featured platform with comprehensive data and AI

**Option B: Fast-to-Market**
- Skip Phase 2.5 Tier 3 (complex scrapers)
- Implement Phase 3 with limited data
- Deploy Phase 6-7 (The Floor)
- Timeline: 30-35 weeks (7-9 months)
- Result: Functional platform, can enhance data collection later

**Option C: MVP**
- Phase 2.5 Tier 1 only (free sources)
- Phase 6-7 (The Floor) without Agentic
- Timeline: 20-25 weeks (5-6 months)
- Result: Basic live trading platform, add AI later

**Total Estimated Timeline**: 
- MVP: 5-6 months
- Fast-to-Market: 7-9 months
- Comprehensive: 10-12 months
- Full Platform with UX: 12-15 months

---

## Parallel Development Opportunities

**Strategic Context**: Many phases can be developed in parallel by different team members or work streams, significantly reducing overall timeline. This section identifies dependencies and parallelization opportunities.

### Phase Dependencies Matrix

```
Phase 1 (Foundation) → [COMPLETE]
    ↓
Phase 2 (Auth & Credentials) → [COMPLETE]
    ↓
    ├─→ Phase 2.5 (Comprehensive Data) ─┐
    │                                     │
    ├─→ Phase 3 (Agentic AI)* ───────────┤
    │                                     │
    └─→ Phase 4 (Manual Lab)* ───────────┤
                                          ↓
                                    Phase 5 (Promotion)
                                          ↓
                                    Phase 6 (Floor Trading)
                                          ↓
                                    Phase 7 (Floor Dashboard)
                                          ↓
    ┌────────────────────────────────────┤
    │                                     │
Phase 8 (Advanced Features) ←───────────┤
    │                                     │
Phase 9 (AWS Deployment) ←──────────────┤
    │                                     │
Phase 10 (Testing & QA) ←───────────────┘ (Ongoing throughout)
    ↓
Phase 11 (User Experience) (Future, informed by all phases)

* Phase 3 benefits greatly from Phase 2.5 data but can start in parallel
* Phase 4 is optional and independent of Phase 3
```

### Parallelization Strategies

#### Strategy 1: Two-Track Development (Recommended)
**Team Size**: 2-3 developers

**Track A: Data Foundation**
- Developer 1: Phase 2.5 (Comprehensive Data Collection)
  - Week 1-4: Tier 1 (Free sources)
  - Week 5-6: Tier 2 (Premium sources)
  - Week 7-10: Tier 3 (Complex scrapers)
  - Week 11-12: Testing & deployment

**Track B: AI & Trading System**
- Developer 2: Phase 3 (Agentic AI System)
  - Week 1-14: Agentic system implementation
  - Can start with existing price data
  - Enhanced with comprehensive data as Track A completes
- Developer 3: Phase 6-7 (The Floor)
  - Can start after Week 8 of Track B
  - Week 9-16: Trading execution and dashboard

**Timeline Impact**: 16 weeks (4 months) instead of 32 weeks (8 months) sequential
**Dependencies**: 
- Track B (Agentic) starts with price-only data, gets enhanced mid-development
- Track B (Floor) waits for Agentic core to be functional

---

#### Strategy 2: Three-Track Development (Maximum Parallelization)
**Team Size**: 3-4 developers

**Track A: Data Infrastructure**
- Developer 1: Phase 2.5 (Comprehensive Data)
  - Week 1-12: All tiers + testing

**Track B: Algorithm Development**
- Developer 2: Phase 3 (Agentic AI)
  - Week 1-14: Full agentic system
  - Week 15+: Integration with Phase 2.5 data
- Developer 3: Phase 4 (Manual Lab) - *Optional*
  - Week 1-8: Manual algorithm development
  - Can run parallel to Track B

**Track C: Trading & Execution**
- Developer 4: Phase 6-7 (The Floor)
  - Week 1-2: Design and planning
  - Week 3-10: Trading execution engine
  - Week 11-14: Management dashboard

**Timeline Impact**: 14-16 weeks (3.5-4 months) for core functionality
**Risk**: Higher coordination overhead, potential integration challenges

---

#### Strategy 3: Sequential with Partial Overlap (Conservative)
**Team Size**: 1-2 developers

**Phase Progression**:
1. Phase 2.5 Tier 1 (4 weeks) - Developer 1
2. **Parallel Start**:
   - Phase 2.5 Tier 2+3 (6 weeks) - Developer 1
   - Phase 3 Foundation (6 weeks) - Developer 2 (starts Week 5)
3. **Parallel Continue**:
   - Phase 2.5 Testing (2 weeks) - Developer 1
   - Phase 3 Agents (6 weeks) - Developer 2
4. **Join for Integration**:
   - Phase 3 + 2.5 Integration (2 weeks) - Both
5. Phase 6-7 (10 weeks) - Both developers

**Timeline Impact**: 20-24 weeks (5-6 months)
**Benefit**: Lower risk, better knowledge sharing

---

### Independent Workstreams (Can Run Anytime)

These components can be developed at any time without blocking other work:

#### Workstream 1: Documentation & Testing (Ongoing)
- **Phase 10**: Testing & QA
  - Unit tests written alongside feature development
  - Integration tests after phase completion
  - Can be done by any developer or dedicated QA
- **Documentation**:
  - API documentation (OpenAPI/Swagger)
  - User guides and tutorials
  - Operational runbooks
  - Can be done by technical writer or developers

#### Workstream 2: Infrastructure & DevOps (Parallel to All)
- **Phase 9**: AWS Deployment preparation
  - Infrastructure as Code (Terraform/CloudFormation)
  - CI/CD pipeline enhancements
  - Monitoring and alerting setup
  - Can be done by DevOps engineer in parallel
  - Final deployment waits for Phase 6-7 completion

#### Workstream 3: Advanced Features (After Core)
- **Phase 8**: Advanced Features & Optimization
  - Paper trading mode
  - A/B testing framework
  - WebSocket real-time updates
  - Can start once Phase 6-7 basics are complete
  - Doesn't block other work

#### Workstream 4: User Experience (Future)
- **Phase 11**: UX/UI Enhancements
  - Can start design work early (wireframes, mockups)
  - Implementation waits for user feedback from earlier phases
  - Can be done by frontend specialist in parallel to backend work

---

### Specific Parallel Development Opportunities

#### Within Phase 2.5 (Comprehensive Data)
**4 Independent Collectors** (can be built in parallel by 1-4 developers):
1. **Glass Ledger** (Week 1-3)
   - DeFiLlama API (Week 1)
   - Dashboard scrapers (Week 2-3)
   - Nansen API (Week 3) - if Tier 2
2. **Human Ledger** (Week 1-4)
   - CryptoPanic API (Week 1)
   - Reddit API (Week 2)
   - X (Twitter) scraper (Week 3-4) - if Tier 3
3. **Catalyst Ledger** (Week 1-2)
   - SEC API (Week 1)
   - CoinSpot announcements (Week 2)
4. **Exchange Ledger** (Week 1)
   - Enhanced CoinSpot client

**Parallelization**: All 4 ledgers can be developed simultaneously
**Shared Work**: Database schema (Week 1), Collection orchestrator (Week 1)

---

#### Within Phase 3 (Agentic AI)
**5 Independent Agents** (can be built in parallel by 1-5 developers):
1. **Data Retrieval Agent** (Week 3-4)
2. **Data Analyst Agent** (Week 3-4)
3. **Model Training Agent** (Week 5-6)
4. **Model Evaluator Agent** (Week 5-6)
5. **Reporting Agent** (Week 11-12)

**Parallelization**: Agents 1-2 parallel (Week 3-4), then 3-4 parallel (Week 5-6)
**Shared Work**: Foundation (Week 1-2), Orchestrator (Week 7-8), HiTL (Week 9-10)

---

#### Within Phase 6-7 (The Floor)
**3 Independent Subsystems** (can be built in parallel):
1. **Trading Execution** (Phase 6.1-6.3)
   - Coinspot API client
   - Order execution service
   - Position management
2. **P&L Calculation** (Phase 6.4)
   - P&L engine
   - P&L APIs
3. **Management Dashboard** (Phase 7)
   - Backend APIs
   - Frontend components
   - Alert system

**Parallelization**: Trading execution and P&L can start together, dashboard starts Week 3

---

### Recommended Team Compositions

#### Small Team (1-2 developers)
- Use **Strategy 3** (Sequential with Partial Overlap)
- Timeline: 20-24 weeks
- Focus on critical path, defer optional features

#### Medium Team (2-3 developers)
- Use **Strategy 1** (Two-Track Development)
- Timeline: 16 weeks for core functionality
- Best balance of speed and risk

#### Large Team (3-4+ developers)
- Use **Strategy 2** (Three-Track Development)
- Timeline: 14-16 weeks for core functionality
- Requires strong coordination and integration planning
- Consider adding dedicated QA and DevOps roles

---

### Risk Mitigation for Parallel Development

1. **Integration Points**: Plan integration testing windows between parallel tracks
2. **Shared Resources**: Coordinate database schema changes and migrations
3. **Code Conflicts**: Use feature branches, frequent merges, clear ownership
4. **Knowledge Silos**: Regular sync meetings, code reviews, documentation
5. **Dependency Changes**: API contracts defined upfront, versioning strategy

---

### Critical Path Analysis

**Longest Sequential Path** (cannot be parallelized):
1. Phase 1-2 (Complete) ✅
2. Phase 2.5 OR Phase 3 (whichever comes first)
3. Phase 5 (Promotion) - requires Phase 3 or 4
4. Phase 6 (Trading) - requires Phase 5
5. Phase 7 (Dashboard) - requires Phase 6
6. Phase 9 (AWS) - requires Phase 6-7

**Critical Path Timeline**: ~28-32 weeks (7-8 months) if fully sequential

**With Parallelization**: Can reduce to 14-20 weeks (3.5-5 months) depending on team size

---

## Risk Management

### Technical Risks
1. **Coinspot API Rate Limits**: Implement exponential backoff and respect limits
   - Mitigation: Rate limiting middleware, request queuing, monitoring
2. **Real Money Risk**: Start with paper trading mode, extensive testing before live
   - Mitigation: Sandbox environments, position limits, circuit breakers
3. **Security**: Regular audits, penetration testing, secure credential management
   - Mitigation: Encryption at rest/transit, regular vulnerability scanning, code reviews
4. **Performance**: Load testing, optimization, scalable architecture
   - Mitigation: Caching layers, database optimization, horizontal scaling
5. **Algorithm Bugs**: Sandbox execution, safety limits, emergency stops
   - Mitigation: Comprehensive testing, gradual rollout, kill switches

### Data Collection Risks (Phase 2.5)
6. **Web Scraping Fragility**: Websites change layouts, breaking scrapers
   - Mitigation: Defensive parsing, multiple data sources, monitoring/alerts
7. **Anti-Bot Detection**: Twitter/Glassnode may block automated access
   - Mitigation: Proxy rotation, rate limiting, fallback to manual/API sources
8. **Data Quality Issues**: Incomplete or inaccurate data from free sources
   - Mitigation: Validation rules, cross-source verification, data quality monitoring
9. **API Deprecation**: Free APIs may become paid or deprecated
   - Mitigation: Multiple sources per ledger, budget for paid alternatives

### AI/ML Risks (Phase 3)
10. **LLM API Costs**: OpenAI/Anthropic costs can escalate with usage
    - Mitigation: Usage monitoring, rate limits, local models for some tasks
11. **Model Hallucinations**: LLM may generate incorrect trading logic
    - Mitigation: Human-in-the-loop, validation steps, output constraints
12. **Training Data Drift**: Market conditions change, models become stale
    - Mitigation: Regular retraining, performance monitoring, adaptive algorithms

### Parallel Development Risks
13. **Integration Complexity**: Parallel tracks may conflict during integration
    - Mitigation: Clear API contracts, integration testing windows, feature flags
14. **Knowledge Silos**: Team members working independently lose context
    - Mitigation: Daily standups, code reviews, shared documentation, pair programming
15. **Dependency Deadlocks**: Parallel work blocked waiting for each other
    - Mitigation: Clear dependency mapping, mock interfaces, incremental integration
16. **Code Merge Conflicts**: Simultaneous changes to shared code
    - Mitigation: Small frequent merges, feature branches, clear ownership boundaries
17. **Inconsistent Architecture**: Different developers implement different patterns
    - Mitigation: Architecture reviews, coding standards, shared libraries/utilities
18. **Testing Gaps**: Integration issues not caught until late
    - Mitigation: Continuous integration, automated testing, regular integration milestones

### Project Management Risks
19. **Scope Creep**: Adding features beyond original plan
    - Mitigation: Strict change control, MVP focus, deferred feature backlog
20. **Resource Constraints**: Team size or availability changes
    - Mitigation: Modular design, clear priorities, ability to de-scope
21. **Timeline Pressure**: Rushing to meet deadlines compromises quality
    - Mitigation: Realistic estimates, buffer time, "done means tested"
22. **User Feedback Lag**: Building wrong features without user validation
    - Mitigation: Early prototypes, user testing, iterative releases

---

## Infrastructure: Staging Environment

- **Objective:** Deploy a complete, stable staging environment on AWS using Terraform.
- **Status:** ✅ Deployed (November 19, 2025)
- **Developer:** Developer C (Infrastructure & DevOps)
- **Details:** The staging environment is now fully deployed on AWS via Terraform. This includes:
  - VPC with public/private subnets
  - RDS PostgreSQL for application data
  - ElastiCache Redis for caching and agent state
  - ECS Fargate for containerized services
  - Application Load Balancer with SSL termination
  - EKS cluster (OMC-test) with autoscaling GitHub Actions runners
  - CloudWatch monitoring and logging
  - Complete Terraform modules for production replication
- **Accessible At:** `dashboard.staging.ohmycoins.com`
- **Next Steps:** Deploy applications to staging environment (Phase 2.5 collectors, Phase 3 agentic system)
