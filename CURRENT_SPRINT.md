# Current Sprint: 2.47

**Status**: IN PROGRESS
**Objective**: Backtesting Framework Hardening
**Previous Sprint**: 2.46 (Model Playground — COMPLETED)

## Context

Sprint 2.46 shipped Model Playground, artifact wiring, and promote endpoint (959 tests, clean lints). The Lab can now train ML models (12 sklearn types), optimize hyperparameters (Optuna), serialize models to disk, and test predictions via the Playground.

Sprint 2.47 addresses key gaps: XGBoost is installed but not integrated, training uses random splits (data leakage risk for time-series), no backtesting engine exists, and no performance metrics beyond basic PnL.

## Tasks

### Track H — Housekeeping

1. [x] **H1 — Close Sprint 2.46**
   - Updated CURRENT_SPRINT.md, ROADMAP.md

### Track A — Backend: Backtesting Framework

2. [ ] **A1 — XGBoost Integration**
   - Files: `model_training_tools.py`, `hyperparameter_search.py`
   - Add `xgboost` model type to classification/regression training + Optuna search

3. [ ] **A2 — Walk-Forward Validation**
   - File: `model_training_tools.py`
   - Add `validation_strategy` parameter: `random` (default), `time_series`, `expanding_window`
   - TimeSeriesSplit with n_splits=5, no shuffle, preserves temporal order

4. [ ] **A3 — Performance Metrics Calculator**
   - New: `backend/app/services/trading/metrics.py`
   - `calculate_backtest_metrics()`: Sharpe, Sortino, max drawdown, win rate, profit factor

5. [ ] **A4 — BacktestRun DB Model + Migration**
   - File: `backend/app/models.py`
   - New BacktestRun table with schemas + Alembic migration

6. [ ] **A5 — Backtesting Engine**
   - New: `backend/app/services/trading/backtester.py`
   - BacktestEngine: load algorithm, query prices, simulate trades, calculate metrics

7. [ ] **A6 — API Endpoints**
   - New: `backend/app/api/routes/backtests.py`
   - POST /floor/backtests, GET /floor/backtests/{id}, GET /floor/backtests

8. [ ] **A7 — Tests (~16 new)**
   - test_metrics.py (4), test_backtester.py (4), test_backtests.py (4)
   - test_optuna_tool.py additions (2), test_model_training_tools additions (2)

### Track B — Frontend: Backtesting UI

9. [ ] **B1 — Backtest Hooks**
   - New: `frontend/src/features/floor/hooks/useBacktest.ts`

10. [ ] **B2 — BacktestConfigPanel Component**
    - New: `frontend/src/features/floor/components/BacktestConfigPanel.tsx`

11. [ ] **B3 — BacktestResultsPanel Component**
    - New: `frontend/src/features/floor/components/BacktestResultsPanel.tsx`

12. [ ] **B4 — Floor Route**
    - New: `frontend/src/routes/_layout/floor.tsx`

13. [ ] **B5 — Sidebar Navigation**
    - File: `frontend/src/components/Common/SidebarItems.tsx`

14. [ ] **B6 — OpenAPI Client Regeneration**

## Key Files

| File | Change |
|------|--------|
| `backend/app/services/agent/tools/model_training_tools.py` | A1, A2 |
| `backend/app/services/agent/tools/hyperparameter_search.py` | A1 |
| `backend/app/services/trading/metrics.py` | A3: new |
| `backend/app/models.py` | A4: BacktestRun model |
| `backend/app/services/trading/backtester.py` | A5: new |
| `backend/app/api/routes/backtests.py` | A6: new |
| `backend/app/api/main.py` | A6: register router |
| `frontend/src/features/floor/hooks/useBacktest.ts` | B1: new |
| `frontend/src/features/floor/components/BacktestConfigPanel.tsx` | B2: new |
| `frontend/src/features/floor/components/BacktestResultsPanel.tsx` | B3: new |
| `frontend/src/routes/_layout/floor.tsx` | B4: new |
| `frontend/src/components/Common/SidebarItems.tsx` | B5: Floor link |

## Verification

- [ ] `docker compose exec backend bash scripts/test.sh` — 959+ passing (+ ~16 new)
- [ ] `docker compose exec backend bash scripts/lint.sh` — mypy + ruff clean
- [ ] `cd frontend && npm run type-check` — clean
- [ ] `cd frontend && npm run lint` — Biome clean
- [ ] Manual: XGBoost model trains successfully
- [ ] Manual: TimeSeriesSplit validation produces no future leakage
- [ ] Manual: POST /floor/backtests with BTC, 30-day range returns metrics + equity curve
- [ ] Manual: /floor page renders with Algorithms + Backtesting tabs
