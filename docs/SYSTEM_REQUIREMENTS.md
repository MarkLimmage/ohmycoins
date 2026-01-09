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
