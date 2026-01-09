# Current Sprint Plan - Parallel Development Cycle

**Status:** Active
**Cycle:** Phase 2.5 (Data), Phase 3 (Agentic), Phase 9 (Infrastructure)
**Strategy:** 3-Developer Parallel Execution (Tracks A, B, C)

---

## 📅 Sprint Overview

This sprint synchronizes three parallel tracks to achieve a fully operational data-to-decision pipeline. The primary focus is finalizing the "Single Source of Truth" (Data), activating the "Autonomous Brain" (Agent), and deploying the "Scalable Foundation" (Infrastructure/ECS).

### 🎯 Strategic Goals
1.  **Track A (Data):** Complete the Catalyst Ledger (SEC, CoinSpot) and verify 4-Ledger integrity.
2.  **Track B (Agent):** Operationalize the ReAct Loop (LangGraph) with live data access.
3.  **Track C (Infra):** Finalize ECS production architecture (replacing EKS) and secure secrets.

---

## 🛣️ Track A: Data & Backend (OMC-Data-Specialist)
**Focus:** `backend/app/services/collectors/`
**Goal:** Achieve 100% Catalyst Ledger visibility and ensuring data quality for Agents.

| Priority | Task | Description | Status |
| :--- | :--- | :--- | :--- |
| **High** | **Catalyst: SEC API** | Implement `sec_api.py` to track Form 4/8-K filings for major crypto holders (MSTR, COIN). | [ ] Pending |
| **High** | **Catalyst: CoinSpot** | Finalize `coinspot_announcements.py` scraper for new listings/maintenance. | [ ] Pending |
| **Med** | **Quality Monitor** | Implement `quality_monitor.py` to flag stale or missing data across all 4 ledgers. | [ ] Pending |
| **Low** | **Human Ledger** | Expand `reddit.py` to cover 3 additional subreddits with sentiment scoring. | [ ] Pending |

**Dependencies:** None. Independent of other tracks.

---

## 🧠 Track B: Agentic AI (OMC-ML-Scientist)
**Focus:** `backend/app/services/agent/`
**Goal:** Connect the "Brain" to the "Eyes" (Data) and enable autonomous reasoning.

| Priority | Task | Description | Status |
| :--- | :--- | :--- | :--- |
| **High** | **Data Retrieval Agent** | Implement `DataRetrievalAgent` with tools to query the 4-Ledger database (using Track A's schema). | [ ] Pending |
| **High** | **ReAct Loop** | Finalize `orchestrator.py` to support full Reason-Act-Observe loops using LangGraph. | [ ] Pending |
| **Med** | **Analyst Agent** | Implement `DataAnalystAgent` with technical indicator tools (RSI, MACD) and sentiment alignment. | [ ] Pending |
| **Med** | **Human-in-the-Loop** | Add `clarification.py` node to ask user for guidance when confidence is low. | [ ] Pending |

**Dependencies:** Relies on Database Schema (Track A) being stable.

---

## 🏗️ Track C: Infrastructure & DevOps (OMC-DevOps-Engineer)
**Focus:** `infrastructure/terraform/`
**Goal:** Deploy a cost-effective, scalable ECS architecture (No EKS).

| Priority | Task | Description | Status |
| :--- | :--- | :--- | :--- |
| **High** | **ECS Transition** | Validate `modules/ecs/` and ensure all EKS references are archived/removed. | [ ] Pending |
| **High** | **Secrets Management** | Implement AWS Secrets Manager integration for `OPENAI_API_KEY` and DB credentials. | [ ] Pending |
| **Med** | **CI/CD Pipeline** | Update GitHub Actions to build/push Docker images to ECR and deploy to ECS Fargate. | [ ] Pending |
| **Med** | **Monitoring** | Configure CloudWatch dashboards for Container Insights (CPU/Memory/Latency). | [ ] Pending |

**Dependencies:** Deployment targets backend/agent Docker images.

---

## 🔗 Integration Points
*   **Data -> Agent:** Schema `backend/app/models.py` is the contract. Track A updates it; Track B reads it.
*   **Agent -> Infra:** Agents require `OPENAI_API_KEY` injected via AWS Secrets Manager (Track C).
*   **All -> Infra:** CI/CD pipeline (Track C) deploys code from Tracks A & B.

---

## 📜 Definition of Done (DoD)
1.  **Code:** Committed to `main` with passing tests (Unit + Integration).
2.  **Docs:** EARS-compliant requirements updated in `docs/`.
3.  **Deploy:** Staging environment successfully running latest build on ECS.
