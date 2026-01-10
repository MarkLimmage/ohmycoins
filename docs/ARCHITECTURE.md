# Oh My Coins (OMC) - System Architecture

**Version**: 2.1
**Last Updated**: 2026-01-10
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

---

## 10. Agent-Data Interface

### 10.1 Overview
The Agent-Data Interface defines how the Agentic AI system queries the 4-Ledger data collection framework. All agent workflows access market data, sentiment, events, and trading history through a standardized set of data retrieval tools located in `backend/app/services/agent/tools/data_retrieval_tools.py`.

**Design Principles:**
- **Read-Only Access**: Agents query data but never modify ledger tables
- **Performance Target**: All queries complete in <1 second
- **Graceful Degradation**: Missing data returns empty results, not errors
- **SQLModel Compliance**: Uses unidirectional relationship patterns (see Section 9.1)

---

### 10.2 Glass Ledger: Market & On-Chain Data

The Glass Ledger provides objective, quantifiable market data including prices, volumes, and blockchain metrics.

#### Available Tools

##### `fetch_price_data(session, coin_type, start_date, end_date=None)`
Retrieves historical 5-minute price data for technical analysis and model training.

**Parameters:**
- `session`: SQLModel database session
- `coin_type`: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
- `start_date`: Beginning of time range (datetime)
- `end_date`: End of time range (defaults to now)

**Returns:** List of dictionaries with `timestamp`, `coin_type`, `bid`, `ask`, `last`

**Example Query:**
```python
from datetime import datetime, timedelta

# Get last 24 hours of Bitcoin prices
now = datetime.now()
start = now - timedelta(days=1)
prices = await fetch_price_data(session, "BTC", start, now)

# Result structure:
# [
#   {
#     "timestamp": "2026-01-09T14:30:00+00:00",
#     "coin_type": "BTC",
#     "bid": 50000.0,
#     "ask": 50100.0,
#     "last": 50050.0
#   },
#   ...
# ]
```

##### `fetch_on_chain_metrics(session, asset, start_date, end_date=None, metric_names=None)`
Retrieves blockchain-level metrics like active addresses, transaction volume, hash rate.

**Parameters:**
- `asset`: Cryptocurrency symbol
- `metric_names`: Optional list to filter specific metrics (e.g., `['active_addresses', 'hash_rate']`)

**Returns:** List of dictionaries with `asset`, `metric_name`, `metric_value`, `source`, `collected_at`

**Example Query:**
```python
# Get recent on-chain activity for Ethereum
metrics = await fetch_on_chain_metrics(
    session, 
    "ETH", 
    start_date=datetime.now() - timedelta(days=7),
    metric_names=["active_addresses", "transaction_count"]
)
```

##### `get_available_coins(session)`
Returns list of all cryptocurrencies with price data in the system.

**Example Query:**
```python
coins = await get_available_coins(session)
# Returns: ["BTC", "ETH", "ADA", ...]
```

##### `get_data_statistics(session, coin_type=None)`
Provides coverage statistics for data quality monitoring.

**Returns:** Dictionary with counts and date ranges for all ledgers

---

### 10.3 Human Ledger: Sentiment & Narrative

The Human Ledger captures subjective market sentiment from news outlets and social media platforms.

#### Available Tools

##### `fetch_sentiment_data(session, start_date, end_date=None, platform=None, currencies=None)`
Retrieves news articles and social media posts with sentiment analysis scores.

**Parameters:**
- `platform`: Filter social data by platform ('reddit', 'twitter', etc.)
- `currencies`: Filter to specific cryptocurrencies (e.g., `['BTC', 'ETH']`)

**Returns:** Dictionary with `news_sentiment` and `social_sentiment` arrays

**Example Query:**
```python
# Get sentiment for Bitcoin from Reddit over last week
sentiment = await fetch_sentiment_data(
    session,
    start_date=datetime.now() - timedelta(days=7),
    platform="reddit",
    currencies=["BTC"]
)

# Result structure:
# {
#   "news_sentiment": [
#     {
#       "title": "Bitcoin Reaches New High",
#       "source": "CoinDesk",
#       "published_at": "2026-01-09T10:00:00+00:00",
#       "sentiment": "positive",
#       "sentiment_score": 0.85,
#       "currencies": ["BTC"]
#     },
#     ...
#   ],
#   "social_sentiment": [
#     {
#       "platform": "reddit",
#       "content": "BTC looking bullish!",
#       "score": 145,
#       "sentiment": "positive",
#       "currencies": ["BTC"],
#       "posted_at": "2026-01-09T12:30:00+00:00"
#     },
#     ...
#   ]
# }
```

**Use Cases:**
- Sentiment-based trading signals
- Narrative detection (bull/bear market transitions)
- News impact analysis

---

### 10.4 Catalyst Ledger: Events & Announcements

The Catalyst Ledger tracks high-impact events like regulatory filings, exchange listings, and protocol upgrades.

#### Available Tools

##### `fetch_catalyst_events(session, start_date, end_date=None, event_types=None, currencies=None)`
Retrieves market-moving events with impact scores for filtering.

**Parameters:**
- `event_types`: Filter by type (e.g., `['listing', 'sec_filing', 'regulation']`)
- `currencies`: Filter to specific cryptocurrencies

**Returns:** List of dictionaries with `event_type`, `title`, `description`, `impact_score`, `detected_at`

**Example Query:**
```python
# Get high-impact SEC filings for all coins
events = await fetch_catalyst_events(
    session,
    start_date=datetime.now() - timedelta(days=30),
    event_types=["sec_filing"]
)

# Filter high-impact events (score > 5)
critical_events = [e for e in events if e["impact_score"] > 5]
```

**Performance Note:** Catalyst events have a 30-second detection latency target (NFR-P-001). Agents querying recent events should expect near-real-time data.

---

### 10.5 Exchange Ledger: Trading Activity

The Exchange Ledger provides user-specific trading data including order history and current positions.

#### Available Tools

##### `fetch_order_history(session, user_id, coin_type=None, status=None, start_date=None, end_date=None)`
Retrieves historical orders for portfolio analysis and performance tracking.

**Parameters:**
- `user_id`: User UUID (required for security isolation)
- `coin_type`: Filter by cryptocurrency
- `status`: Filter by order status ('pending', 'filled', 'cancelled', etc.)
- Date range defaults to last 30 days

**Returns:** List of dictionaries with order details including `side`, `quantity`, `price`, `filled_at`

**Example Query:**
```python
# Get all filled Bitcoin orders for a user
orders = await fetch_order_history(
    session,
    user_id=user.id,
    coin_type="BTC",
    status="filled"
)

# Calculate total BTC purchased
total_bought = sum(
    float(o["quantity"]) 
    for o in orders 
    if o["side"] == "buy"
)
```

##### `fetch_user_positions(session, user_id, coin_type=None)`
Retrieves current holdings for P&L calculations and risk management.

**Returns:** List of dictionaries with `coin_type`, `quantity`, `average_price`, `total_cost`

**Example Query:**
```python
# Get all current positions
positions = await fetch_user_positions(session, user_id=user.id)

# Calculate portfolio value (requires current prices from Glass Ledger)
for position in positions:
    current_prices = await fetch_price_data(
        session, 
        position["coin_type"], 
        datetime.now() - timedelta(minutes=5),
        datetime.now()
    )
    if current_prices:
        current_value = position["quantity"] * current_prices[-1]["last"]
        unrealized_pnl = current_value - position["total_cost"]
        print(f"{position['coin_type']}: ${unrealized_pnl:,.2f} P&L")
```

---

### 10.6 Cross-Ledger Queries

Agents often combine data from multiple ledgers to generate insights.

#### Example: Sentiment-Driven Price Analysis

```python
from datetime import datetime, timedelta

async def analyze_sentiment_impact(session, coin_type, user_id):
    """
    Correlate sentiment spikes with price movements.
    Demonstrates cross-ledger data integration.
    """
    now = datetime.now()
    lookback = timedelta(days=7)
    
    # Glass Ledger: Get price history
    prices = await fetch_price_data(session, coin_type, now - lookback, now)
    
    # Human Ledger: Get sentiment data
    sentiment = await fetch_sentiment_data(
        session, 
        now - lookback, 
        now, 
        currencies=[coin_type]
    )
    
    # Catalyst Ledger: Check for major events
    events = await fetch_catalyst_events(
        session, 
        now - lookback, 
        now, 
        currencies=[coin_type]
    )
    
    # Exchange Ledger: Get user's trading history
    orders = await fetch_order_history(
        session, 
        user_id, 
        coin_type=coin_type
    )
    
    return {
        "price_trend": "bullish" if prices[-1]["last"] > prices[0]["last"] else "bearish",
        "sentiment_score": sum(s["sentiment_score"] for s in sentiment["news_sentiment"]) / len(sentiment["news_sentiment"]),
        "major_events": [e for e in events if e["impact_score"] > 5],
        "user_position": len([o for o in orders if o["side"] == "buy"]) > len([o for o in orders if o["side"] == "sell"])
    }
```

#### Example: Multi-Asset Portfolio Risk

```python
async def calculate_portfolio_risk(session, user_id):
    """
    Calculate portfolio-level risk metrics using multiple ledgers.
    """
    # Exchange Ledger: Get all positions
    positions = await fetch_user_positions(session, user_id)
    
    portfolio_risk = []
    for position in positions:
        coin = position["coin_type"]
        
        # Glass Ledger: Get price volatility
        prices = await fetch_price_data(
            session, 
            coin, 
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        volatility = calculate_std_dev([p["last"] for p in prices])
        
        # Catalyst Ledger: Check for upcoming events
        upcoming_events = await fetch_catalyst_events(
            session,
            datetime.now(),
            datetime.now() + timedelta(days=7),
            currencies=[coin]
        )
        
        portfolio_risk.append({
            "coin": coin,
            "exposure": position["total_cost"],
            "volatility": volatility,
            "upcoming_catalysts": len(upcoming_events)
        })
    
    return portfolio_risk
```

---

### 10.7 Performance Guidelines

**Query Optimization:**
1. **Batch Queries**: Fetch data for multiple coins in parallel when possible
2. **Time Windows**: Limit queries to necessary timeframes (avoid full history pulls)
3. **Pagination**: Use date range filtering instead of retrieving all records
4. **Caching**: Frequently accessed data (e.g., latest prices) should be cached in Redis

**Performance Targets:**
- Single ledger query: <500ms
- Cross-ledger analysis: <1 second
- Complex multi-asset queries: <2 seconds

**Test Validation:**
All query performance is validated in `tests/services/agent/integration/test_data_integration.py::TestPerformanceAndPatterns::test_query_performance_under_1_second`

---

### 10.8 Security & Access Control

**Data Isolation:**
- Exchange Ledger queries require `user_id` parameter
- Agents can only access data for the authenticated user
- Cross-user data access is prevented at the query level

**Audit Trail:**
- All agent data queries are logged with session ID
- Query patterns are monitored for anomalies
- Performance metrics tracked per ledger and coin type

**Error Handling:**
- Missing data returns empty list/dict (never raises exception)
- Invalid coin types return empty results
- Date range errors fall back to safe defaults

---

### 10.9 Integration Testing

All agent-data integration patterns are validated in:
- `tests/services/agent/integration/test_data_integration.py`

**Test Coverage (22 tests):**
- Glass Ledger: 5 tests (price data, metrics, statistics, coin list)
- Human Ledger: 3 tests (sentiment by currency, platform filtering)
- Catalyst Ledger: 3 tests (events by type, currency, impact score)
- Exchange Ledger: 5 tests (orders, positions, filtering, user isolation)
- Performance: 4 tests (query speed, error handling, pattern compliance)
- Cross-ledger: 2 tests (multi-ledger workflows)

**Running Tests:**
```bash
cd backend
pytest tests/services/agent/integration/test_data_integration.py -v
```

---

### 10.10 Future Enhancements

**Planned for Sprint 2.7+:**
- Streaming data endpoints for real-time price updates
- GraphQL interface for complex multi-ledger queries
- Query result caching with Redis for frequently accessed data
- Materialized views for common aggregations (daily summaries, volatility metrics)
