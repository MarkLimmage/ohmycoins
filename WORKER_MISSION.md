# WORKER MISSION: ENGINE AGENT (PHASE 4)

You are the Engine Agent. You are the sole developer here. Ignore legacy docs.

## Task: Phase 4 (Tracking & Deployment)
Your goal is to update the Dagger sandbox execution environment to log training artifacts and metrics to the MLflow server.

## Key Objectives
1.  **MLflow Integration:** Update `backend/app/services/dagger_service.py` (or equivalent Dagger runner) to use `mlflow.start_run()` inside the sandbox or ensure the sandbox script itself logs to `http://mlflow_server:5000`.
2.  **Artifact Logging:** Ensure the trained model (e.g., XGBoost Booster, Scikit-Learn Pipeline) is logged as an artifact using `mlflow.sklearn.log_model` or equivalent.
3.  **Metric Logging:** Log `f1_score`, `precision`, `recall`, etc., as MLflow metrics.
4.  **Parameter Logging:** Log hyperparameters used in training.

## Constraints
1.  **Strict Contract Adherence:** You must output JSON that matches `API_CONTRACTS.md`. The `render_output` payload for the `EVALUATION` stage must include the `mlflow_run_id` field in the `application/json+tearsheet` mimetype content.
2.  **No FastAPI/React:** Do NOT touch the API routes or frontend code.
3.  **RFC Protocol:** If a contract is impossible, write a `CONTRACT_RFC.md` and halt.

## Context
*   MLflow Tracking URI: `http://localhost:5000` (or `http://mlflow_server:5000` inside Docker).
*   The Dagger pipeline runs inside a container, but it needs network access to the MLflow container. Ensure the Dagger pipeline configuration allows this. 
