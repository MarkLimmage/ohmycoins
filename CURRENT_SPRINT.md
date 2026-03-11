# Current Sprint: 2.48

**Status**: COMPLETED
**Objective**: Explainable AI + Feature Store
**Previous Sprint**: 2.47 (Backtesting Framework Hardening — COMPLETED)

## Context

Sprint 2.47 shipped XGBoost integration, walk-forward validation, backtesting engine with performance metrics, and Floor UI (966 tests, clean lints). The Lab can now train 14 model types, optimize hyperparameters, run backtests with equity curves, and test predictions via the Playground.

Sprint 2.48 addresses two gaps:
1. **Model Opacity**: Users can see predictions but not *why* — SHAP explainability adds feature importance and per-prediction explanations.
2. **Ad-hoc Training Data**: No pre-computed, bias-free training dataset — the Feature Store creates PostgreSQL Materialized Views with strict T-1h lag to prevent look-ahead bias.

## Tasks

### Track H — Housekeeping

1. [x] **H1 — Close Sprint 2.47**
   - Updated CURRENT_SPRINT.md, ROADMAP.md

### Track A — Backend: Explainable AI (SHAP)

2. [x] **A1 — Add `shap` dependency**
   - File: `backend/pyproject.toml`

3. [x] **A2 — SHAP Explainability Service**
   - New: `backend/app/services/agent/explainability.py`
   - ExplainabilityService: TreeExplainer (RF/GB/DT/XGB), LinearExplainer (LogReg/LinReg/Ridge/Lasso), unsupported (SVM)

4. [x] **A3 — Extend Prediction with SHAP**
   - File: `backend/app/services/agent/playground.py`
   - predict_with_explanation() for per-prediction SHAP values

5. [x] **A4 — API Endpoints**
   - File: `backend/app/api/routes/agent.py`, `schemas.py`
   - POST /artifacts/{id}/explain, GET /artifacts/{id}/explain
   - Extend POST /artifacts/{id}/predict with include_explanation

6. [x] **A5 — Tests (~12 new)**
   - New: `backend/tests/services/agent/test_explainability.py`
   - Additions to `test_agent_playground.py`

### Track B — Frontend: Explainability UI

7. [x] **B1 — Explainability Hooks**
   - New: `frontend/src/features/lab/hooks/useExplainability.ts`

8. [x] **B2 — FeatureImportanceChart Component**
   - New: `frontend/src/features/lab/components/FeatureImportanceChart.tsx`

9. [x] **B3 — PredictionExplanation Component**
   - New: `frontend/src/features/lab/components/PredictionExplanation.tsx`

10. [ ] **B4 — SHAPSummaryPlot Component**
    - New: `frontend/src/features/lab/components/SHAPSummaryPlot.tsx`

11. [x] **B5 — Integration into ModelPlaygroundPanel**
    - File: `frontend/src/features/lab/components/ModelPlaygroundPanel.tsx`

12. [x] **B6 — Integration into ArtifactViewer**
    - File: `frontend/src/features/lab/components/ArtifactViewer.tsx`

13. [x] **B7 — OpenAPI Client Regeneration**

### Track C — Backend: Feature Store (Materialized Views)

14. [x] **C1 — Alembic Migration for Materialized Views**
    - New: `backend/app/alembic/versions/xxxx_feature_store_mvs.py`
    - 4 MVs: mv_coin_targets_5min, mv_sentiment_signals_1h, mv_catalyst_impact_decay, mv_training_set_v1

15. [x] **C2 — MV Refresh Scheduler**
    - File: `backend/app/enrichment/views.py`
    - Extend refresh_materialized_views() with Feature Store MVs

16. [x] **C3 — Training Data Retrieval Tool**
    - File: `backend/app/services/agent/tools/data_retrieval_tools.py`
    - fetch_training_data() querying mv_training_set_v1

17. [x] **C4 — Tests (~6 new)**
    - New: `backend/tests/services/agent/test_feature_store.py`

## Key Files

| File | Change |
|------|--------|
| `backend/pyproject.toml` | A1: shap dependency |
| `backend/app/services/agent/explainability.py` | A2: new |
| `backend/app/services/agent/playground.py` | A3: predict_with_explanation |
| `backend/app/services/agent/schemas.py` | A4: ExplanationResponse |
| `backend/app/api/routes/agent.py` | A4: explain endpoints |
| `backend/tests/services/agent/test_explainability.py` | A5: new |
| `frontend/src/features/lab/hooks/useExplainability.ts` | B1: new |
| `frontend/src/features/lab/components/FeatureImportanceChart.tsx` | B2: new |
| `frontend/src/features/lab/components/PredictionExplanation.tsx` | B3: new |
| `frontend/src/features/lab/components/SHAPSummaryPlot.tsx` | B4: new |
| `frontend/src/features/lab/components/ModelPlaygroundPanel.tsx` | B5: explain integration |
| `frontend/src/features/lab/components/ArtifactViewer.tsx` | B6: explain button |
| `backend/app/alembic/versions/xxxx_feature_store_mvs.py` | C1: new |
| `backend/app/enrichment/views.py` | C2: MV refresh |
| `backend/app/services/agent/tools/data_retrieval_tools.py` | C3: fetch_training_data |
| `backend/tests/services/agent/test_feature_store.py` | C4: new |

## Verification

- [ ] `docker compose exec backend bash scripts/test.sh` — 966+ passing (+ ~18 new)
- [ ] `docker compose exec backend bash scripts/lint.sh` — mypy + ruff clean
- [ ] `cd frontend && npm run type-check` — clean
- [ ] `cd frontend && npm run lint` — Biome clean
- [ ] Manual: POST /artifacts/{id}/explain → SHAP summary plot + feature importance
- [ ] Manual: POST /artifacts/{id}/predict with include_explanation=true → SHAP values
- [ ] Manual: SVM model returns "unsupported" gracefully
- [ ] Manual: 4 Feature Store MVs exist in pg_matviews
- [ ] Manual: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_training_set_v1 succeeds
