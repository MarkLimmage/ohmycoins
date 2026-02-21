# Current Sprint - Sprint 2.26 (Autonomous Trading Beta)

**Status:** 🚀 PLANNED
**Overall Goal:** Transition from "Paper Trading" to "Limited Live Trading" (Beta), enabled by a fully integrated Strategist-Guard-Floor loop, and finalize the "Living Documentation" system.

---

## 🎯 Sprint 2.26 Objectives

### 1. Workflow Hygiene (The Architect & Tester)
*   **Goal**: Eliminate the "Phantom Code" and "Context Switching" friction identified in Sprint 2.25.
*   **Tasks**:
    *   **Enforcement**: Strict rejection of any PR that hasn't been verified on `origin`.
    *   **Tooling**: Check `clean_worktree.sh` into `scripts/` and integrate it into the developer shutdown routine.
    *   **CI/CD**: Verify the Self-Hosted Runner on `192.168.0.241` correctly auto-deploys `main` to the "Live" environment.

### 2. The Strategist - Live Beta (Track B)
*   **Goal**: First autonomous real-money trade (Limited Cap).
*   **Tasks**:
    *   **Strategy Promotion**: Select the best performing "Paper" agent (likely MA-Crossover) and promote it to "Live Candidates".
    *   **Execution**: Enable `CoinSpotPrivate` execution for this specific agentID, capped at $10 AUD/trade.
    *   **Monitoring**: Run the agent for 48h under strict supervision.

### 3. The Guard - Production Hardening (Track A)
*   **Goal**: Ensure The Guard can stop a "Live" runaway agent.
*   **Tasks**:
    *   **Latency Check**: ✅ Verified Risk Checks add <200ms (Actual: 6ms).
    *   **Double Circuit**: ✅ Implemented `HardStopWatcher` service monitoring total account equity (5% drawdown trigger).

### 4. The Interface - "The Floor" (Track C)
*   **Goal**: A unified "Mission Control" specifically for the Beta test.
*   **Tasks**:
    *   **Live vs Paper Toggle**: Unified dashboard showing both Paper P&L and Live P&L side-by-side.
    *   **Agent Control Panel**: "Pause/Resume" buttons for individual running agents.

---

## 📦 Deliverables

1.  **Live Trade Proof**: Transaction ID of the first autonomous real-money trade.
2.  **Unified Dashboard**: UI showing "Live Beta" status.
3.  **Workflow Report**: Zero instances of "Phantom Code" or Permission blockers.

---

**Last Updated:** Feb 2026
