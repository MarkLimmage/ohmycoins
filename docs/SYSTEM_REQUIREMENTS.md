# System Requirements Specification

**Version**: 2.1
**Last Updated**: 2026-01-24
**Status**: Consolidated

## 1. Executive Summary

This document serves as the Single Source of Truth for the system requirements of the Oh My Coins (OMC) platform. It consolidates the requirements for the **Comprehensive Data Collection** system (The 4 Ledgers) and the **Agentic Data Science Capability** (The Lab).

The system aims to transform from a simple price-tracking application into an autonomous, multi-agent trading platform capable of predictive market intelligence and automated strategy generation.

## 2. System Overview

### 2.1 Core Modules

1.  **Comprehensive Data Collection (The 4 Ledgers)**: A high-fidelity data ingestion engine that captures:
    *   **Glass Ledger**: On-chain and fundamental protocol metrics.
    *   **Human Ledger**: Social sentiment and narrative streams.
    *   **Catalyst Ledger**: Real-time event detection (listings, regulations).
    *   **Exchange Ledger**: Market microstructure and execution data.

2.  **Agentic Data Science (The Lab)**: An autonomous multi-agent framework utilizing ReAct patterns to:
    *   Interpret natural language trading goals.
    *   Execute end-to-end data science workflows (retrieval, analysis, training, evaluation).
    *   Generate and validate trading algorithms.

### 2.2 EARS Syntax Notation
Requirements are specified using the Easy Approach to Requirements Syntax (EARS) patterns:
*   **Ubiquitous**: *The <system> shall <action>.* (Always active)
*   **Event-driven**: *When <trigger>, the <system> shall <action>.* (Triggered response)
*   **State-driven**: *While <state>, the <system> shall <action>.* (Active during state)
*   **Optional**: *Where <feature>, the <system> shall <action>.* (Feature specific)
*   **Unwanted Behavior**: *If <condition>, the <system> shall <action>.* (Error handling)

## 3. Functional Requirements

### 3.1 Data Collection (The 4 Ledgers)

| ID | EARS Pattern | Requirement Statement | Priority | Tier |
|----|--------------|-----------------------|----------|------|
| **Glass Ledger** | | | | |
| FR-GL-001 | Ubiquitous | The System shall integrate with the DeFiLlama REST API to collect TVL, fees, and revenue data daily for configured protocols. | High | 1 |
| FR-GL-002 | Event-driven | When the daily collection schedule triggers, the System shall scrape free metrics (Active Addresses, Transaction Count, MVRV) from Glassnode and Santiment using Playwright. | Medium | 1 |
| FR-GL-003 ✅ | State-driven | While operating in Tier 2 mode, the System shall update "Smart Money" wallet flows from Nansen Pro API every 15 minutes. | Medium | 2 |
| **Human Ledger** | | | | |
| FR-HL-001 | Ubiquitous | The System shall query the CryptoPanic API every 5 minutes to collect news items tagged with sentiment (bullish/bearish/neutral). | High | 1 |
| FR-HL-002 | Ubiquitous | The System shall retrieve top 50 "hot" posts from configured subreddits via the Reddit API every 15 minutes. | Medium | 1 |
| FR-HL-003 | State-driven | While operating in Tier 3 mode, the System shall scrape X (Twitter) for influencer sentiment using proxy rotation to avoid detection. | Low | 3 |
| **Catalyst Ledger** | | | | |
| FR-CL-001 | Event-driven | When a new filing is detected via the SEC API (polled every 10 mins), the System shall parse it for crypto-related keywords. | High | 1 |
| FR-CL-002 | Ubiquitous | The System shall poll the CoinSpot Zendesk announcements page every 30-60 seconds to detect new listing keywords. | Critical | 1 |
| FR-CL-003 | Event-driven | When a "listing" keyword is detected in an announcement, the System shall immediately trigger a listing alert event. | Critical | 1 |
| **Exchange Ledger** | | | | |
| FR-EL-001 | Ubiquitous | The System shall collect real-time price data (bid, ask, last) and volume from CoinSpot API every 5-10 seconds. | Critical | 1 |
| FR-EL-002 | Event-driven | When an order request is received, the System shall validate sufficient balance before execution. | Critical | 1 |

### 3.2 Agentic Data Science (The Lab)

| ID | EARS Pattern | Requirement Statement | Priority |
|----|--------------|-----------------------|----------|
| **Orchestration** | | | |
| FR-AG-001 | Event-driven | When the User submits a natural language trading goal, the Orchestrator Agent shall generate a multi-step execution plan. | High |
| FR-AG-002 | Ubiquitous | The System shall utilize LangGraph to manage state transitions between the Planner, Data Retrieval, Analyst, Trainer, and Evaluator agents. | High |
| FR-AG-003 | State-driven | While executing a plan, the System shall persist agent state and memory to Redis to support resumption and context retention. | High |
| **Specialized Agents** | | | |
| FR-AG-004 | Event-driven | When the Data Retrieval Agent receives a data request, it shall query the PostgreSQL `price_data_5min` and 4-Ledgers tables. | High |
| FR-AG-005 | Ubiquitous | The Data Analyst Agent shall perform exploratory data analysis (EDA) and generate feature sets (technical indicators, sentiment scores) using pandas/numpy. | High |
| FR-AG-006 | Ubiquitous | The Model Training Agent shall train candidate models (Regression, Random Forest, XGBoost) utilizing scikit-learn within a secure sandbox. | High |
| FR-AG-007 | Event-driven | When model training completes, the Model Evaluator Agent shall calculate performance metrics (Accuracy, F1, ROI) and compare against baselines. | High |
| **Human-in-the-Loop** | | | |
| FR-AG-008 | If | If the Agent encounters ambiguity in the user goal, it shall pause execution and request clarification from the User via the API. | High |
| FR-AG-009 | Event-driven | When the System proposes a final model for deployment, it shall require explicit User approval before promotion. | High |

## 4. Non-Functional Requirements

### 4.1 Performance & Latency
*   **NFR-P-001**: Catalyst Ledger events (e.g., listings) shall be detected and processed within **30 seconds**.
*   **NFR-P-002**: Exchange Ledger price updates shall occur with a latency of **< 10 seconds**.
*   **NFR-P-003**: Agentic workflows for simple tasks shall complete within **5 minutes**.
*   **NFR-P-004**: The System shall support **10+ concurrent agent sessions**.

### 4.2 Security
*   **NFR-S-001**: All external API credentials shall be encrypted at rest using **Fernet/AES-256**.
*   **NFR-S-002**: Agent code execution shall be confined to a **restricted sandbox** with no network access (except explicit data retrieval tools).
*   **NFR-S-003**: No plaintext secrets shall be included in architectural designs or logs.

### 4.3 Reliability & Integrity
*   **NFR-R-001**: Critical collectors (Catalyst, Exchange) shall maintain **99% uptime**.
*   **NFR-R-002**: The System shall enforce the **4 Ledgers Framework**, ensuring all data designs map to Glass, Human, Catalyst, or Exchange taxonomies.

## 5. Integration Requirements

*   **IR-001**: The System shall expose a **FastAPI** backend for all client interactions.
*   **IR-002**: Data persistence shall utilize **PostgreSQL** for structured data and **Redis** for hot state/caching.
*   **IR-003**: The architecture shall support a seamless pipeline from **Lab** (discovery) to **Floor** (execution), allowing approved models to be promoted without code rewrites.

## 6. Development Standards
*   **DS-001**: All architectural changes shall be documented using **EARS** notation.
*   **DS-002**: Development shall strictly adhere to **Parallel Development Boundaries**:
    *   Track A: `backend/app/services/collectors/`
    *   Track B: `backend/app/services/agent/`
    *   Track C: `infrastructure/terraform/`
*   **DS-003**: Outdated plans shall be proactively moved to `/docs/archive/`.

---

## 7. Bring Your Own Model (BYOM) Requirements

### 7.1 Functional Requirements - BYOM

#### User Credential Management
*   **FR-BYOM-001**: While the user is authenticated, the system shall allow configuration of LLM provider credentials (OpenAI, Google, Anthropic).
*   **FR-BYOM-002**: When the user submits an API key, the system shall validate the key with the provider before saving.
*   **FR-BYOM-003**: While the user has multiple LLM credentials configured, the system shall allow designation of one as the default.
*   **FR-BYOM-004**: When the user requests deletion of LLM credentials, the system shall perform a soft delete (set `is_active=False`).
*   **FR-BYOM-005**: While viewing configured credentials, the system shall mask API keys (show first 4 and last 6 characters only).

#### Agent Session Integration
*   **FR-BYOM-006**: When an agent session starts, if the user has a default LLM credential configured, the system shall use that credential for all LLM operations.
*   **FR-BYOM-007**: When an agent session starts, if the user has no BYOM configuration, the system shall fall back to the system default LLM.
*   **FR-BYOM-008**: When an agent completes execution, the system shall record which LLM provider and model were used in the session metadata.
*   **FR-BYOM-009**: While creating an agent session, the system shall allow the user to select from their configured LLM credentials.

#### Multi-Provider Support
*   **FR-BYOM-010**: The system shall support OpenAI models: gpt-4, gpt-4-turbo, gpt-3.5-turbo.
*   **FR-BYOM-011**: The system shall support Google Gemini models: gemini-1.5-pro, gemini-1.5-flash.
*   **FR-BYOM-012**: The system shall support Anthropic Claude models: claude-3-opus, claude-3-sonnet, claude-3-haiku.
*   **FR-BYOM-013**: When instantiating an LLM, the system shall use provider-specific configurations (API endpoints, authentication methods).

### 7.2 Non-Functional Requirements - BYOM

#### Performance
*   **NFR-BYOM-P-001**: Retrieving and decrypting user LLM credentials shall complete in **<100ms**.
*   **NFR-BYOM-P-002**: Agent session initialization with BYOM shall add **<500ms** overhead compared to system default.
*   **NFR-BYOM-P-003**: API key validation shall timeout after **10 seconds** if provider is unresponsive.

#### Security
*   **NFR-BYOM-S-001**: The system shall encrypt all user LLM API keys using **AES-256** encryption before storage.
*   **NFR-BYOM-S-002**: The system shall never log plaintext API keys (all logs must mask keys).
*   **NFR-BYOM-S-003**: The system shall audit-log all LLM credential retrievals with user ID, session ID, and timestamp.
*   **NFR-BYOM-S-004**: The system shall enforce rate limiting: **max 10 key validations per user per hour**.
*   **NFR-BYOM-S-005**: The system shall enforce rate limiting: **max 100 LLM API calls per agent session** (cost protection).
*   **NFR-BYOM-S-006**: The system shall support API key rotation without service interruption.
*   **NFR-BYOM-S-007**: The system shall prevent users from accessing other users' LLM credentials.

#### Usability
*   **NFR-BYOM-U-001**: Configuring a new LLM provider credential shall take **<2 minutes** for an average user.
*   **NFR-BYOM-U-002**: The UI shall provide real-time feedback during API key validation (success/error within 3 seconds).
*   **NFR-BYOM-U-003**: The UI shall display estimated cost per 1000 tokens for each provider/model.
*   **NFR-BYOM-U-004**: The system shall alert users if an agent session exceeds **$10 in API costs**.

#### Backward Compatibility
*   **NFR-BYOM-BC-001**: Existing users without BYOM configuration shall continue using the system default LLM without interruption.
*   **NFR-BYOM-BC-002**: All existing agent tests shall pass with all supported LLM providers (OpenAI, Google, Anthropic).

### 7.3 Data Model Requirements - BYOM

*   **DM-BYOM-001**: The system shall persist user LLM credentials in a new `user_llm_credentials` table.
*   **DM-BYOM-002**: The `user_llm_credentials` table shall have a foreign key to the `user` table.
*   **DM-BYOM-003**: The `agent_session` table shall be extended to store `llm_credentials_id`, `llm_provider`, and `llm_model_name`.
*   **DM-BYOM-004**: LLM provider values shall be constrained to an ENUM: `['openai', 'google', 'anthropic', 'azure_openai']`.

### 7.4 Integration Requirements - BYOM

*   **IR-BYOM-001**: The system shall extend the existing `EncryptionService` to support LLM API key encryption (reuse CoinSpot pattern).
*   **IR-BYOM-002**: The system shall implement an `LLMFactory` pattern to instantiate provider-specific LLM clients.
*   **IR-BYOM-003**: The `AgentOrchestrator` shall be refactored to accept LLM instances via dependency injection.
*   **IR-BYOM-004**: All agent classes (`BaseAgent`, `PlannerAgent`, `DataAnalystAgent`, etc.) shall accept an `llm` parameter in their constructors.
*   **IR-BYOM-005**: The system shall use LangChain's provider-specific classes: `ChatOpenAI`, `ChatGoogleGenerativeAI`, `ChatAnthropic`.

### 7.5 Testing Requirements - BYOM

*   **TR-BYOM-001**: The system shall have unit tests for API key encryption/decryption with 100% coverage.
*   **TR-BYOM-002**: The system shall have integration tests for creating agent sessions with all 3 supported providers.
*   **TR-BYOM-003**: The system shall have E2E tests (Playwright) for the complete BYOM configuration workflow.
*   **TR-BYOM-004**: The system shall validate that all 318 agent tests pass when using OpenAI, Google Gemini, and Anthropic Claude.

---
## 8. Trading Execution (The Floor)

### 8.1 Functional Requirements - The Floor

| ID | EARS Pattern | Requirement Statement | Priority |
| --- | --- | --- | --- |
| **Algorithm Deployment** |  |  |  |
| FR-FL-001 | Event-driven | When a User promotes an approved model from the Lab, the System shall instantiate a dedicated Execution Worker for that algorithm. | High |
| FR-FL-002 | Ubiquitous | The System shall map the algorithm’s abstract "Trade" signals to specific CoinSpot API endpoints (`/my/buy` or `/my/sell`). | Critical |
| **Order Management** |  |  |  |
| FR-FL-003 | Event-driven | When an order is placed, the System shall poll the `/my/orders` endpoint every 2 seconds until the status is 'Complete' or 'Cancelled'. | High |
| FR-FL-004 | Ubiquitous | The System shall calculate Realized and Unrealized P&L in real-time by comparing current `Exchange Ledger` prices against the `last_price` in `/my/balances`. | High |
| **Risk & Safety** |  |  |  |
| FR-FL-005 | State-driven | While an algorithm is active, the System shall prevent any single trade from exceeding the User-defined "Max Position Size" (Position Limit). | Critical |
| FR-FL-006 | Event-driven | When an account’s total daily drawdown exceeds the User-defined "Loss Limit," the System shall trigger the Emergency Stop. | Critical |
| FR-FL-007 | Event-driven | When the Emergency Stop is triggered, the System shall cancel all open orders and liquidate all active positions to AUD/USDT. | Critical |
| FR-FL-008 | Ubiquitous | The System shall provide a manual "Kill Switch" in the UI to allow the User to instantly terminate all Floor execution. | Critical |
| **Execution Quality** | | | |
| FR-FL-009 | Ubiquitous | The System shall calculate slippage for every executed parent order. | High |
| FR-FL-010 | Event-driven | When slippage exceeds the defined tolerance (default 10 bps), the System shall flag the execution report for review. | Medium |

### 8.2 Non-Functional Requirements - The Floor

* **NFR-FL-P-001**: Signal-to-Execution latency (the time from an algorithm generating a signal to the API call being sent) shall be **< 500ms**.
* **NFR-FL-Q-001**: Execution Slippage shall not exceed **10 bps (0.10%)** for standard TWAP/VWAP orders in normal market conditions.
* **NFR-FL-R-001**: The Execution Worker shall implement an exponential backoff retry logic for CoinSpot API `5xx` errors.
* **NFR-FL-S-001**: Trading operations shall require a dedicated "Trading API Key" with restricted permissions (No Withdrawal access).
* **NFR-FL-I-001**: The System shall maintain an immutable audit log of every signal generated, order sent, and response received.

---

### 8.3 Data Model Requirements - The Floor

* **DM-FL-001**: The system shall implement a `deployed_algorithms` table to track active models, their versions, and their current "Heartbeat" status.
* **DM-FL-002**: The system shall implement a `trade_ledger` table to store all execution history, linking `order_id` from CoinSpot to the internal `algorithm_id`.

### 8.4 Disconnected State Requirements - The Floor

| ID | EARS Pattern | Requirement Statement | Priority |
| --- | --- | --- | --- |
| **WebSocket Lifecycle** |  |  |  |
| REQ-FL-DISC-001 | Event-driven | When the WebSocket connection to The Floor is lost for > 10 seconds, the System shall display a "DISCONNECTED" banner and switch to REST API polling every 2 seconds. | Critical |
| REQ-FL-DISC-002 | State-driven | While in disconnected mode for 60-300 seconds, the System shall increase polling interval to 5 seconds and display a "DEGRADED MODE" warning. | High |
| REQ-FL-DISC-003 | Event-driven | When disconnected for > 300 seconds (5 minutes), the System shall display a critical alert recommending Emergency Stop and manual intervention. | Critical |
| REQ-FL-DISC-004 | Event-driven | When the WebSocket reconnects successfully, the System shall fetch a full state sync (GET /api/v1/trading/floor/sync) to catch up on missed updates. | High |
| **Fallback Mechanisms** |  |  |  |
| REQ-FL-DISC-005 | Ubiquitous | The Kill Switch shall support 3-level fallback: WebSocket → REST API → Manual Intervention (contact support). | Critical |
| REQ-FL-DISC-006 | State-driven | While in disconnected mode, the System shall display data staleness indicators ("Last updated: X seconds ago") on all real-time metrics. | Medium |
| REQ-FL-DISC-007 | Event-driven | When reconnection attempts fail consecutively for 30 seconds, the System shall use exponential backoff (1s, 2s, 4s, 8s, 16s, max 30s). | Medium |

---

## 9. UI/UX Non-Functional Requirements

### 9.1 Performance & Responsiveness

| ID | Requirement Statement | Priority |
| --- | --- | --- |
| **Response Times** |  |  |
| NFR-UX-P-001 | UI updates (chart re-renders, P&L ticker changes) shall complete in **< 500ms** from data received. | High |
| NFR-UX-P-002 | Initial page load for The Lab or The Floor shall complete in **< 2 seconds** (excluding data fetching). | Medium |
| NFR-UX-P-003 | Chart rendering (4 Ledgers dashboard) shall complete in **< 100ms** for initial render. | High |
| NFR-UX-P-004 | WebSocket message processing (Catalyst events, P&L updates) shall update UI within **< 50ms** of message receipt. | Critical |
| **Data Refresh Rates** |  |  |
| NFR-UX-P-005 | Glass Ledger cards (TVL, fees) shall refresh via polling every **5 seconds**. | Medium |
| NFR-UX-P-006 | Exchange Ledger sparklines (prices) shall update every **10 seconds**. | High |
| NFR-UX-P-007 | The Floor P&L ticker shall update in real-time via WebSocket (every trade execution). | Critical |
| NFR-UX-P-008 | Catalyst Ledger events shall appear within **30 seconds** of detection (end-to-end latency from source to UI). | Critical |

### 9.2 Accessibility (WCAG 2.1 AA Compliance)

| ID | Requirement Statement | Priority |
| --- | --- | --- |
| **Chart Accessibility** |  |  |
| REQ-UX-001 | All charts (Glass TVL, Human heatmap, Exchange sparklines) shall provide a "View as Table" toggle for screen reader users. | High |
| REQ-UX-002 | Chart table views shall support keyboard navigation (arrow keys), sorting (click headers), and CSV export. | High |
| REQ-UX-003 | All charts shall have descriptive ARIA labels (e.g., "Glass Ledger TVL chart showing upward trend over 30 days, current value $42.5 billion"). | Medium |
| **Keyboard Navigation** |  |  |
| REQ-UX-004 | The System shall support global keyboard shortcuts: Ctrl+Shift+K (focus Kill Switch), Ctrl+Shift+T (toggle all table views). | High |
| REQ-UX-005 | All interactive elements (buttons, links, form inputs) shall be keyboard-accessible (Tab/Shift+Tab navigation, Enter/Space activation). | Critical |
| REQ-UX-006 | Focus indicators shall be visible (2px outline) and meet 3:1 contrast ratio per WCAG 2.1 AA. | Medium |
| **Live Regions & Alerts** |  |  |
| REQ-UX-007 | Critical alerts (Catalyst events, disconnection warnings, Emergency Stop confirmations) shall use ARIA live regions with `aria-live="assertive"`. | Critical |
| REQ-UX-008 | P&L updates and non-critical notifications shall use `aria-live="polite"` to avoid interrupting screen readers. | Medium |
| REQ-UX-009 | The Kill Switch shall have a detailed `aria-describedby` description: "Press to stop all active trading algorithms and close all open positions. This action requires confirmation." | Critical |

### 9.3 Visual Design & Consistency

| ID | Requirement Statement | Priority |
| --- | --- | --- |
| **Design Tokens** |  |  |
| NFR-UX-V-001 | The System shall use a consistent color palette: Glass (blue #3b82f6), Human (green #10b981), Catalyst (amber #f59e0b), Exchange (purple #a855f7). | Medium |
| NFR-UX-V-002 | The System shall use a 8px spacing scale (xs=4px, sm=8px, md=16px, lg=24px, xl=32px, xxl=48px) for all layout margins and padding. | Low |
| NFR-UX-V-003 | Interactive elements (buttons, cards) shall have consistent hover states: brightness(1.1) or opacity(0.9) with 150ms transition. | Low |
| **Responsive Design** |  |  |
| NFR-UX-V-004 | The System shall support 3 breakpoints: Mobile (< 768px), Tablet (768-1279px), Desktop (≥ 1280px). | High |
| NFR-UX-V-005 | The Floor (trading controls) shall be desktop-only in Phase 1 MVP (mobile shows read-only activity log). | High |
| NFR-UX-V-006 | The 4 Ledgers dashboard shall adapt layout: 2x2 grid (desktop/tablet), vertical stack (mobile with priority order: Catalyst, Exchange, Human, Glass). | Medium |

### 9.4 Error Handling & User Feedback

| ID | Requirement Statement | Priority |
| --- | --- | --- |
| **Error Messages** |  |  |
| NFR-UX-E-001 | HTTP error responses shall map to user-friendly messages (e.g., 429 → "Too many requests. Please wait [X] seconds." with countdown timer). | High |
| NFR-UX-E-002 | The System shall display inline validation errors for form inputs (e.g., "API key format invalid. Expected: sk-..."). | Medium |
| NFR-UX-E-003 | Fatal errors (Exchange API down, database connection lost) shall show a full-screen error modal with support contact information. | Critical |
| **Loading States** |  |  |
| NFR-UX-E-004 | Data fetching operations shall show skeleton screens for chart areas (gray rectangles approximating final layout). | Medium |
| NFR-UX-E-005 | Button actions (Pause Algorithm, Stop, Emergency Stop) shall show inline spinners ("Pausing...", "Stopping...") and disable button during execution. | High |
| NFR-UX-E-006 | Long-running operations (> 5 seconds) shall show progress bars with percentage and estimated time remaining. | Medium |

---

## 10. Cross-Module Integration Requirements

### 10.1 Lab-to-Floor Promotion Workflow

| ID | EARS Pattern | Requirement Statement | Priority |
| --- | --- | --- | --- |
| **Model Handoff** |  |  |  |
| IR-LAB-FLOOR-001 | Event-driven | When the User approves a Lab model for promotion, the System shall serialize the trained model (pickle/joblib) and hyperparameters to persistent storage (S3 or PostgreSQL BYTEA). | High |
| IR-LAB-FLOOR-002 | Event-driven | When the System deploys a promoted model to The Floor, it shall deserialize the model and instantiate an Execution Worker with identical parameters (no code rewrites). | Critical |
| IR-LAB-FLOOR-003 | Ubiquitous | The System shall maintain a `model_version_registry` table linking Lab session IDs to deployed Floor algorithms for traceability. | High |
| **Risk Validation** |  |  |  |
| IR-LAB-FLOOR-004 | Event-driven | When a model is promoted, the System shall validate that User-defined risk limits (Max Position Size, Stop Loss %, Daily Loss Limit) are configured. | Critical |
| IR-LAB-FLOOR-005 | If | If risk limits are not configured, the System shall block promotion and prompt the User to set limits via the UI. | High |

### 10.2 Ledger-to-Lab Data Pipeline

| ID | EARS Pattern | Requirement Statement | Priority |
| --- | --- | --- | --- |
| **Data Availability** |  |  |  |
| IR-LEDGER-LAB-001 | Ubiquitous | The Lab Data Retrieval Agent shall have read-only access to all 4 Ledgers tables (via SQLAlchemy ORM with user-scoped queries). | High |
| IR-LEDGER-LAB-002 | Event-driven | When the User requests historical data (e.g., "Get BTC prices for last 30 days"), the Agent shall query `price_data_5min` and aggregate to requested granularity (hourly, daily). | High |
| IR-LEDGER-LAB-003 | Ubiquitous | The Lab shall support real-time data access: Agents can subscribe to Ledger WebSocket streams for live analysis (e.g., "Monitor BTC price in real-time for next 5 minutes"). | Medium |
| **Feature Engineering** |  |  |  |
| IR-LEDGER-LAB-004 | Ubiquitous | The Data Analyst Agent shall compute technical indicators (SMA, EMA, RSI, MACD) from Exchange Ledger price data using TA-Lib or pandas-ta. | High |
| IR-LEDGER-LAB-005 | Ubiquitous | The Data Analyst Agent shall merge sentiment scores (Human Ledger) with price data (Exchange Ledger) for multi-modal feature sets. | Medium |

### 10.3 BYOM Integration with Agent Orchestration

| ID | EARS Pattern | Requirement Statement | Priority |
| --- | --- | --- | --- |
| **LLM Provider Routing** |  |  |  |
| IR-BYOM-AGENT-001 | Event-driven | When an agent session starts, the LLMFactory shall retrieve the User's default LLM credentials from the `user_llm_credentials` table and instantiate the provider-specific client (ChatOpenAI, ChatGoogleGenerativeAI, ChatAnthropic). | High |
| IR-BYOM-AGENT-002 | Event-driven | When an agent encounters a rate limit (HTTP 429), the System shall automatically fall back to the system default LLM and notify the User. | Medium |
| IR-BYOM-AGENT-003 | Ubiquitous | All agent LLM calls (planning, analysis, training prompts) shall include the User's configured temperature, max_tokens, and model name in the request. | High |
| **Cost Tracking** |  |  |  |
| IR-BYOM-AGENT-004 | Event-driven | When an agent completes an LLM call, the System shall calculate cost (tokens × provider rate) and accumulate in the `agent_session.total_cost` field. | High |
| IR-BYOM-AGENT-005 | Event-driven | When a session's total cost exceeds the User-defined "Cost Alert Threshold" (default $10), the System shall send an in-app notification and email alert. | Medium |

### 10.4 WebSocket Architecture for Real-Time Features

| ID | EARS Pattern | Requirement Statement | Priority |
| --- | --- | --- | --- |
| **Connection Management** |  |  |  |
| IR-WS-001 | Ubiquitous | The System shall implement WebSocket endpoints at `/ws/ledgers/catalyst/live`, `/ws/floor/pnl`, and `/ws/lab/agent-stream` using FastAPI WebSockets. | High |
| IR-WS-002 | Event-driven | When a WebSocket client connects, the System shall authenticate the JWT token passed via query parameter (`?token={jwt}`) and reject unauthorized connections. | Critical |
| IR-WS-003 | State-driven | While a WebSocket connection is active, the System shall send heartbeat pings every 30 seconds and expect pong responses within 5 seconds. | High |
| **Message Format** |  |  |  |
| IR-WS-004 | Ubiquitous | All WebSocket messages shall follow a standard JSON schema: `{"type": "event_type", "data": {...}, "timestamp": "ISO 8601"}`. | High |
| IR-WS-005 | Event-driven | When the backend publishes a Catalyst event, all connected clients subscribed to `/ws/ledgers/catalyst/live` shall receive the message within 100ms. | Critical |

---

## Document Governance

**Version History**:
- v2.0 (2026-01-24): Added Section 9 (UI/UX Non-Functional Requirements), Section 10 (Cross-Module Integration), and Section 8.4 (Disconnected State - REQ-FL-DISC-001)
- v1.9 (2026-01-09): Added Section 8 (Trading Execution - The Floor) with functional, non-functional, and data model requirements
- v1.0 (2025-12-15): Initial consolidated document with 4 Ledgers + Lab requirements

**Review Schedule**: Quarterly (next review: 2026-04-24)  
**Ownership**: Product Manager (system-level), Tech Lead (technical details)  
**Related Documents**:
- [DOCUMENTATION_STRATEGY.md](DOCUMENTATION_STRATEGY.md) - Documentation governance and maintenance policy
- [USER_JOURNEYS.md](USER_JOURNEYS.md) - Persona-driven user interaction flows
- [API_CONTRACTS.md](API_CONTRACTS.md) - API interaction patterns and UI behavior contracts
- [docs/ui/DESIGN_SYSTEM.md](ui/DESIGN_SYSTEM.md) - Component library specifications
- [docs/ui/DATA_VISUALIZATION_SPEC.md](ui/DATA_VISUALIZATION_SPEC.md) - Chart specifications for 4 Ledgers
- [docs/ui/TRADING_UI_SPEC.md](ui/TRADING_UI_SPEC.md) - Floor controls and disconnected state handling
