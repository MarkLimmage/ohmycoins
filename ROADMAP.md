# Oh My Coins (OMC!) - Development Roadmap

## Progress Summary
**Last Updated**: November 15, 2025

### Phase 1 Status: ✅ Complete (100%)
- ✅ **Foundation Setup**: Full-stack template integrated, Docker environment configured
- ✅ **Database Schema**: `price_data_5min` table created with optimized indexes
- ✅ **Data Collection**: Collector microservice running with 5-minute scheduler
- ✅ **Error Handling**: Comprehensive retry logic, validation, and logging
- ✅ **Testing**: 15 passing tests with unit and integration coverage
- ✅ **CI/CD**: GitHub Actions workflows for testing and Docker builds

**Key Achievements**:
- Complete development environment with live reload
- Automated data collection from Coinspot API every 5 minutes
- Robust error handling with retry logic
- Comprehensive test suite (15 tests passing)
- CI/CD pipeline with linting, testing, and Docker builds

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
- [ ] Extend template's user model with OMC-specific fields
- [ ] Implement user profile management API

### 2.2 Coinspot Credentials Management
- [ ] Design database schema for API credentials
  - Table: `coinspot_credentials` (user_id, api_key_encrypted, api_secret_encrypted)
  - Encryption at rest using industry standards (Fernet/AES-256)
- [ ] Implement credential CRUD APIs
  - POST /api/v1/credentials/coinspot
  - GET /api/v1/credentials/coinspot (masked)
  - PUT /api/v1/credentials/coinspot
  - DELETE /api/v1/credentials/coinspot
- [ ] Implement HMAC-SHA512 signing utility for Coinspot API
- [ ] Test Coinspot API authentication
  - Endpoint: `/api/ro/my/balances/:cointype`
  - Verify nonce and signature generation
- [ ] Add credential validation endpoints
- [ ] Write security tests

**Deliverables**:
- Secure credential storage system
- Working Coinspot API authentication

---

## Phase 3: The Lab (Algorithm Development Platform)
**Goal**: Create a sandbox environment for developing and backtesting trading algorithms.

### 3.1 Algorithm Development Infrastructure
- [ ] Design algorithm database schema
  - Table: `algorithms` (id, user_id, name, description, type, parameters, status, created_at, updated_at)
  - Table: `algorithm_versions` (id, algorithm_id, version, code, created_at)
- [ ] Implement algorithm CRUD APIs
  - POST /api/v1/lab/algorithms
  - GET /api/v1/lab/algorithms
  - GET /api/v1/lab/algorithms/{id}
  - PUT /api/v1/lab/algorithms/{id}
  - DELETE /api/v1/lab/algorithms/{id}

### 3.2 Scikit-learn Integration
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

### 3.3 Backtesting Engine
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

### 3.4 Lab Frontend
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

## Phase 4: Algorithm Promotion & Packaging
**Goal**: Enable validated algorithms to be packaged and deployed to The Floor.

### 4.1 Algorithm Packaging System
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

### 4.2 Deployment Registry
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

## Phase 5: The Floor (Live Trading Platform)
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

## Phase 6: The Floor - Management Dashboard
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

## Phase 7: Advanced Features & Optimization
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

## Phase 8: Production Deployment & AWS Migration
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

## Phase 9: Testing & Quality Assurance
**Goal**: Ensure system reliability and correctness.

### 9.1 Testing Strategy
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

### 9.2 Quality Assurance
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

## Success Criteria
- ✅ Data collector ingesting prices every 5 minutes
- ✅ Users can develop and backtest algorithms in The Lab
- ✅ Algorithms can be promoted from Lab to Floor
- ✅ Live trading execution with Coinspot API
- ✅ Real-time P&L tracking and dashboard
- ✅ Secure credential management
- ✅ Production deployment on AWS
- ✅ Comprehensive documentation

---

## Timeline Estimates
- **Phase 1-2**: 3-4 weeks (Foundation & Authentication)
- **Phase 3-4**: 6-8 weeks (The Lab & Promotion)
- **Phase 5-6**: 6-8 weeks (The Floor & Dashboard)
- **Phase 7**: 4-6 weeks (Advanced Features)
- **Phase 8**: 4-6 weeks (AWS Deployment)
- **Phase 9**: Ongoing (Testing & QA)

**Total Estimated Timeline**: 6-8 months for MVP, 12+ months for full platform

---

## Risk Management
1. **Coinspot API Rate Limits**: Implement exponential backoff and respect limits
2. **Real Money Risk**: Start with paper trading mode, extensive testing before live
3. **Security**: Regular audits, penetration testing, secure credential management
4. **Performance**: Load testing, optimization, scalable architecture
5. **Algorithm Bugs**: Sandbox execution, safety limits, emergency stops

---

## Notes
- This roadmap is a living document and will be updated as requirements evolve
- Each phase should be completed and tested before moving to the next
- Security and testing are integrated throughout, not just in dedicated phases
- User feedback should be incorporated at each milestone
