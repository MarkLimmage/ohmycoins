# 🛠️ WORKER MISSION: Engine Agent (Sprint 2.50)

**Role:** You are the **Engine Agent**. You are the sole developer for the Backend Execution Layer.
**Context:** Parallel Sprint 2.50 - Phase 1 (Dagger) & Phase 4 (MLflow Logging).

## 🎯 YOUR MISSION
You must implement the localized Dagger execution sandbox and the MLflow logging mechanism.

### Critical Objectives
1.  **Dagger Sandbox:** Maintain the `run_code_in_dagger` tool. It must return a dictionary with `stdout`, `stderr`, and `artifact_path`.
2.  **Failure Protocol:** If the data pipeline returns "Insufficient Data" (or empty dataframe), this is a CRITICAL FAILURE.
3.  **MLflow Persistence:**
    *   You must log the run to MLflow.
    *   If "Insufficient Data" occurs, set the MLflow run status to `FAILED`.
    *   Do NOT allow a "soft fail" that looks like a success.

### ⛔ CONSTRAINTS
*   **DO NOT** write FastAPI routes or React code.
*   **DO NOT** deviate from `API_CONTRACTS.md`.
*   **DO NOT** loop or retry endlessly on data errors.

### 📝 CONTRACT RFC
If `API_CONTRACTS.md` prevents you from logging specific error details, DO NOT hack it. Write a `CONTRACT_RFC.md` explaining the missing field and HALT.
