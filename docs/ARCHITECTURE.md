# Oh My Coins (OMC) - System Architecture

**Version**: 2.1
**Last Updated**: 2026-01-10
**Status**: Consolidated

## 1. Overview
Oh My Coins is a microservices-based platform designed to provide a seamless "Lab-to-Floor" pipeline for algorithmic cryptocurrency trading. It integrates a comprehensive 4-Ledger data collection engine with an autonomous Agentic Data Science capability (The Lab) to enable predictive market intelligence and automated strategy execution.

**Infrastructure Note:** As of Feb 2026, the architecture is deployed on a **dedicated local Linux server (192.168.0.241)** to facilitate rapid iteration and high-frequency data processing without cloud overhead.

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
*   `on_chain_metrics` (Glass)
*   `smart_money_flow` (Glass - Nansen smart wallet tracking)
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
*   **Host**: Local Linux Server (192.168.0.241).
*   **Orchestration**: Docker Compose with Traefik ingress.
*   **CI/CD**: GitHub Actions with self-hosted runners.
*   **Monitoring**: Docker Logs, Status Checks.

### 6.2 Scalability
*   **Horizontal**: Stateless collectors and API workers (replica scaling via Compose).
*   **Vertical**: Server resource upgrades.

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
*   **Infra**: Local Linux Server, Docker Compose, Traefik.
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

##### `fetch_smart_money_flows(session, token, start_date, end_date=None)`
Retrieves smart money wallet tracking data from Nansen API showing what successful wallets are buying and selling.

**Parameters:**
- `session`: SQLModel database session
- `token`: Cryptocurrency symbol (e.g., 'ETH', 'BTC')
- `start_date`: Beginning of time range (datetime)
- `end_date`: End of time range (defaults to now)

**Returns:** List of dictionaries with smart money flow data

**Example Query:**
```python
from datetime import datetime, timedelta

# Get last 7 days of Ethereum smart money flows
flows = await fetch_smart_money_flows(
    session, 
    "ETH", 
    start_date=datetime.now() - timedelta(days=7)
)

# Result structure:
# [
#   {
#     "token": "ETH",
#     "net_flow_usd": 2500000.75,
#     "buying_wallet_count": 15,
#     "selling_wallet_count": 3,
#     "buying_wallets": ["0x1111...", "0x2222..."],
#     "selling_wallets": ["0x3333..."],
#     "collected_at": "2026-01-20T10:00:00+00:00"
#   },
#   ...
# ]
```

**Database Model:**
The `smart_money_flow` table stores Nansen smart wallet tracking data:
- `token`: Cryptocurrency symbol (indexed)
- `net_flow_usd`: Net smart money flow in USD (positive = buying, negative = selling)
- `buying_wallet_count`: Number of smart wallets buying
- `selling_wallet_count`: Number of smart wallets selling
- `buying_wallets`: Array of top smart wallet addresses buying
- `selling_wallets`: Array of top smart wallet addresses selling
- `collected_at`: UTC timestamp when data was collected (indexed)

**Use Cases:**
- Identify when smart money is accumulating or distributing specific tokens
- Track wallet addresses of successful traders
- Detect early trends before they become mainstream
- Generate trading signals based on smart money movements

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

---

## 11. Bring Your Own Model (BYOM) Architecture

### 11.1 Overview

The BYOM (Bring Your Own Model) feature enables users to configure custom LLM providers and models for agent execution, replacing the system-wide default LLM configuration with user-specific credentials.

**Design Goals:**
1. **User Autonomy**: Each user controls their AI provider, model, and API keys
2. **Multi-Provider Support**: OpenAI, Google Gemini, Anthropic Claude, and extensible to future providers
3. **Security First**: AES-256 encryption for API keys with audit logging
4. **Backward Compatible**: Existing users continue using system defaults until they configure BYOM
5. **Session-Specific**: LLM instances are created per agent session, not globally

**Implementation Phases:**
- **Sprint 2.8**: Database schema, encryption, OpenAI + Google Gemini support
- **Sprint 2.9**: Agent orchestrator refactoring, Anthropic Claude support
- **Sprint 2.10**: Frontend UI, session creation with model selection
- **Sprint 2.11**: Production hardening, monitoring, key rotation

---

### 11.2 Data Model

#### UserLLMCredentials Table

New table to store user-specific LLM provider credentials:

```python
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum
import enum
import uuid
from datetime import datetime

class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"  # Future

class UserLLMCredentials(SQLModel, table=True):
    """Stores encrypted API keys for user-specific LLM providers"""
    __tablename__ = "user_llm_credentials"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    
    # Provider configuration
    provider: LLMProvider = Field(sa_column=Column(Enum(LLMProvider)))
    model_name: str = Field(max_length=100)  # e.g., "gpt-4", "gemini-1.5-pro"
    
    # Encrypted credentials
    encrypted_api_key: str = Field(max_length=512)  # AES-256 encrypted
    encryption_key_id: str = Field(max_length=50)  # References encryption key version
    
    # Metadata
    is_default: bool = Field(default=False)  # User's preferred model
    is_active: bool = Field(default=True)  # Soft delete support
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = Field(default=None)
    
    # Unidirectional relationship (see Section 9.1)
    user: "User" = Relationship(back_populates="llm_credentials")

    class Config:
        arbitrary_types_allowed = True


# Extend User model
class User(SQLModel, table=True):
    # ... existing fields ...
    
    # No bidirectional collection (see Section 9.1)
    # Access via: session.exec(select(UserLLMCredentials).where(...)).all()
```

#### AgentSession Extension

Extend existing `AgentSession` to track which LLM was used:

```python
class AgentSession(SQLModel, table=True):
    # ... existing fields ...
    
    # New fields for BYOM
    llm_credentials_id: uuid.UUID | None = Field(
        foreign_key="user_llm_credentials.id", 
        nullable=True  # Nullable for backward compatibility
    )
    llm_provider: str | None = Field(max_length=50)  # "openai", "google", etc.
    llm_model_name: str | None = Field(max_length=100)  # "gpt-4", "gemini-1.5-pro"
    
    # Unidirectional relationship
    llm_credentials: "UserLLMCredentials" | None = Relationship()
```

**Migration Strategy:**
- Existing sessions have `llm_credentials_id=None` (uses system default)
- New sessions populate these fields based on user configuration

---

### 11.3 Encryption Architecture

**Reuse Existing Pattern:**
The system already encrypts CoinSpot API credentials using `EncryptionService` in `backend/app/services/encryption_service.py`. BYOM extends this pattern for LLM API keys.

#### EncryptionService Extension

```python
# backend/app/services/encryption_service.py

from cryptography.fernet import Fernet
import base64
import os

class EncryptionService:
    """Handles AES-256 encryption for sensitive credentials"""
    
    def __init__(self):
        # Load encryption key from environment (same as CoinSpot credentials)
        self._key = os.getenv("ENCRYPTION_KEY")
        if not self._key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        self._cipher = Fernet(self._key)
    
    def encrypt_api_key(self, plain_key: str) -> tuple[str, str]:
        """
        Encrypt LLM API key using AES-256.
        
        Returns:
            (encrypted_key, encryption_key_id) tuple
        """
        encrypted = self._cipher.encrypt(plain_key.encode())
        encrypted_b64 = base64.b64encode(encrypted).decode()
        key_id = self._get_key_version()  # e.g., "v1-2026-01"
        return encrypted_b64, key_id
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt LLM API key"""
        encrypted_bytes = base64.b64decode(encrypted_key)
        decrypted = self._cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def _get_key_version(self) -> str:
        """Return current encryption key version for audit trail"""
        return os.getenv("ENCRYPTION_KEY_VERSION", "v1-default")
```

**Security Properties:**
- **Algorithm**: AES-256 via Fernet (symmetric encryption)
- **Key Storage**: Environment variable (AWS Secrets Manager in production)
- **Key Rotation**: Supported via `encryption_key_id` tracking
- **Audit Trail**: All decrypt operations logged with session ID

**Key Rotation Process** (Sprint 2.11):
1. Generate new `ENCRYPTION_KEY_V2`
2. Decrypt existing credentials with old key
3. Re-encrypt with new key
4. Update `encryption_key_id` to "v2-2026-02"
5. Deprecate old key after grace period

---

### 11.4 LLM Factory Pattern

**Problem**: Agent code currently uses hardcoded `ChatOpenAI` instances from LangChain.

**Solution**: LLMFactory creates provider-specific LLM instances based on user configuration.

#### Factory Implementation

```python
# backend/app/services/agent/llm_factory.py

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from typing import Protocol
import uuid

class LLMProvider(Protocol):
    """Protocol for LLM providers (duck typing)"""
    def invoke(self, messages: list) -> dict: ...
    async def ainvoke(self, messages: list) -> dict: ...


class LLMFactory:
    """Creates LLM instances based on user configuration"""
    
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service
    
    async def create_llm(
        self, 
        session: Session, 
        user_id: uuid.UUID
    ) -> LLMProvider:
        """
        Create LLM instance for user.
        Falls back to system default if user has no BYOM config.
        """
        # Check for user's default LLM credentials
        credentials = session.exec(
            select(UserLLMCredentials)
            .where(UserLLMCredentials.user_id == user_id)
            .where(UserLLMCredentials.is_default == True)
            .where(UserLLMCredentials.is_active == True)
        ).first()
        
        if not credentials:
            # Fallback to system default (backward compatibility)
            return self._create_system_default()
        
        # Decrypt API key
        api_key = self.encryption_service.decrypt_api_key(
            credentials.encrypted_api_key
        )
        
        # Update last_used_at
        credentials.last_used_at = datetime.utcnow()
        session.add(credentials)
        session.commit()
        
        # Provider-specific instantiation
        if credentials.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=credentials.model_name,
                openai_api_key=api_key,
                temperature=0.7
            )
        
        elif credentials.provider == LLMProvider.GOOGLE:
            return ChatGoogleGenerativeAI(
                model=credentials.model_name,
                google_api_key=api_key,
                temperature=0.7
            )
        
        elif credentials.provider == LLMProvider.ANTHROPIC:
            return ChatAnthropic(
                model=credentials.model_name,
                anthropic_api_key=api_key,
                temperature=0.7
            )
        
        else:
            raise ValueError(f"Unsupported provider: {credentials.provider}")
    
    def _create_system_default(self) -> LLMProvider:
        """System default (uses OPENAI_API_KEY from environment)"""
        return ChatOpenAI(
            model="gpt-4",
            temperature=0.7
        )
```

**Usage in Agent Orchestrator:**

```python
# backend/app/services/agent/agent_orchestrator.py

class AgentOrchestrator:
    def __init__(
        self, 
        session: Session, 
        llm_factory: LLMFactory  # Inject factory
    ):
        self.session = session
        self.llm_factory = llm_factory
    
    async def start_session(
        self, 
        user_id: uuid.UUID, 
        goal: str
    ) -> AgentSession:
        """Create agent session with user's LLM"""
        
        # Create user-specific LLM instance
        llm = await self.llm_factory.create_llm(self.session, user_id)
        
        # Store LLM metadata in session
        session_record = AgentSession(
            user_id=user_id,
            goal=goal,
            llm_provider=llm.model_provider if hasattr(llm, 'model_provider') else "openai",
            llm_model_name=llm.model_name if hasattr(llm, 'model_name') else "gpt-4",
            status="active"
        )
        self.session.add(session_record)
        self.session.commit()
        
        # Pass LLM to agents via dependency injection
        planner = PlannerAgent(llm=llm, session_id=session_record.id)
        analyst = DataAnalystAgent(llm=llm, session_id=session_record.id)
        
        return session_record
```

---

### 11.5 API Endpoints

#### User Credentials Management

**POST /api/v1/users/me/llm-credentials**
Create new LLM provider credentials for authenticated user.

```json
{
  "provider": "google",
  "model_name": "gemini-1.5-pro",
  "api_key": "AIzaSy...",  // Plain text (encrypted server-side)
  "is_default": true
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "google",
  "model_name": "gemini-1.5-pro",
  "is_default": true,
  "created_at": "2026-01-10T10:00:00Z"
  // API key NOT returned
}
```

**GET /api/v1/users/me/llm-credentials**
List user's configured LLM providers (API keys masked).

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "google",
    "model_name": "gemini-1.5-pro",
    "is_default": true,
    "api_key_preview": "AIza...440000",  // First 4 + last 6 chars
    "last_used_at": "2026-01-10T09:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "provider": "openai",
    "model_name": "gpt-4",
    "is_default": false,
    "api_key_preview": "sk-...440001",
    "last_used_at": null
  }
]
```

**DELETE /api/v1/users/me/llm-credentials/{credential_id}**
Soft delete LLM credentials (sets `is_active=False`).

**PUT /api/v1/users/me/llm-credentials/{credential_id}/default**
Set specified credentials as user's default model.

#### API Key Validation

**POST /api/v1/users/me/llm-credentials/validate**
Test API key validity before saving.

```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-...",
  "model_name": "claude-3-opus-20240229"
}
```

**Response:**
```json
{
  "valid": true,
  "model_info": {
    "max_tokens": 200000,
    "supports_function_calling": true,
    "supports_streaming": true
  }
}
```

If invalid:
```json
{
  "valid": false,
  "error": "Invalid API key or insufficient permissions"
}
```

---

### 11.6 Frontend Integration

#### New UI Components

**Settings Page: LLM Provider Configuration**

Location: `/settings/llm` (new tab in user settings)

**Features:**
1. **Provider Selection Dropdown**:
   - OpenAI (GPT-4, GPT-4 Turbo)
   - Google (Gemini 1.5 Pro, Gemini 1.5 Flash)
   - Anthropic (Claude 3 Opus, Claude 3 Sonnet)

2. **API Key Input**:
   - Secure text field (masked input)
   - "Test Connection" button (calls validation endpoint)
   - Success/error feedback

3. **Model Selection**:
   - Provider-specific model dropdown
   - Model descriptions (context window, capabilities)

4. **Credentials List**:
   - Table showing configured providers
   - "Set as Default" action
   - "Delete" action (with confirmation modal)
   - Last used timestamp

**Session Creation Modal Extension**

Existing modal at `/lab` for starting agent sessions:

**Before:**
```
┌─ Start Agent Session ─────────────────┐
│ Goal: [text input]                    │
│                                        │
│ [Cancel] [Start Session]              │
└────────────────────────────────────────┘
```

**After (Sprint 2.10):**
```
┌─ Start Agent Session ─────────────────┐
│ Goal: [text input]                    │
│                                        │
│ LLM Model: [dropdown]                 │
│   - My Default (GPT-4) ✓              │
│   - Gemini 1.5 Pro (Google)           │
│   - Claude 3 Opus (Anthropic)         │
│   - System Default                    │
│                                        │
│ [Cancel] [Start Session]              │
└────────────────────────────────────────┘
```

---

### 11.7 Prompt Engineering Considerations

Different LLM providers have different prompt optimization strategies:

#### OpenAI (GPT-4)
```python
# Works well with structured prompts
system_prompt = """You are a financial data analyst agent.
Your goal is to analyze cryptocurrency market data.

Tools available:
- fetch_price_data: Retrieve historical prices
- fetch_sentiment_data: Get sentiment analysis
"""
```

#### Google Gemini
```python
# Prefers conversational style with examples
system_prompt = """You're helping a user analyze crypto markets.

Example task: "Show me Bitcoin's price trend"
You would: Call fetch_price_data("BTC", last_7_days)

Now, help the user with their request.
"""
```

#### Anthropic Claude
```python
# Benefits from XML-style structured prompts
system_prompt = """
<role>Financial Data Analyst Agent</role>

<capabilities>
  <tool name="fetch_price_data">Retrieve historical prices</tool>
  <tool name="fetch_sentiment_data">Get sentiment analysis</tool>
</capabilities>

<task>Analyze cryptocurrency market data for the user</task>
"""
```

**Implementation Strategy:**
- **Sprint 2.9**: Create provider-specific prompt templates in `backend/app/services/agent/prompts/`
- **Sprint 2.10**: A/B test prompt variations, track success metrics
- **Sprint 2.11**: Optimize prompts based on production usage patterns

---

### 11.8 Security & Compliance

#### API Key Handling Rules

1. **Never Log Plain Keys**:
   ```python
   # ❌ INCORRECT
   logger.info(f"Using API key: {api_key}")
   
   # ✅ CORRECT
   logger.info(f"Using API key: {mask_api_key(api_key)}")  # "AIza...440000"
   ```

2. **Audit Logging**:
   ```python
   # Log every key retrieval
   audit_log.info({
       "event": "llm_key_retrieved",
       "user_id": user_id,
       "provider": credentials.provider,
       "session_id": session_id,
       "timestamp": datetime.utcnow()
   })
   ```

3. **Rate Limiting**:
   - Max 10 key validations per user per hour (prevent brute force)
   - Max 100 LLM API calls per session (cost control)

4. **Access Control**:
   - Users can only access their own credentials
   - Admins cannot view user API keys (even encrypted)

#### Cost Management

**Problem**: Users with BYOM pay for their own LLM usage, but need cost visibility.

**Solution** (Sprint 2.11):
- Track token usage per session in `AgentSession.token_usage_count`
- Display estimated cost in UI: `tokens × provider_rate`
- Alert users if session exceeds $10 in API costs
- Allow setting per-session cost limits

#### Compliance Considerations

- **GDPR**: API keys are personal data, support right to deletion
- **SOC 2**: Encryption at rest (AES-256), access logging, key rotation
- **PCI**: Not applicable (no payment card data)

---

### 11.9 Testing Strategy

#### Unit Tests

**Encryption Service Tests** (`tests/services/test_encryption_service.py`):
```python
def test_encrypt_decrypt_api_key():
    service = EncryptionService()
    plain_key = "sk-ant-api03-1234567890"
    
    encrypted, key_id = service.encrypt_api_key(plain_key)
    decrypted = service.decrypt_api_key(encrypted)
    
    assert decrypted == plain_key
    assert key_id.startswith("v1-")
```

**LLM Factory Tests** (`tests/services/agent/test_llm_factory.py`):
```python
async def test_create_llm_with_user_credentials(session, test_user):
    # Create user credentials
    credentials = UserLLMCredentials(
        user_id=test_user.id,
        provider=LLMProvider.GOOGLE,
        model_name="gemini-1.5-pro",
        encrypted_api_key="...",
        is_default=True
    )
    session.add(credentials)
    session.commit()
    
    factory = LLMFactory(encryption_service)
    llm = await factory.create_llm(session, test_user.id)
    
    assert isinstance(llm, ChatGoogleGenerativeAI)
    assert llm.model_name == "gemini-1.5-pro"
```

#### Integration Tests

**Full Session with BYOM** (`tests/integration/test_byom_agent_session.py`):
```python
async def test_agent_session_with_custom_llm(client, test_user):
    # 1. Configure user's LLM credentials
    response = await client.post(
        "/api/v1/users/me/llm-credentials",
        json={
            "provider": "anthropic",
            "model_name": "claude-3-opus-20240229",
            "api_key": os.getenv("TEST_ANTHROPIC_KEY"),
            "is_default": True
        }
    )
    assert response.status_code == 201
    
    # 2. Start agent session (should use Claude)
    response = await client.post(
        "/api/v1/agent/sessions",
        json={"goal": "Analyze Bitcoin price trend"}
    )
    assert response.status_code == 201
    session_id = response.json()["id"]
    
    # 3. Verify session used correct LLM
    response = await client.get(f"/api/v1/agent/sessions/{session_id}")
    assert response.json()["llm_provider"] == "anthropic"
    assert response.json()["llm_model_name"] == "claude-3-opus-20240229"
```

#### E2E Tests (Playwright)

**LLM Configuration Flow** (`frontend/tests/llm-settings.spec.ts`):
```typescript
test('configure Google Gemini credentials', async ({ page }) => {
  await page.goto('/settings/llm');
  
  // Select provider
  await page.selectOption('#provider-select', 'google');
  
  // Enter API key
  await page.fill('#api-key-input', process.env.TEST_GOOGLE_API_KEY);
  
  // Select model
  await page.selectOption('#model-select', 'gemini-1.5-pro');
  
  // Test connection
  await page.click('button:has-text("Test Connection")');
  await expect(page.locator('.success-message')).toBeVisible();
  
  // Save
  await page.click('button:has-text("Save Credentials")');
  await expect(page.locator('.credentials-list')).toContainText('Google');
});
```

---

### 11.10 Monitoring & Observability

#### Metrics to Track

**Sprint 2.11 Implementation:**

1. **Usage Metrics**:
   - `byom_sessions_created{provider="openai|google|anthropic"}` (counter)
   - `byom_api_calls{provider, model}` (counter)
   - `byom_token_usage{provider, model}` (histogram)
   - `byom_session_duration{provider, model}` (histogram)

2. **Error Metrics**:
   - `byom_key_validation_failures{provider}` (counter)
   - `byom_api_errors{provider, error_type}` (counter)
   - `byom_rate_limit_hits{user_id, provider}` (counter)

3. **Security Metrics**:
   - `byom_key_retrievals{user_id}` (counter, for anomaly detection)
   - `byom_encryption_errors` (counter)
   - `byom_unauthorized_access_attempts` (counter)

#### Dashboards

**Grafana Dashboard: "BYOM Health"**
- Panel 1: Sessions by provider (pie chart)
- Panel 2: Average session cost by provider (bar chart)
- Panel 3: API error rate by provider (time series)
- Panel 4: Token usage trends (time series)
- Panel 5: Top users by API usage (table)

**Alerts:**
- High error rate (>5%) for any provider → Page ops team
- User exceeding cost limits → Email user
- Unusual key retrieval pattern → Security review

---

### 11.11 Migration & Rollout Plan

#### Phase 1: Sprint 2.8 (Foundation)
**Goal**: Database schema, encryption, basic multi-provider support

**Deliverables:**
- Alembic migration for `user_llm_credentials` table
- `EncryptionService` extension for LLM keys
- `LLMFactory` with OpenAI + Google support
- Backend API endpoints (CRUD for credentials)
- Unit tests for encryption and factory

**Validation:**
- 100% test coverage for new components
- Manual testing with test API keys
- No impact on existing users (backward compatible)

**Risks:**
- Encryption key management (mitigated by reusing CoinSpot pattern)
- Google Gemini API differences (mitigated by LangChain abstraction)

#### Phase 2: Sprint 2.9 (Agent Integration)
**Goal**: Refactor agents to use dependency-injected LLMs

**Deliverables:**
- Update `AgentOrchestrator.start_session` to use `LLMFactory`
- Refactor `BaseAgent` to accept `llm` parameter
- Add Anthropic Claude support
- Provider-specific prompt templates
- Integration tests with all 3 providers

**Validation:**
- Run full agent test suite with each provider
- Compare agent performance across providers
- Verify session metadata correctly tracks LLM usage

**Risks:**
- Function calling compatibility (Gemini + Claude may differ from OpenAI)
- Prompt optimization required per provider

#### Phase 3: Sprint 2.10 (User Experience)
**Goal**: Frontend UI for LLM configuration

**Deliverables:**
- `/settings/llm` page (React + TanStack Router)
- API key validation UI with real-time feedback
- Session creation modal with model selection
- Playwright E2E tests for full flow

**Validation:**
- User acceptance testing with Beta users
- Measure time to configure credentials (<2 minutes target)
- Track adoption rate (% of users configuring BYOM)

**Risks:**
- UX confusion (mitigated by clear help text and examples)
- Security concerns about entering API keys (mitigated by HTTPS + education)

#### Phase 4: Sprint 2.11 (Production Hardening)
**Goal**: Cost management, monitoring, security hardening

**Deliverables:**
- Cost tracking and alerts
- Rate limiting enforcement
- Key rotation automation
- Grafana dashboards
- Security audit logging
- Documentation updates

**Validation:**
- Penetration testing of API key handling
- Load testing with 100 concurrent BYOM sessions
- Verify cost alerts trigger correctly
- Monitor for 1 week post-launch

**Rollout Strategy:**
1. Week 1: Beta users only (10 users)
2. Week 2: All users, feature flag enabled
3. Week 3: Monitor adoption + errors
4. Week 4: Full general availability

---

### 11.12 Future Enhancements (Post-Sprint 2.11)

**Azure OpenAI Support:**
- Requires endpoint URL + deployment name configuration
- Useful for enterprise customers with Azure subscriptions

**Prompt Caching:**
- Anthropic Claude supports prompt caching for repeated system prompts
- Could reduce costs by 90% for frequent users

**Model Fine-Tuning Integration:**
- Allow users to configure fine-tuned model IDs
- Useful for specialized trading strategies

**Multi-Model Ensembles:**
- Run same query through multiple models, aggregate results
- Useful for high-stakes decisions (e.g., large trades)

**Cost Optimization Recommendations:**
- Suggest switching to cheaper models based on usage patterns
- "Your queries could run on Gemini 1.5 Flash for 80% less cost"

## 8. DevOps & Monitoring (Governance)

### 8.1 Centralized Log Hub
To facilitate observability across multiple development tracks (Git Worktrees), the architecture mandates a **Centralized Log Hub**.
*   **Host Path**: `~/omc/logs/hub` (Outside Git).
*   **Container Path**: `/var/log/omc-agents` (Mounted Read-Write).
*   **Mechanism**: All agents and containers write structured logs to this volume.
*   **Tooling**: `scripts/governance/watchdog.py` and `agent-monitor.sh` aggregate these logs for the Architect.
