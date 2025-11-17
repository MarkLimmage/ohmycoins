# Oh My Coins (OMC!) 🪙

A microservices-based algorithmic cryptocurrency trading platform with a seamless "Lab-to-Floor" pipeline for AI-powered algorithm development, backtesting, and live trading.

## 🎯 Overview

Oh My Coins provides a complete ecosystem for cryptocurrency algorithmic trading:

- **The Collector**: Automated data pipeline gathering cryptocurrency prices every 5 minutes
- **The Lab**: AI-powered autonomous algorithm development platform (NEW - Agentic Capability)
- **The Floor**: Live trading execution with Coinspot API integration (Coming Soon)

## ✨ Key Features

### ✅ Phase 1: Complete
- Real-time cryptocurrency price data collection from Coinspot
- PostgreSQL time-series database with 50,000+ price records
- Robust error handling with retry logic
- Comprehensive test suite (15 tests passing)
- CI/CD pipeline with GitHub Actions

### 🚀 Phase 2: Complete
- User authentication and profile management
- Secure Coinspot API credential storage (AES-256 encryption)
- HMAC-SHA512 signature generation for Coinspot API

### 🤖 Phase 3: NEW - Agentic Data Science Capability (In Planning)
Transform The Lab into an autonomous "data scientist" powered by AI:

- **Natural Language Goals**: "Predict Bitcoin price movements over the next hour"
- **Autonomous Execution**: AI agents automatically fetch data, analyze, train models, and deliver results
- **Multi-Agent System**: 5 specialized agents working collaboratively
  - Data Retrieval Agent
  - Data Analyst Agent  
  - Model Training Agent
  - Model Evaluator Agent
  - Reporting Agent
- **Human-in-the-Loop**: Clarifications, choice presentation, user overrides
- **ReAct Loop**: Iterative refinement and hyperparameter tuning
- **Secure Sandbox**: Safe code execution with resource limits

**📚 Documentation**:
- [Quick Start Guide](./AGENTIC_QUICKSTART.md) - Overview and examples
- [Requirements Specification](./AGENTIC_REQUIREMENTS.md) - Detailed requirements (26KB)
- [Architecture Design](./AGENTIC_ARCHITECTURE.md) - Technical architecture (29KB)
- [Implementation Plan](./AGENTIC_IMPLEMENTATION_PLAN.md) - 14-week plan (19KB)

## 📋 Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Foundation & Data Collection Service |
| Phase 2 | ✅ Complete | User Authentication & API Credentials |
| Phase 3 | 📋 Planning | Agentic Data Science Capability (NEW) |
| Phase 4 | 📅 Planned | The Lab - Manual Algorithm Development |
| Phase 5 | 📅 Planned | Algorithm Promotion & Packaging |
| Phase 6 | 📅 Planned | The Floor - Live Trading Platform |
| Phase 7 | 📅 Planned | Management Dashboard |
| Phase 8 | 📅 Planned | Advanced Features & Optimization |
| Phase 9 | 📅 Planned | Production Deployment & AWS Migration |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway                             │
│                     (FastAPI + Authentication)                   │
└──────────────┬─────────────────────────────────┬────────────────┘
               │                                 │
       ┌───────▼────────┐                ┌──────▼──────┐
       │   User Service │                │  Lab Service│
       │   (Auth/Users) │                │ (Algo Dev)  │
       └───────┬────────┘                └──────┬──────┘
               │                                 │
       ┌───────▼────────────────────────────────▼──────────┐
       │              PostgreSQL Database                   │
       │  (Users, Credentials, Algorithms, Trades, Prices) │
       └───────┬────────────────────────────────┬──────────┘
               │                                 │
    ┌──────────▼────────┐              ┌────────▼─────────────┐
    │ Collector Service │              │   Trading Service    │
    │  (Data Pipeline)  │              │    (The Floor)       │
    └──────────┬────────┘              └────────┬─────────────┘
               │                                 │
    ┌──────────▼────────┐              ┌────────▼─────────────┐
    │  Coinspot Public  │              │  Coinspot Private    │
    │      API          │              │      API             │
    │   (Price Data)    │              │  (Trading/Orders)    │
    └───────────────────┘              └──────────────────────┘
```

### Agentic System Architecture (NEW)

```
User Goal → Agent Orchestrator → Multi-Agent Team → Evaluated Models
                   ↓
              [LangGraph State Machine]
                   ↓
    ┌──────────────┼──────────────┬──────────────┬──────────────┐
    ↓              ↓              ↓              ↓              ↓
Data Retrieval  Data Analyst  Model Trainer  Model Evaluator  Reporter
    Agent          Agent          Agent           Agent        Agent
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.10+
- uv (Python package installer)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/MarkLimmage/ohmycoins.git
   cd ohmycoins
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   uv sync
   ```

4. **Run database migrations**
   ```bash
   uv run alembic upgrade head
   ```

5. **Start backend server**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

6. **Access the application**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend (when ready): http://localhost:5173

For detailed setup instructions, see [DEVELOPMENT.md](./DEVELOPMENT.md)

## 📖 Documentation

### Core Documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design principles
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Developer setup and workflow guide
- [ROADMAP.md](./ROADMAP.md) - Project roadmap and milestones
- [PHASE1_SUMMARY.md](./PHASE1_SUMMARY.md) - Phase 1 completion summary

### Agentic Capability (NEW)
- [AGENTIC_QUICKSTART.md](./AGENTIC_QUICKSTART.md) - Quick reference guide
- [AGENTIC_REQUIREMENTS.md](./AGENTIC_REQUIREMENTS.md) - Detailed requirements
- [AGENTIC_ARCHITECTURE.md](./AGENTIC_ARCHITECTURE.md) - Technical architecture
- [AGENTIC_IMPLEMENTATION_PLAN.md](./AGENTIC_IMPLEMENTATION_PLAN.md) - Implementation plan

## 🧪 Testing

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/services/test_collector.py

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy + SQLModel
- **Database**: PostgreSQL 15+
- **Authentication**: JWT tokens
- **Task Scheduling**: APScheduler
- **Encryption**: Cryptography (Fernet/AES-256)

### Agentic System (NEW)
- **Agent Framework**: LangChain + LangGraph
- **LLM Provider**: OpenAI / Anthropic
- **State Management**: Redis
- **Data Science**: pandas, scikit-learn, xgboost
- **Visualization**: matplotlib, seaborn

### Frontend (Coming Soon)
- **Framework**: Vue.js 3
- **State Management**: Pinia
- **UI Components**: Vuetify
- **Charts**: Chart.js

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (dev), EKS with autoscaling (prod)
- **CI/CD**: GitHub Actions on self-hosted EKS runners with scale-to-zero capability
- **Monitoring**: CloudWatch, Prometheus (future)
- **Cost Optimization**: Cluster Autoscaler enabling 40-60% cost savings

## 📊 Current Data Collection

The Collector service is actively gathering cryptocurrency price data:

- **Frequency**: Every 5 minutes
- **Source**: Coinspot Public API
- **Coins Tracked**: 19+ cryptocurrencies (BTC, ETH, etc.)
- **Records Collected**: 60+ price entries and growing
- **Uptime**: 100% since deployment

## 🔐 Security

- **Credential Encryption**: AES-256 encryption for API credentials
- **Authentication**: JWT-based user authentication
- **Code Sandbox**: Secure execution environment for agent-generated code
- **Input Validation**: All user inputs validated and sanitized
- **Audit Logging**: Complete audit trail of agent actions

## 🤝 Contributing

This is currently a private project. For questions or collaboration, please contact the repository owner.

## 📝 License

Copyright © 2025 Mark Limmage. All rights reserved.

## 🎯 Roadmap Highlights

### Immediate Next Steps (Phase 3)
1. Implement agent framework (LangChain/LangGraph)
2. Create 5 specialized agents
3. Build ReAct loop for iterative refinement
4. Add human-in-the-loop features
5. Comprehensive testing and documentation

### Future Plans
- The Lab: Manual algorithm development (Phase 4)
- The Floor: Live trading execution (Phase 6)
- Management Dashboard (Phase 7)
- AWS Production Deployment (Phase 9)

See [ROADMAP.md](./ROADMAP.md) for the complete development plan.

## 📞 Contact

For questions, feedback, or collaboration:
- **Author**: Mark Limmage
- **GitHub**: [@MarkLimmage](https://github.com/MarkLimmage)

---

**Built with ❤️ for the crypto trading community**# Test autoscaling - Mon Nov 17 21:55:49 AEDT 2025
