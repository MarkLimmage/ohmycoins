# WORKER MISSION: GRAPH AGENT (PHASE 4)

You are the Graph Agent. You are the sole developer here. Ignore legacy docs.

## Task: Phase 4 (Tracking & Deployment)
Your goal is to implement the Model Promotion API in the FastAPI gateway to bridge "The Lab" to "The Floor".

## Key Objectives
1.  **Implement REST API:** Create the `POST /api/v1/algorithms/promote` endpoint as defined in `API_CONTRACTS.md` Section 3.1.
2.  **MLflow Integration:** The endpoint must validate the `mlflow_run_id` exists in the MLflow Tracking Server (http://localhost:5000).
3.  **Business Logic:**
    *   Retrieve the run from MLflow.
    *   Register the model in the MLflow Model Registry (if not already).
    *   Transition the model stage to "Staging" or "Production" based on logic (or default to "Staging").
    *   Return the success response with the new `algorithm_id`.
4.  **Mock Dagger/Glass:** You are only working on the specific API endpoint. You can mock the other parts of the system if needed for local testing.

## Constraints
1.  **Strict Contract Adherence:** The request and response JSON must match `API_CONTRACTS.md` exactly.
2.  **Port:** Your service runs on Port 8000.
3.  **RFC Protocol:** If a contract is impossible, write a `CONTRACT_RFC.md` and halt.

## Context
*   MLflow Tracking URI: `http://localhost:5000`.
