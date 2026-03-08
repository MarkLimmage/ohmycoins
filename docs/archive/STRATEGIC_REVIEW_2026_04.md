# Strategic Review: Oh My Coins (OMC) - April 2026

**Date**: April 18, 2026  
**Reviewer**: GitHub Copilot (on behalf of Tech Lead)  
**Status**: DRAFT  
**Scope**: Project-wide retrospective and forward-looking strategy for MVP Live Deployment.

---

## 1. Executive Summary

As of Sprint 2.21 (The Optimizer), Oh My Coins has successfully transitioned from a data-collection utility to an intelligent, agentic trading platform. The functional core is robust: we have comprehensive data ingestion (4 Ledgers), sophisticated analysis tools (The Lab/Strategist), and a capable simulation engine (The Tactician).

However, a critical gap exists between our **functional maturity** and our **operational readiness**. While the software performs exceptionally well in local development, the production and staging environments remain "Pending Validation."

To achieve the goal of **User Live Testing (MVP)**, the project must pivoting from **Feature Development** to **Operational Hardening and Safety**. We cannot invite external users or enable real-money trading until the deployment pipeline is validated and the automated risk layer ("The Guard") is strictly enforced.

---

## 2. Progress to Date

### Phase 1: Foundation (Sprints 2.1 - 2.7)
*   **Achievement**: Built the "4 Ledgers" data engine.
*   **Status**: ✅ Stable & Production Ready.
*   **Impact**: We have a data advantage with established pipes for Glass (DeFiLlama), Human (Social), Catalyst (Events), and Exchange data.

### Phase 2: Intelligence & BYOM (Sprints 2.8 - 2.13)
*   **Achievement**: Implemented "Bring Your Own Model" and the Agentic Framework.
*   **Status**: ✅ Complete.
*   **Impact**: Users can bring OpenAI/Gemini/Claude keys, decoupling our specialized logic from LLM costs.

### Phase 3: The Trading Loop (Sprints 2.14 - 2.21)
*   **Achievement**: Connected "The Lab" (Ideas) to "The Floor" (Execution).
*   **Status**: ⚠️ Functionally Complete (Simulated).
*   **Highlights**:
    *   **The Strategist**: Backtesting with realistic fees (0.1%) and slippage (0.05%).
    *   **The Tactician**: Paper trading works locally.
    *   **The Optimizer**: Performance dashboard is live.

---

## 3. Current Capability Assessment

| Domain | Capability Level | Notes |
| :--- | :--- | :--- |
| **Data Ingestion** | 🟩 **High** | 4 Ledgers are stable and providing unique signals. |
| **Strategy Generation** | 🟩 **High** | "The Lab" reliably produces testable strategies. |
| **Simulation** | 🟩 **High** | Backtesting & Paper Trading accurately model market friction. |
| **Live Execution** | 🟨 **Medium** | "The Floor" UI is ready, but real-money execution is gated. |
| **Risk Management** | 🟧 **Low** | "The Guard" is specified but not fully integrated into the live loop. |
| **Infrastructure** | 🟥 **Critical** | Staging/Production environments are defined in Terraform but not validated. |

---

## 4. Critical Blockers to MVP (Live Testing)

### 1. The Deployment Gap
*   **Issue**: `DEPLOYMENT_STATUS.md` lists Staging and Production as "Not Deployed" or "Pending Validation."
*   **Risk**: We cannot invite users to `localhost`.
*   **Requirement**: Validate the AWS ECS/RDS terraform stack immediately.

### 2. The Safety Gap ("The Guard")
*   **Issue**: Moving from Paper to Money requires a fail-safe layer.
*   **Risk**: An agent hallucination could drain a wallet in minutes.
*   **Requirement**: "The Guard" must be a hard-coded, non-AI service that validates every order against strict risk parameters (Max Drawdown, Position Size, Daily Loss Limit) *before* it hits the exchange API.

### 3. User Onboarding
*   **Issue**: While Auth exists, the "New User" experience for setting up API keys and Risk Limits is likely rough (developer-centric).
*   **Requirement**: A polished "Onboarding Wizard" to securely collect Exchange Keys and set Risk Limits.

---

## 5. Strategic Recommendations

To optimize for an **Initial User Live Test** (MVP) in Q2 2026, we propose the following adjustments:

### Recommendation 1: "Operation Green Light" (Sprint 2.22)
**Stop all new feature development.** Dedicate the entirety of Sprint 2.22 to **Infrastructure & Deployment**.
*   **Goal**: A URL (`staging.ohmycoins.io`) that allows a team member to log in and see the dashboard.
*   **Tasks**:
    *   Validate Staging Terraform.
    *   Setup CI/CD pipeline for auto-deploy.
    *   Verify SSL/DNS automation.

### Recommendation 2: "The Guard" Implementation (Sprint 2.23)
**Safety First.** Before enabling the "Real Money" toggle, implement "The Guard" as a separate microservice or middleware.
*   **Goal**: Systematic prevention of catastrophic loss.
*   **Tasks**:
    *   Implement `RiskCheckService`.
    *   Hard-code "Circuit Breakers" (e.g., Kill Switch if -5% in 1 hour).
    *   Audit logging for all execution attempts.

### Recommendation 3: The "Closed Beta"
Define the scope of the MVP as a **Closed Beta** for trusted users (Internal + Friends/Family) only.
*   **Why**: testing risk management in production requires high trust.
*   **Action**: Create a whitelist mechanism in `UserService` to restrict access.

---

## 6. Conclusion
Oh My Coins is technically impressive but operationally fragile. The software is ready for the major leagues, but the stadium isn't built yet. 

**Immediate Action**: Shift focus from *creating intelligence* to *deploying infrastructure*.
