# Current Sprint - Sprint 2.25 (Reliability & Scalability Polish)

**Status:** 🚀 PLANNED
**Overall Goal:** Eliminate technical debt identified in the 2.24 retrospective, solidify the "Guard" layer, and prepare "The Strategist" for autonomous trading on the live local server.

---

## 🎯 Sprint 2.25 Objectives

### 1. Robustness & Cleanup (The Architect & Tester)
*   **Goal**: Smooth out the "Worktree + Docker" workflow friction.
*   **Tasks**:
    *   Create `scripts/clean_worktree.sh` to handle the "root artifact" deletion automatically.
    *   Implement a Github Action or Pre-commit hook to check for `alembic` branching conflicts.
    *   Standardize `.env` templates to use docker service names by default.

### 2. The Guard - Phase 2 (Track A - Risk)
*   **Goal**: Advanced Risk Logic & Circuit Breakers.
*   **Tasks**:
    *   **Dynamic Limits**: Implement "Volatile Market" mode where limits tighten automatically if market volatility spikes (Glass Ledger integration).
    *   **Slack/Discord Alerts**: When the Kill Switch is triggered, fire a webhook notification.
    *   **Unit Test Coverage**: Increase coverage for `RiskCheckService` to >95%.

### 3. The Strategist - Live Paper Trading (Track B - AI)
*   **Goal**: Let the Agents trade "on paper" in the stable environment.
*   **Tasks**:
    *   **Paper Exchange**: verify `PaperExchange` class executes orders against local DB without touching CoinSpot API.
    *   **Strategy Loop**: Run a simple "Moving Average Crossover" agent for 24h on the local server.
    *   **Observation**: Ensure agents correctly log to `TradeAudit` (Track C's work).

### 4. The Interface - Audit Visualization (Track C - Frontend)
*   **Goal**: Visualize the decisions made by the Agents and The Guard.
*   **Tasks**:
    *   ✅ **Audit Log UI**: Table view of `TradeAudit` records (Who decided? Why? Outcome?).
    *   ✅ **Kill Switch History**: Timeline of when/why the switch was thrown.

---

## 📦 Deliverables

1.  **DevOps Scripts**: `clean_worktree.sh` functionality confirmed.
2.  **Alerting System**: Webhook fired on Risk Event.
3.  **Active Paper Trading**: Logs showing agents placing "paper" orders locally.
4.  **Audit Dashboard**: UI visible on `http://192.168.0.241:3001/audit`.

---

**Last Updated:** Feb 2026
