# Sprint 2.25 Retrospective: The Strategist & Workflow Analysis

**Date:** February 14, 2026
**Topic:** Track B Development Workflow & "Ghost Mode" Implementation
**Participants:** Mark (User), Copilot (Agent)

---

## 🚀 Executive Summary
The sprint goals for **"The Strategist" (Track B)** were successfully met. We implemented a working "Ghost Mode" (Paper Trading) environment, deployed a simulation script (`run_ma_strategy.py`), and verified that algorithmic signals are correctly audited.

However, the development session revealed significant friction in the **local Docker workflow**, specifically regarding port allocations and code synchronization.

---

## 🛑 Workflow Friction Points (The "Why it took longer")

### 1. Port Collision "Whac-A-Mole"
*   **Issue**: On startup, the Track B stack failed because ports `8094` (Traefik) and `1080` (Mailcatcher) were already bound, likely by Track C or the Main stack.
*   **Impact**: Required manual debugging, `lsof` checks, and editing `docker-compose.override.yml` multiple times to find clear ports (`8096/8097` and `1084`).
*   **Root Cause**: Lack of a centralized, automated registry or script to assign unique ports per "Track" workspace.

### 2. The "Docker CP" Pattern
*   **Issue**: Changes made to `backend/scripts/run_ma_strategy.py` locally were **not** reflecting inside the running container.
*   **Impact**: We had to manually run `docker cp backend/scripts/run_ma_strategy.py ...` after every edit.
*   **Root Cause**: The `docker-compose.override.yml` mounts `./backend/app` and `./backend/tests`, but **missing** `./backend/scripts`.
    ```yaml
    # Current Mounts
    volumes:
      - ./backend/app:/app/app
      - ./backend/tests:/app/tests
      # MISSING: - ./backend/scripts:/app/scripts
    ```

### 3. Manual Database Verification
*   **Issue**: To verify if the Audit Logs were working, we relied on executing complex Python one-liners inside the container via `docker exec`.
*   **Impact**: High cognitive load and risk of syntax errors. "Flying blind" regarding the state of the simulation until the query runs.
*   **Root Cause**: Lack of simple CLI utility scripts (e.g., `scripts/check_status.py`) to dump key metrics (Order counts, Audit Log tail).

---

## ✅ The Wins (What went right)
*   **Ghost Mode Verification**: The `PaperExchange` successfully blocked attempts to call the real CoinSpot API (verified via logs).
*   **Safety Logic**: Quickly identified a bug in `SafetyManager` (Gross vs Net exposure) and fixed it, preventing false positive blocks.
*   **Audit Trail**: Confirmed that `ALGORITHM_SIGNAL` events are writing to Postgres, satisfying the "Black Box" transparency requirement.

---

## 🛠 Action Plan (Next Steps)

1.  **Fix Docker Mounts**:
    *   Update `docker-compose.override.yml` to include `- ./backend/scripts:/app/scripts`.
    *   This will allow instant hot-reloading of simulation scripts.

2.  **Standardize Ports**:
    *   Update `README.md` with a "Track Port Matrix".
    *   Track A: 8000-8010
    *   Track B: 8020-8030
    *   Track C: 8040-8050

3.  **Create CLI Utils**:
    *   Build a lightweight TUI or script `scripts/status.sh` that queries the DB and prints:
        *   Active Algorithms
        *   Recent Audit Logs
        *   Current PnL (Ghost Mode)

---
**Status:** 🏁 Sprint Completed. Fixes documented.
