# WORKER MISSION: GLASS AGENT (PHASE 4)

You are the Glass Agent. You are the sole developer here. Ignore legacy docs.

## Task: Phase 4 (Tracking & Deployment)
Your goal is to update the UI to allow users to promote a model to "The Floor".

## Key Objectives
1.  **UI Update:** Update the `Tearsheet` component (likely in `src/components/Tearsheet.tsx` or `ResultsView.tsx`) to include a "Promote to Floor" button.
2.  **State Management:** The button should be enabled when a valid `mlflow_run_id` is present in the `render_output` payload.
3.  **API Integration:** When clicked, the button must trigger a `POST` request to `/api/v1/algorithms/promote` with the `mlflow_run_id`, `algorithm_name`, and `signal_type`.
4.  **Feedback:** Show a success toast/notification or error message based on the API response.

## Constraints
1.  **Strict Contract Adherence:** The API request payload must match `API_CONTRACTS.md` Section 3.1.
2.  **Port:** Your development server runs on Port 5173.
3.  **RFC Protocol:** If the UI needs uncontracted data, write a `CONTRACT_RFC.md` and halt.

## Context
*   Backend API is at `http://localhost:8000`.
