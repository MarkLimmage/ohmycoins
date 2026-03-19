# 🧬 REQUIREMENTS.md: The Lab 2.0 (v1.3 — Conversational Scientific Grid)

## 🔄 DIFF: v1.2 → v1.3

**Completed (Workstreams A–E):**
* [x] **A+: Event Ledger** — Immutable `EventLedger` with `sequence_id` COMPLETE.
* [x] **B+: Rehydration** — `GET /rehydrate` + `?after_seq` dedup COMPLETE.
* [x] **C+: Dagger-MLflow Bridge** — Disposable Script, lifecycle tagging COMPLETE.
* [x] **D+: Health Gates** — Zero-variance kill-switch, circuit breaker COMPLETE.
* [x] **Phase 6:** PostgresSaver migration, graph consolidation COMPLETE.

**New in v1.3 (Phase 7 — Conversational Grid):**
* [ ] **Mandatory Scope Confirmation:** `action_request` with `scope_confirmation_v1` at session start. No conditional skip.
* [ ] **Agent Narration:** Every LangGraph node emits `stream_chat` with reasoning.
* [ ] **User Messaging:** `POST /message` → `sequence_id` N, agent response at N+1. New `user_message` event type.
* [ ] **Plan Established:** New event type after scope confirmation with task checklist.
* [ ] **Model Selection Gate:** `action_request` with `model_selection_v1` for model comparison.
* [ ] **Circuit Breaker Escalation:** 3-cycle cap → `action_request` with `circuit_breaker_v1` (not TERMINAL_ERROR).
* [ ] **3-Column Grid:** Dialogue (Left) | Activity (Center) | Outputs (Right).

---

## 1. 🧠 Scientific Orchestration (The Science Loop)

The Lab operates as an **Autonomous Research Loop**. The orchestrator manages a sequence of experiments, where each step must produce a verifiable "Scientific Record."

### 1.1 The `EventLedger` (Causal State)

The system **shall** maintain an immutable ledger for every session. A state object is only valid if it can be reconstructed from this ledger:

* `sequence_id`: A monotonic integer incremented for every system action.
* `stage`: The DSLC stage (e.g., `MODELING`).
* `event_type`: `stream_chat`, `status_update`, `render_output`, `error`, `action_request`, `user_message`, `plan_established`.
* `payload`: The structured JSON data (Mime-Type compliant).
* `timestamp`: ISO-8601 UTC with millisecond precision.

### 1.2 Research Integrity Gates

* **The "Zero Variance" Kill-Switch:** The system **shall** terminate the workflow immediately if `_validate_data_node` detects zero variance in target/features or >90% outliers.
* **The Iteration Cap:** No DSLC stage **shall** exceed 3 reasoning iterations. On the 4th attempt, the system **must** emit an `action_request` with `action_id: "circuit_breaker_v1"` containing error context, suggestions, and options (CHOOSE_SUGGESTION, PROVIDE_GUIDANCE, ABORT_SESSION). Only truly unrecoverable errors (zero variance, sandbox crash) produce `error` events.
* **State Rehydration:** Upon session initialization or reconnection, the backend **shall** replay the `EventLedger` to the frontend to ensure the Grid UI reflects the exact historical causality of the research.

---

## 2. 🛡️ The Execution Sandbox (Dagger + MLflow)

The sandbox is the "Lab Bench." It must be isolated, tracked, and optimized for high-volume iteration.

### 2.1 The "Disposable Script" Pattern

* **Script Generation:** The Agent **shall** generate a standalone Python script for training. This script is a disposable artifact, not part of the core codebase.
* **MLflow Lineage:** Every Dagger run **must** be accompanied by an MLflow `run_id`.
* **Lifecycle Tagging:** Models with Accuracy < 0.5 or F1 < 0.3 **shall** be tagged `lifecycle: discarded` in MLflow to prevent registry pollution.
* **Promotion Eligibility:** Models with Accuracy >= 0.5 AND F1 >= 0.3 **shall** be tagged `lifecycle: valid` upon passing the evaluation gate. Only models with `lifecycle: valid` are eligible for promotion to The Floor.

### 2.2 Performance Optimization (Parquet Caching)

* **Cold-Start Mitigation:** The `PipelineManager` **shall** implement row-count caching. If the Materialized View row-count is unchanged, Dagger **must** reuse the existing Parquet file from `/tmp/`.

---

## 3. 🖥️ Frontend UX: The Scientific Grid

The UI is a **Dashboard of Evidence**, not a chat window.

### 3.1 The Grid Layout

* **3-Column Layout:** The Lab session renders as a CSS Grid: Dialogue (350px) | Activity Tracker (1fr) | Stage Outputs (300px).
* **Left Cell (Dialogue):** Routes `stream_chat`, `user_message`, `action_request`, `error`. Shows agent narration, user messages, and HITL cards.
* **Center Cell (Activity):** Routes `status_update`, `plan_established`. Master checklist of tasks grouped by stage.
* **Right Cell (Outputs):** Routes `render_output`. Mime-type-dispatched artifacts for the active/selected stage.
* **Mime-Type Dispatcher:** Uses `mime_type` in event payload to render Markdown, Plotly charts, Blueprint cards, or Tear Sheets.

### 3.2 Human-in-the-Loop (HITL) Controls

4 mandatory interrupt points with `action_request` rendering:

| Interrupt | Stage | action_id | Options |
|-----------|-------|-----------|----------|
| Scope Confirmation | BUSINESS_UNDERSTANDING | `scope_confirmation_v1` | CONFIRM_SCOPE, ADJUST_SCOPE |
| Blueprint Approval | MODELING | `approve_modeling_v1` | APPROVE, REJECT, EDIT_BLUEPRINT |
| Model Selection | EVALUATION | `model_selection_v1` | Radio select + CONFIRM |
| Circuit Breaker | Any (after 3 failures) | `circuit_breaker_v1` | CHOOSE_SUGGESTION, PROVIDE_GUIDANCE, ABORT_SESSION |

### 3.3 Conversational Interface

* **ChatInput:** Text input at the bottom of the Dialogue panel. Sends via `POST /message`, response at `sequence_id` N+1.
* **Agent Narration:** Every node emits `stream_chat` with human-readable reasoning. No silent processing.

### 3.4 Enforcement Rules (v1.3.1 — from Production Testing)

These requirements were implicit in v1.3 but violated during Sprint 2.51. They are now mandatory acceptance criteria.

* **No Silent Fallbacks:** If any LLM call fails, the backend **shall** escalate via `action_request` with `circuit_breaker_v1`. It **shall not** emit a stub `stream_chat` with fallback text and continue silently. A silent fallback cascades: no scope confirmation → no plan → empty Activity Tracker → broken HITL.
* **Node Events Take Priority:** When a LangGraph node emits structured `pending_events` (e.g., `scope_confirmation_v1`), the runner **shall** publish those events. The runner **shall not** emit a duplicate generic `action_request` (e.g., `approve_reason`) that conflicts with or overwrites the node's structured event.
* **`task_id` Mandatory on `status_update`:** Every `status_update` payload **shall** include a `task_id` field matching the `plan_established` task list. Updates without `task_id` cannot be matched to checklist items and create orphan entries in the Activity Tracker.
* **`plan_established` Always Emitted:** The backend **shall** emit `plan_established` even when scope confirmation fails or is bypassed. A default/simplified plan **shall** be used as fallback. The Activity Tracker is non-functional without it.
* **Sequence Deduplication:** The frontend **shall** track `max_seen_sequence_id` and discard events with `sequence_id ≤ max_seen_sequence_id`. This prevents duplicate messages during rehydration/WS overlap and reconnection.
* **Inline HITL Only:** All HITL interactions **shall** render as inline `action_request` cards in the Dialogue panel. No standalone buttons, banners, or modals outside the Dialogue. The legacy "Resume Workflow (HITL)" button is deprecated.
* **Pipeline Node Colors:** COMPLETE = green (`#38A169`), ACTIVE = blue (`#3182CE` with bold + box-shadow), PENDING = gray (`#EDF2F7`). Yellow is not a valid stage color.
* **ChatInput Enabled:** The Dialogue text input **shall** be enabled during RUNNING and AWAITING_APPROVAL sessions. It **shall** be disabled only for COMPLETED, FAILED, or CANCELLED.
* **Stage Outputs Selection:** The Right Cell **shall** display outputs for the user-selected stage (via pipeline click) or the most recently active stage. It **shall not** be hardcoded to a single stage.

---

## 4. 🌉 Deployment (The Lab-to-Floor Bridge)

* **Promotion Contract:** A model is only eligible for "The Floor" if it exists in the MLflow Registry with a `lifecycle: valid` tag.
* **Signal Isolation:** The Bridge **shall** only pass the model's `weights` and `feature_map`. No execution logic (sizing/orders) is permitted to leave the Lab.





# For REFERENCE ONLY - OLD REQUIREMENTS VERSION
## 🔬 Requirements Specification: "The Lab" (Algo Development Module)

**Version:** 1.1 (Updated Post-Review)
**Context:** This module provides an interactive, agent-assisted Data Science Life Cycle (DSLC) environment. It sits between the Data Collectors (Materialized Views) and the Live Trading Platform ("The Floor").

## 1. 🧠 Core Orchestration (LangGraph State Machine)

The Lab operates as a directed state graph. The dev team must implement the orchestration layer to strictly manage transitions between these states.

### 1.1 The `DSLCState` Object

The system **shall** maintain a persistent state object for every Lab Session containing:

* `session_id` (UUID)
* `current_stage` (Enum: `BUSINESS_UNDERSTANDING`, `DATA_ACQUISITION`, `PREPARATION`, `EXPLORATION`, `MODELING`, `EVALUATION`, `DEPLOYMENT`)
* `chat_history` (List of user/agent messages)
* `artifacts` (Dict mapping stages to output file paths or MLflow URIs)
* `stale_flags` (Dict mapping stages to Boolean values)

### 1.2 State Transitions & The "Stale" Protocol

* **Sequential Enforcement:** The agent **shall not** execute a stage if its immediate preceding stage is incomplete or marked as stale.
* **Upstream Invalidation:** **If** the user modifies the output or code of Stage $N$, the system **shall** automatically set the `stale_flags` for all Stages > $N$ to `True`.
* **Approval Gates:** The LangGraph implementation **shall** contain a `Human_in_the_Loop` interrupt node before transitioning from `EXPLORATION` to `MODELING`, and `MODELING` to `EVALUATION`.
* **Self-Healing Loop:** **If** the Dagger execution engine returns a hardware limit error (Out of Memory or Timeout), the LangGraph orchestrator shall feed the error back to the agent for code optimization before surfacing a terminal error to the user. The system shall allow a maximum of 2 retry attempts.

### 1.3 Automated Validation (The Leakage Guard)

* **Pre-Training Check:** Before entering the `MODELING` stage, the system **shall** automatically run a validation script against the prepped data to detect label leakage (e.g., overlapping time windows between target variables and features).

---

## 2. 🛡️ The Execution Sandbox (Dagger integration)

No agent-generated data science code shall run on the host FastAPI process.

### 2.1 Container Lifecycle & Specifications

* **Base Image:** The system **shall** construct Dagger containers using a pre-baked, local Docker image tagged `omc-agent-base:latest`.
* **Pre-loaded Toolchains:** The omc-agent-base image **shall** contain `scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `ta-lib`, and `shap`. Dynamic `pip install` commands within the sandbox are strictly prohibited.
* **Ephemeral Nature:** Containers **shall** be destroyed immediately upon task completion, failure, or timeout.

### 2.2 Data Ingestion & Volume Mounting

* **MV to Parquet Pipeline:** **When** the `DATA_ACQUISITION` stage executes, the FastAPI backend **shall** query the requested Materialized View, export the result to a local `.parquet` file, and mount *only* that file into the Dagger container.
* **Database Isolation:** The Dagger container **shall not** possess database connection strings or drivers.
* **Write-Only Artifact Store:** The container **shall** have access to a specific `/workspace/out` directory to write trained models (`.pkl`) and visual plots (`.json`/`.png`).

---

## 3. 🤖 AI Agent Capabilities & Tools

### 3.1 The "Model Blueprint" Generation

* **When** in the `BUSINESS_UNDERSTANDING` stage, the agent **shall** output a structured JSON schema (The Blueprint) containing:
* `target_variable` (e.g., `target_return_1h`)
* `feature_list` (e.g., `['volatility_24h', 'sentiment_1h']`)
* `ml_task_type` (Enum: `CLASSIFICATION`, `REGRESSION`)
* `hyperparameters` (Dict of model-specific tuning parameters)



### 3.2 Agent Tool Bindings

The dev team must expose the following internal APIs to the LangGraph agent:

* `extract_feature_store(query_params)`: Triggers the MV-to-Parquet pipeline.
* `execute_sandbox_code(code: str)`: Sends Python code to Dagger and returns `stdout`, `stderr`, and artifact URIs.
* `log_to_mlflow(metrics: dict, params: dict, model_path: str)`: Pushes execution results to the local experiment tracker.

---

## 4. 🖥️ Frontend UX & Communication Protocol (React + FastAPI)

### 4.1 Low-Code Overlays & Code Abstraction

* **Hyperparameter Tuning UI:** **If** the agent generates a Blueprint with `hyperparameters` (e.g., XGBoost `learning_rate`), the UI **shall** render these as visual sliders/inputs, allowing the user to adjust them without editing the underlying Python script.
* **Code Collapsibility:** The Python code generated by the agent **shall** be placed in a collapsible accordion panel within the cell, defaulting to "Closed".

### 4.2 Standardized Insight Rendering (Result-First UI)

* **Structured Visuals:** **If** the agent executes code that generates a chart, the backend **shall** return a Plotly-compatible JSON object or Base64 image string, which the React component **shall** render natively.
* **The "Tear Sheet":** In the `EVALUATION` stage, the UI **shall** render a standardized metric card (The Tear Sheet) displaying the model's out-of-sample performance (e.g., Accuracy, Precision, assumed P&L).

### 4.3 Visual State Graph

* **Status Map:** A linear graph node display (e.g., using React Flow) **shall** persist at the top of the workspace.
* **Real-time Sync:** The backend **shall** push WebSocket events (`status_update`) to instantly color-code nodes (Green = Healthy, Amber = Stale, Blue = In Progress).

---

## 5. 🌉 Deployment (The Lab-to-Floor Bridge)

### 5.1 Promotion Contract

* **When** a user clicks "Promote to Floor" in the `DEPLOYMENT` stage, the system **shall**:
1. Verify the model exists in the MLflow Model Registry with a "Production" tag.
2. Create a new record in the `Algorithm` database table.
3. Link the `Algorithm` record to the specific `mlflow_run_id` to maintain data lineage.


* **Separation of Concerns:** The deployed model artifact **shall only** emit predictive signals (e.g., `[Buy: 0.85]`). It **shall not** contain execution logic (e.g., position sizing or Coinspot API calls), which remains the strict domain of The Floor.

---

## 6. 🛑 Non-Functional Security & Performance Guardrails

### 6.1 Resource Constraints

* **Timeout:** Any single agent code execution inside the Dagger sandbox **shall** be terminated if it exceeds **300 seconds**.
* **Memory:** The Dagger container **shall** be hard-capped at **2GB RAM** (adjustable via `.env`).

### 6.2 Air-Gap Security

* **Network Isolation:** During `PREPARATION`, `EXPLORATION`, and `MODELING`, the Dagger container **shall** have external internet access disabled.
* **Credential Blacklist:** Real-world trading credentials **shall never** be mounted, passed, or accessible to The Lab's execution environment.

