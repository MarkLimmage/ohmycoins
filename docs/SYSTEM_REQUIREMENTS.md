# System Requirements Specification

**Version**: 2.0
**Last Updated**: 2026-01-09
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
| FR-GL-003 | State-driven | While operating in Tier 2 mode, the System shall update "Smart Money" wallet flows from Nansen Pro API every 15 minutes. | Medium | 2 |
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
