# Oh My Coins (OMC!) - System Architecture

## Overview
Oh My Coins is a microservices-based platform built on the FastAPI full-stack template, designed to provide a seamless "Lab-to-Floor" pipeline for algorithmic cryptocurrency trading.

---

## Architecture Principles
1. **Microservices**: Each service has a single, well-defined responsibility
2. **API-First**: All services communicate via RESTful APIs
3. **Security**: End-to-end encryption, secure credential management
4. **Scalability**: Horizontal scaling, containerized deployment
5. **Observability**: Comprehensive logging, monitoring, and alerting

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          API Gateway                             │
│                     (FastAPI + Authentication)                   │
└──────────────┬─────────────────────────────────┬────────────────┘
               │                                 │
       ┌───────▼────────┐                ┌──────▼──────┐
       │   User Service │                │  Lab Service│
       │   (Auth/Users) │                │  (Algo Dev) │
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

---

## Microservices Definition

### 1. API Gateway Service
**Responsibility**: Central entry point, authentication, request routing

**Key Functions**:
- Authentication and authorization (JWT tokens)
- Request routing to appropriate services
- Rate limiting
- CORS management
- API documentation (Swagger/OpenAPI)

**Technology**: FastAPI (from template)

**Endpoints**:
- `/api/v1/auth/*` - Authentication endpoints
- `/api/v1/users/*` - User management
- `/api/v1/lab/*` - Algorithm development (proxied to Lab Service)
- `/api/v1/floor/*` - Live trading (proxied to Trading Service)
- `/api/v1/data/*` - Historical data queries

**Dependencies**:
- PostgreSQL (user sessions, auth tokens)
- All other microservices (routing)

---

### 2. User Service
**Responsibility**: User account management and Coinspot credential storage

**Key Functions**:
- User CRUD operations (extends template's user model)
- Profile management
- Secure storage of Coinspot API credentials
  - Encryption at rest (AES-256)
  - Decryption only when needed for trading
- Credential validation with Coinspot API

**Technology**: FastAPI + SQLAlchemy

**Endpoints**:
- `POST /api/v1/users/register` - New user registration
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update profile
- `POST /api/v1/credentials/coinspot` - Add Coinspot credentials
- `GET /api/v1/credentials/coinspot` - Get credentials (masked)
- `PUT /api/v1/credentials/coinspot` - Update credentials
- `DELETE /api/v1/credentials/coinspot` - Remove credentials
- `POST /api/v1/credentials/coinspot/validate` - Test credentials

**Database Tables**:
- `users` (from template, extended)
- `coinspot_credentials`

**Dependencies**:
- PostgreSQL
- Encryption library (cryptography/Fernet)

---

### 3. Collector Service (Data Pipeline)
**Responsibility**: Ingest cryptocurrency price data from Coinspot public API

**Key Functions**:
- Scheduled data collection (every 5 minutes)
- HTTP GET request to Coinspot public API
- Parse JSON response (prices object with bid, ask, last)
- Store time-series data in PostgreSQL
- Error handling and retry logic
- Data quality validation

**Technology**: FastAPI + APScheduler (or standalone Python script with cron)

**Endpoints** (Internal/Admin only):
- `POST /internal/collector/trigger` - Manual data collection trigger
- `GET /internal/collector/status` - Service health check
- `GET /internal/collector/last-run` - Last successful collection info

**External API**:
- `GET https://www.coinspot.com.au/pubapi/v2/latest` (no auth required)

**Database Tables**:
- `price_data_5min`

**Dependencies**:
- PostgreSQL
- Coinspot Public API

**Cron Schedule**: `*/5 * * * *` (every 5 minutes)

---

### 4. Lab Service (Algorithm Development Platform)
**Responsibility**: Algorithm development, backtesting, and validation

**Key Functions**:
- Algorithm CRUD operations
- Code storage and versioning
- Scikit-learn API integration
- Sandbox execution environment (isolated, resource-limited)
- Backtesting engine
  - Historical data queries
  - Trade simulation
  - Performance metrics calculation (P&L, Sharpe, drawdown)
- Algorithm validation before promotion
- Algorithm packaging for deployment

**Technology**: FastAPI + SQLAlchemy + scikit-learn + pandas

**Endpoints**:
- `POST /api/v1/lab/algorithms` - Create new algorithm
- `GET /api/v1/lab/algorithms` - List user's algorithms
- `GET /api/v1/lab/algorithms/{id}` - Get algorithm details
- `PUT /api/v1/lab/algorithms/{id}` - Update algorithm
- `DELETE /api/v1/lab/algorithms/{id}` - Delete algorithm
- `POST /api/v1/lab/algorithms/{id}/backtest` - Run backtest
- `GET /api/v1/lab/backtests/{id}` - Get backtest results
- `GET /api/v1/lab/algorithms/{id}/backtests` - List algorithm backtests
- `POST /api/v1/lab/algorithms/{id}/promote` - Promote to Floor
- `GET /api/v1/lab/data/historical` - Query historical price data

**Database Tables**:
- `algorithms`
- `algorithm_versions`
- `algorithm_backtest_runs`
- `price_data_5min` (read-only for backtesting)

**Dependencies**:
- PostgreSQL
- Python sandbox (RestrictedPython or similar)
- Collector Service (historical data)

---

### 5. Trading Service (The Floor)
**Responsibility**: Live algorithm execution and trade management

**Key Functions**:
- Load and execute deployed algorithms
- Real-time price monitoring
- Trading signal generation
- Order execution via Coinspot API
  - Buy orders: `POST /my/buy`
  - Sell orders: `POST /my/sell`
- Order status tracking: `GET /my/orders`
- Position management: `GET /my/balances`, `GET /api/ro/my/balances/:cointype`
- P&L calculation (realized and unrealized)
- Risk management (position limits, loss limits)
- Emergency stop functionality

**Technology**: FastAPI + SQLAlchemy + asyncio

**Endpoints**:
- `GET /api/v1/floor/available-algorithms` - List deployable algorithms
- `POST /api/v1/floor/deploy` - Deploy algorithm
- `GET /api/v1/floor/deployments` - List active deployments
- `POST /api/v1/floor/algorithms/{id}/activate` - Activate algorithm
- `POST /api/v1/floor/algorithms/{id}/pause` - Pause algorithm
- `POST /api/v1/floor/algorithms/{id}/deactivate` - Stop and remove
- `PUT /api/v1/floor/algorithms/{id}/parameters` - Update parameters
- `GET /api/v1/floor/algorithms/{id}/status` - Get algorithm status
- `GET /api/v1/floor/algorithms/{id}/performance` - Performance metrics
- `GET /api/v1/floor/algorithms/{id}/trades` - Recent trades
- `GET /api/v1/floor/pnl/summary` - Overall P&L
- `GET /api/v1/floor/pnl/by-algorithm` - P&L by algorithm
- `GET /api/v1/floor/pnl/by-coin` - P&L by coin
- `GET /api/v1/floor/positions` - Current positions
- `POST /api/v1/floor/emergency-stop` - Stop all trading

**External API** (Coinspot Private):
- `POST https://www.coinspot.com.au/api/v2/my/buy` - Place buy order
- `POST https://www.coinspot.com.au/api/v2/my/sell` - Place sell order
- `GET https://www.coinspot.com.au/api/v2/my/orders` - Get orders
- `GET https://www.coinspot.com.au/api/v2/my/balances` - Get all balances
- `GET https://www.coinspot.com.au/api/v2/api/ro/my/balances/:cointype` - Get specific balance

**Coinspot Authentication**:
- Method: HMAC-SHA512
- Headers: `sign` (signature), `key` (API key)
- Body: JSON with `nonce` field (timestamp in milliseconds)

**Database Tables**:
- `deployed_algorithms`
- `positions`
- `trades`
- `orders`

**Dependencies**:
- PostgreSQL
- User Service (fetch credentials)
- Lab Service (fetch algorithms)
- Coinspot Private API

---

## Database Schema

### Core Tables

#### users
*From template, extended for OMC*
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### coinspot_credentials
*Encrypted storage of Coinspot API credentials*
```sql
CREATE TABLE coinspot_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key_encrypted BYTEA NOT NULL,
    api_secret_encrypted BYTEA NOT NULL,
    is_validated BOOLEAN DEFAULT FALSE,
    last_validated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX idx_coinspot_credentials_user_id ON coinspot_credentials(user_id);
```

#### price_data_5min
*Time-series price data from Coinspot*
```sql
CREATE TABLE price_data_5min (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    coin_type VARCHAR(20) NOT NULL,
    bid NUMERIC(20, 8),
    ask NUMERIC(20, 8),
    last NUMERIC(20, 8),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(timestamp, coin_type)
);

CREATE INDEX idx_price_data_timestamp ON price_data_5min(timestamp DESC);
CREATE INDEX idx_price_data_coin_timestamp ON price_data_5min(coin_type, timestamp DESC);
CREATE INDEX idx_price_data_coin ON price_data_5min(coin_type);
```

#### algorithms
*User-created trading algorithms*
```sql
CREATE TABLE algorithms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    algorithm_type VARCHAR(50) NOT NULL, -- 'moving_average', 'mean_reversion', 'ml_model', etc.
    code TEXT NOT NULL, -- Python code or serialized model
    parameters JSONB, -- Algorithm-specific parameters
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'validated', 'deployable', 'deployed'
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_algorithms_user_id ON algorithms(user_id);
CREATE INDEX idx_algorithms_status ON algorithms(status);
```

#### algorithm_versions
*Version history for algorithms*
```sql
CREATE TABLE algorithm_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES algorithms(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    code TEXT NOT NULL,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(algorithm_id, version)
);

CREATE INDEX idx_algorithm_versions_algorithm_id ON algorithm_versions(algorithm_id);
```

#### algorithm_backtest_runs
*Backtest execution results*
```sql
CREATE TABLE algorithm_backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES algorithms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    coins JSONB NOT NULL, -- Array of coin types tested
    parameters JSONB, -- Algorithm parameters used
    results JSONB NOT NULL, -- P&L, Sharpe, drawdown, trade count, etc.
    execution_time_seconds NUMERIC(10, 2),
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_backtest_runs_algorithm_id ON algorithm_backtest_runs(algorithm_id);
CREATE INDEX idx_backtest_runs_user_id ON algorithm_backtest_runs(user_id);
CREATE INDEX idx_backtest_runs_created_at ON algorithm_backtest_runs(created_at DESC);
```

#### deployed_algorithms
*Algorithms deployed to The Floor for live trading*
```sql
CREATE TABLE deployed_algorithms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    algorithm_id UUID NOT NULL REFERENCES algorithms(id),
    user_id UUID NOT NULL REFERENCES users(id),
    deployment_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'stopped'
    coins JSONB NOT NULL, -- Array of coins to trade
    parameters JSONB, -- Runtime parameters
    risk_limits JSONB, -- Max position size, daily loss limit, etc.
    deployed_at TIMESTAMP DEFAULT NOW(),
    last_executed_at TIMESTAMP,
    last_signal_at TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    UNIQUE(user_id, deployment_name)
);

CREATE INDEX idx_deployed_algorithms_user_id ON deployed_algorithms(user_id);
CREATE INDEX idx_deployed_algorithms_status ON deployed_algorithms(status);
CREATE INDEX idx_deployed_algorithms_algorithm_id ON deployed_algorithms(algorithm_id);
```

#### positions
*Current trading positions*
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    deployed_algorithm_id UUID REFERENCES deployed_algorithms(id),
    coin_type VARCHAR(20) NOT NULL,
    quantity NUMERIC(20, 8) NOT NULL,
    avg_entry_price NUMERIC(20, 8) NOT NULL,
    current_price NUMERIC(20, 8),
    unrealized_pnl NUMERIC(20, 8),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, deployed_algorithm_id, coin_type)
);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_deployed_algorithm_id ON positions(deployed_algorithm_id);
```

#### trades
*Historical trade records*
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    deployed_algorithm_id UUID REFERENCES deployed_algorithms(id),
    coin_type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'buy' or 'sell'
    quantity NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 8) NOT NULL,
    total_value NUMERIC(20, 8) NOT NULL,
    fees NUMERIC(20, 8),
    coinspot_order_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'filled', 'partial', 'cancelled', 'failed'
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_deployed_algorithm_id ON trades(deployed_algorithm_id);
CREATE INDEX idx_trades_created_at ON trades(created_at DESC);
CREATE INDEX idx_trades_coin_type ON trades(coin_type);
```

#### orders
*Order tracking for Coinspot API*
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    trade_id UUID REFERENCES trades(id),
    coinspot_order_id VARCHAR(100) UNIQUE,
    coin_type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 8),
    status VARCHAR(20) DEFAULT 'submitted', -- 'submitted', 'accepted', 'filled', 'cancelled', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_trade_id ON orders(trade_id);
CREATE INDEX idx_orders_coinspot_order_id ON orders(coinspot_order_id);
CREATE INDEX idx_orders_status ON orders(status);
```

---

## Security Architecture

### Authentication Flow
1. User logs in via API Gateway → JWT token issued
2. JWT token included in all subsequent requests
3. API Gateway validates token and extracts user_id
4. Requests forwarded to services with user context

### Credential Encryption
- **Algorithm**: AES-256 with Fernet (symmetric encryption)
- **Key Storage**: Environment variable (AWS Secrets Manager in production)
- **Process**:
  1. User submits API key/secret
  2. Service encrypts with master key
  3. Encrypted bytes stored in database
  4. Decryption only when needed for API calls
  5. Credentials never logged or returned in API responses (masked)

### Coinspot API Authentication
```python
def sign_request(payload: dict, api_secret: str) -> str:
    """Generate HMAC-SHA512 signature for Coinspot API"""
    message = json.dumps(payload).encode('utf-8')
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message,
        hashlib.sha512
    ).hexdigest()
    return signature

# Usage
payload = {
    "nonce": int(time.time() * 1000),
    "cointype": "BTC",
    "amount": 100.00
}
signature = sign_request(payload, api_secret)
headers = {
    "sign": signature,
    "key": api_key,
    "Content-Type": "application/json"
}
```

### Algorithm Sandbox
- **Isolation**: RestrictedPython or subprocess with limited permissions
- **Resource Limits**: CPU time, memory, execution time
- **Import Restrictions**: Only approved libraries (numpy, pandas, sklearn)
- **No Network Access**: Algorithms cannot make external API calls
- **No File System Access**: Read-only data access via service APIs

---

## Data Flow

### Lab-to-Floor Pipeline
```
1. Developer creates algorithm in Lab
   ↓
2. Run backtests with historical data
   ↓
3. Validate performance (Sharpe > threshold, etc.)
   ↓
4. Promote algorithm (status: draft → deployable)
   ↓
5. Deploy to Floor with parameters
   ↓
6. Trading Service loads algorithm
   ↓
7. Execute on schedule, generate signals
   ↓
8. Submit orders to Coinspot API
   ↓
9. Track trades and calculate P&L
   ↓
10. Display results in dashboard
```

### Data Collection Flow
```
1. Collector Service runs every 5 minutes (cron)
   ↓
2. HTTP GET → https://www.coinspot.com.au/pubapi/v2/latest
   ↓
3. Parse JSON response
   {
     "status": "ok",
     "prices": {
       "btc": {"bid": "50000.00", "ask": "50100.00", "last": "50050.00"},
       "eth": {"bid": "3000.00", "ask": "3010.00", "last": "3005.00"},
       ...
     }
   }
   ↓
4. Insert into price_data_5min table
   ↓
5. Available for backtesting and live algorithm execution
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL 15+
- **Authentication**: JWT (from template)
- **Task Scheduling**: APScheduler or Celery
- **API Client**: httpx (async HTTP)
- **Data Science**: scikit-learn, pandas, numpy
- **Encryption**: cryptography (Fernet)

### Frontend
- **Framework**: Vue.js 3 (from template)
- **State Management**: Pinia
- **UI Components**: Vuetify or Element Plus
- **Charts**: Chart.js or ECharts
- **HTTP Client**: Axios

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (dev), EKS with autoscaling (prod)
- **Database**: RDS PostgreSQL (prod)
- **Caching**: Redis (ElastiCache in prod)
- **CI/CD**: GitHub Actions on self-hosted EKS runners
  - Two-node-group architecture (system-nodes + arc-runner-nodes)
  - Cluster Autoscaler with scale-to-zero capability
  - 40-60% cost savings compared to always-on configuration
  - See [EKS Infrastructure Documentation](infrastructure/aws/eks/README.md)
- **Monitoring**: CloudWatch, Prometheus, Grafana
- **Logging**: CloudWatch Logs, ELK Stack

---

## API Design Principles

### RESTful Conventions
- `GET /resource` - List resources
- `GET /resource/{id}` - Get specific resource
- `POST /resource` - Create resource
- `PUT /resource/{id}` - Update resource (full)
- `PATCH /resource/{id}` - Update resource (partial)
- `DELETE /resource/{id}` - Delete resource

### Response Format
```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional message"
}
```

### Error Format
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  }
}
```

### Pagination
```
GET /api/v1/lab/algorithms?page=1&per_page=20
```

Response includes:
```json
{
  "items": [ ... ],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

---

## Deployment Architecture (AWS)

```
┌─────────────────────────────────────────────────────────┐
│                    Route 53 (DNS)                        │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Application Load Balancer                   │
│                    (HTTPS/SSL)                           │
└────────┬───────────────────────────────────┬────────────┘
         │                                   │
┌────────▼────────┐                 ┌───────▼────────────┐
│   ECS Cluster   │                 │  CloudFront + S3   │
│   (Services)    │                 │   (Vue.js SPA)     │
│                 │                 └────────────────────┘
│ - API Gateway   │
│ - User Service  │
│ - Lab Service   │
│ - Trading Svc   │
│ - Collector Svc │
└────────┬────────┘
         │
┌────────▼────────────────────────┐
│    RDS PostgreSQL (Multi-AZ)    │
│      ElastiCache (Redis)        │
└─────────────────────────────────┘
```

---

## Scalability Considerations

### Horizontal Scaling
- Each microservice can scale independently
- Load balancer distributes traffic
- Stateless services (session in JWT/Redis)

### Database Optimization
- Read replicas for heavy read operations (historical data)
- Connection pooling
- Query optimization and indexing
- Partitioning for price_data_5min (by date)

### Caching Strategy
- Redis for:
  - Session data
  - Frequently accessed algorithms
  - Recent price data
  - P&L calculations (short TTL)

### Asynchronous Processing
- Celery for:
  - Backtest execution (long-running)
  - Batch data processing
  - Report generation
  - Email notifications

---

## Monitoring & Observability

### Metrics
- Request latency (p50, p95, p99)
- Error rates by service
- Database query performance
- Coinspot API response times
- Algorithm execution frequency
- Trade success/failure rates

### Logging
- Structured JSON logs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs for request tracing
- Sensitive data redaction

### Alerts
- Service health checks failing
- High error rates (>5%)
- Database connection pool exhaustion
- Coinspot API rate limiting
- Trading algorithm errors
- Daily loss limit exceeded

---

## Future Enhancements
1. **Multi-Exchange Support**: Extend beyond Coinspot (Binance, Kraken, etc.)
2. **Social Trading**: Share algorithms, copy trading
3. **Advanced ML**: Deep learning models, transformer architectures
4. **Real-time Streaming**: WebSocket price feeds
5. **Mobile App**: iOS/Android native apps
6. **Portfolio Optimization**: Modern portfolio theory integration
7. **Backtesting as a Service**: Allow external users to run backtests
8. **Algorithm Marketplace**: Buy/sell trading strategies

---

## Conclusion
This architecture provides a solid foundation for the Oh My Coins platform, balancing:
- **Security**: Encrypted credentials, sandboxed execution
- **Scalability**: Microservices, horizontal scaling
- **Maintainability**: Clear service boundaries, API-first design
- **User Experience**: Seamless Lab-to-Floor pipeline

The system is designed to grow from MVP to production-scale with minimal architectural changes.
