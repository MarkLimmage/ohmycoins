# Oh My Coins (OMC) - System Architecture

**Version**: 2.0
**Last Updated**: 2026-01-09
**Status**: Consolidated

## 1. Overview
Oh My Coins is a microservices-based platform designed to provide a seamless "Lab-to-Floor" pipeline for algorithmic cryptocurrency trading. It integrates a comprehensive 4-Ledger data collection engine with an autonomous Agentic Data Science capability (The Lab) to enable predictive market intelligence and automated strategy execution.

---

## 2. Architecture Principles
1.  **Microservices**: Strictly separated responsibilities (User, Lab, Floor, Collector).
2.  **API-First**: Communication via RESTful APIs (FastAPI) and Async Events.
3.  **Parallel Development**: Enforced boundaries between Track A (Collectors), Track B (Agents), and Track C (Infra).
4.  **Lab-to-Floor Integrity**: Seamless promotion of algorithms from discovery to execution.
5.  **Security**: Zero-trust credentials, sandboxed agent execution, and end-to-end encryption.

---

## 3. System Architecture Diagram

```mermaid
graph TD
    User[User / Client] -->|HTTPS| Gateway[API Gateway / Load Balancer]
    
    subgraph "Core Services"
        Gateway -->|/auth, /users| UserService[User Service]
        Gateway -->|/lab, /agent| LabService[Lab Service (Agentic)]
        Gateway -->|/floor| FloorService[Trading Service]
        Gateway -->|/data| DataService[Data Service]
    end
    
    subgraph "Data Collection (Track A)"
        Collector[Collector Service] -->|Glass| DeFiLlama
        Collector -->|Human| SocialMedia[Reddit/Twitter/News]
        Collector -->|Catalyst| SEC[SEC/Announcements]
        Collector -->|Exchange| CoinSpot[CoinSpot Public API]
    end
    
    subgraph "The Lab (Track B)"
        LabService --> Orchestrator[Agent Orchestrator]
        Orchestrator --> Planner[Planner Agent]
        Orchestrator --> Analyst[Data Analyst Agent]
        Orchestrator --> Trainer[Model Trainer Agent]
        Orchestrator --> Evaluator[Model Evaluator Agent]
        
        Trainer --> Sandbox[Restricted Python Sandbox]
    end
    
    subgraph "The Floor (Trading)"
        FloorService --> Execution[Order Execution]
        Execution -->|Private API| CoinSpotPrivate[CoinSpot Private API]
    end
    
    subgraph "Persistence Layer"
        UserService & LabService & FloorService & Collector --> DB[(PostgreSQL)]
        LabService & Collector --> Redis[(Redis Cache/State)]
        LabService --> Artifacts[Artifact Store (S3/Local)]
    end
```

---

## 4. Microservices Definition

### 4.1 API Gateway & User Service
*   **Responsibility**: Authentication (JWT), User Management, Credential Storage.
*   **Key Features**:
    *   Fernet/AES-256 encryption for CoinSpot API keys.
    *   Rate limiting and request routing.

### 4.2 Collector Service (Track A)
*   **Responsibility**: Implementation of the **4 Ledgers Framework**.
*   **Components**:
    *   **Glass Ledger**: DeFiLlama, On-chain metrics.
    *   **Human Ledger**: CryptoPanic, Reddit, Twitter (Tier 3).
    *   **Catalyst Ledger**: SEC filings, Exchange listings (Critical latency < 30s).
    *   **Exchange Ledger**: Real-time price/volume data (Latency < 10s).
*   **Tech**: APScheduler, Playwright (Scrapers), Pydantic (Validation).

### 4.3 Lab Service (Track B)
*   **Responsibility**: Autonomous Agentic Data Science.
*   **Architecture**: **LangGraph** State Machine.
*   **Agents**:
    *   **Orchestrator**: Manages ReAct loop and user clarifications.
    *   **Data Retrieval**: Queries 4-Ledger data.
    *   **Analyst**: EDA, Feature Engineering (pandas/ta-lib).
    *   **Trainer**: Model training (scikit-learn/XGBoost) in **Sandbox**.
    *   **Evaluator**: Performance metrics and promotion logic.
*   **Security**: RestrictedPython Sandbox, no network access for generated code.

### 4.4 Trading Service (The Floor)
*   **Responsibility**: Live execution of promoted algorithms.
*   **Key Features**:
    *   Position management and P&L tracking.
    *   Order execution via CoinSpot Private API.
    *   Risk management limits (stop-loss, max drawdown).

---

## 5. Data Architecture

### 5.1 Database Schema (PostgreSQL)

#### Core Data
*   `users`, `coinspot_credentials` (Encrypted)
*   `price_data_5min` (Time-series)

#### 4 Ledgers Data
*   `protocol_fundamentals` (Glass)
*   `news_sentiment`, `social_sentiment` (Human)
*   `catalyst_events` (Catalyst)
*   `orders`, `trades` (Exchange)

#### Agentic Data
*   `agent_sessions`: Stores conversation history and goal state.
*   `agent_artifacts`: Links to trained models and reports.
*   `algorithms`: Versioned algorithm code and metadata.

### 5.2 Caching & State (Redis)
*   **Agent State**: Persists LangGraph state for resumption.
*   **Market Data**: Hot cache for latest prices.
*   **Task Queue**: Celery/APScheduler job management.

---

## 6. Infrastructure (Track C)

### 6.1 Deployment Stack
*   **Containerization**: Docker (Dev), EKS (Prod).
*   **CI/CD**: GitHub Actions with self-hosted runners.
*   **Monitoring**: Prometheus + Grafana (Metrics), ELK Stack (Logs).

### 6.2 Scalability
*   **Horizontal**: Stateless collectors and API workers.
*   **Vertical**: Database read replicas for historical data analysis.

---

## 7. Security Architecture
*   **Credentials**: Never logged, encrypted at rest, decrypted only in memory.
*   **Sandbox**: Agent code runs with `RestrictedPython`, limited imports, and resource quotas (CPU/RAM).
*   **Network**: Collectors use proxy rotation (Tier 3). API uses HTTPS/TLS 1.3.

---

## 8. Technology Stack
*   **Backend**: FastAPI, SQLAlchemy, Pydantic.
*   **AI/ML**: LangChain, LangGraph, OpenAI/Anthropic, Scikit-learn, Pandas.
*   **Data**: PostgreSQL 15+, Redis 7+.
*   **Infra**: AWS (ECS/Fargate, RDS, ElastiCache), Terraform.
*   **ORM**: SQLModel (with known constraints - see Technical Constraints below).

---

## 9. Technical Constraints & Best Practices

### 9.1 SQLModel ORM Patterns
**Constraint**: SQLModel's `Relationship()` cannot parse `list["Model"]` type annotations.

**Solution**: Use unidirectional relationships:
```python
# ✅ CORRECT - Unidirectional from child to parent
class Position(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id")
    user: "User" = Relationship()

class User(SQLModel, table=True):
    # No positions relationship declared
    pass

# Access via explicit query:
positions = session.exec(select(Position).where(Position.user_id == user.id)).all()
```

**Avoid**: Bidirectional relationships with collections cause runtime errors:
```python
# ❌ INCORRECT - Causes InvalidRequestError
class User(SQLModel, table=True):
    positions: list["Position"] = Relationship(back_populates="user")
```

### 9.2 Async Testing with Mocks
**Constraint**: `AsyncMock(return_value=X)` wraps return values in coroutines, incompatible with `async with` statements.

**Solution**: Use `MagicMock` for callables returning context managers:
```python
# ✅ CORRECT - MagicMock returns context manager directly
mock_session.post = MagicMock(return_value=mock_response)
mock_response.__aenter__ = AsyncMock(return_value=mock_response)
mock_response.__aexit__ = AsyncMock(return_value=None)

# ❌ INCORRECT - AsyncMock returns coroutine first
mock_session.post = AsyncMock(return_value=mock_response)
```

### 9.3 Schema-Model Alignment
**Best Practice**: Always verify model field types match migration column definitions.

**Example**: Arrays must use `postgresql.ARRAY()`, not `Column(JSON)`:
```python
from sqlalchemy.dialects import postgresql

# ✅ CORRECT
currencies: list[str] | None = Field(
    default=None, 
    sa_column=Column(postgresql.ARRAY(sa.String()))
)
```

### 9.4 Event Loop Management
**Constraint**: Cannot use `loop.run_until_complete()` from within an already-running async context.

**Solution**: 
- For async tests: Use `await` directly on async methods
- For sync API routes: Create new event loop or use sync wrappers
- Detect context: `asyncio.get_running_loop()` raises `RuntimeError` if no loop
