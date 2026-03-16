# Worker Mission: Production Bridge Agent (Workstream C/C+)

**Spec Version:** v1.2
**Dependency:** Workstream A (merge after A — needs emit_event for training events)

## Task
Route model training through Dagger sandbox with MLflow lifecycle tagging and Parquet caching.

## Deliverables
1. **Disposable Script Pattern:** `ModelTrainingAgent` generates standalone Python scripts for Dagger execution instead of calling local sklearn tools.
2. **MLflow Lifecycle Tagging:** Models with Accuracy < 0.5 or F1 < 0.3 tagged `lifecycle: discarded`. Models passing tagged `lifecycle: valid`.
3. **Parquet Row-Count Caching:** `PipelineManager` checks MV row-count; if unchanged, reuse existing `/tmp/` Parquet file.
4. **Dagger-MLflow Bridge:** Every Dagger run accompanied by an MLflow `run_id`.

## Files to Modify
- `backend/app/services/agent/agents/model_training.py` — Disposable Script generation
- `backend/app/services/agent/tools/` — Dagger execution tool updates
- `backend/app/services/lab/pipeline_manager.py` — Parquet caching
- `backend/app/services/lab/mlflow_service.py` — lifecycle tagging

## Constraints
- Do NOT write FastAPI routes, React code, or WebSocket logic.
- Follow `API_CONTRACTS.md` v1.2 for event schemas when emitting training events.
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.
