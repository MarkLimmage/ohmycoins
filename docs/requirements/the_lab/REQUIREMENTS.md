# 🧬 REQUIREMENTS.md: The Lab 2.0 (v1.3)

## 🔄 DIFF: v1.2 → v1.3 (Conversational Scientific Grid)

* [x] **A+: Event Ledger Implementation:** ✅ COMPLETE — `sequence_id`, `timestamp`, typed events via `emit_event()`.
* [x] **B+: Rehydration Logic:** ✅ COMPLETE — `GET /rehydrate` endpoint, `?after_seq` WebSocket parameter.
* [x] **C+: Dagger-MLflow Bridge:** ✅ COMPLETE — Disposable Script pattern, lifecycle tagging.
* [x] **D+: Statistical Health Gates:** ✅ COMPLETE — Zero-variance kill-switch, 3-cycle circuit breaker.
* [x] **D+: Iteration Circuit Breaker:** ✅ COMPLETE — Per-stage 3-cycle cap.
* [x] **PostgresSaver:** ✅ COMPLETE — Persistent checkpointer (sessions survive restarts).
* [ ] **F: Conversational Pipeline (NEW):** Wire scope confirmation, model selection, reasoning narration, `plan_established`, `POST /message`, circuit breaker → clarification escalation.
* [ ] **G: Scientific Grid UI (NEW):** 3-column layout (Dialogue | Activity | Outputs), event router refactor, ChatInput, rehydration replays all 3 cells.

---

## 1. 🧠 Scientific Orchestration (The Conversational Research Loop)

The Lab operates as a **Conversational Research Loop**. The orchestrator manages a sequence of experiments where each step is narrated to the user, and the user can steer the agent at any point.

### 1.1 The `EventLedger` (Causal State)

The system **shall** maintain an immutable ledger for every session. A state object is only valid if it can be reconstructed from this ledger:

* `sequence_id`: A monotonic integer incremented for every system action.
* `stage`: The DSLC stage (e.g., `MODELING`).
* `event_type`: One of 7 types: `stream_chat`, `status_update`, `render_output`, `error`, `action_request`, `user_message`, `plan_established`.
* `timestamp`: ISO-8601 UTC with millisecond precision.
* `payload`: The structured JSON data (type-specific).

### 1.2 Research Integrity Gates

* **The "Zero Variance" Kill-Switch:** The system **shall** terminate the workflow immediately if `_validate_data_node` detects zero variance in target/features or >90% outliers.
* **The Iteration Cap:** No DSLC stage **shall** exceed 3 reasoning iterations. On the 4th attempt, the system **must** escalate to an `action_request` with `action_id: "circuit_breaker_v1"` presenting the user with recovery options. The system **shall not** emit `TERMINAL_ERROR` for recoverable failures.
* **Mandatory Scope Confirmation:** Every session **must** begin with a `scope_confirmation` interrupt at BUSINESS_UNDERSTANDING. The user explicitly confirms or adjusts the interpreted scope before any data retrieval begins. There is no conditional skip.
* **State Rehydration:** Upon session initialization or reconnection, the backend **shall** return the full `EventLedger` via REST. The frontend replays it through the same event router to reconstruct all three UI cells identically.

### 1.3 The Conversational Contract

* **Agent Narration:** The agent **shall** emit `stream_chat` events at every significant decision point to explain what it is doing and why. The user must never be left guessing.
* **User Messaging:** The user **may** send messages at any time via `POST /message`. The message is persisted as a `user_message` event with an assigned `sequence_id`. The agent's next event **must** be `sequence_id` N+1.
* **Plan Visibility:** After scope confirmation, the agent **shall** emit a `plan_established` event containing the anticipated task list grouped by stage, enabling the Activity Tracker checklist.

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

## 3. 🖥️ Frontend UX: The 3-Column Scientific Grid

The UI is a **Conversational Dashboard of Evidence** — not a flat chat window, not a single-column stage list.

### 3.1 The 3-Column Grid Layout

The Lab session view **shall** be organized as a CSS Grid with 3 columns:

| Column | Width | Component | Routes events from |
|--------|-------|-----------|-------------------|
| Left | 350px | `DialoguePanel` | `stream_chat`, `user_message`, `action_request`, `error` |
| Center | 1fr | `ActivityTracker` | `status_update`, `plan_established` |
| Right | 300px | `StageOutputs` | `render_output` |

### 3.2 Event Routing

* **`stream_chat`** → Left Cell as agent chat bubble.
* **`user_message`** → Left Cell as user chat bubble.
* **`action_request`** → Left Cell as interactive HITL card (scope confirmation, model selection, blueprint approval, circuit breaker).
* **`status_update`** → Center Cell as checklist item update. `status_update` **shall not** create cells or clutter. If `task_id` provided, update existing checklist item; otherwise append.
* **`plan_established`** → Center Cell initializes the master checklist grouped by stage.
* **`render_output`** → Right Cell for the active/selected stage. Uses mime-type dispatcher (markdown, plotly, blueprint, tearsheet, PNG).
* **`error`** → Left Cell as error card.

### 3.3 Human-in-the-Loop (HITL) Controls

The system defines **4 interrupt points** with corresponding `action_request` subtypes:

1. **`scope_confirmation_v1`** (BUSINESS_UNDERSTANDING): Mandatory scope lock — parsed goal, assets, timeframe, questions. Options: CONFIRM_SCOPE, ADJUST_SCOPE.
2. **`approve_modeling_v1`** (MODELING): Blueprint approval — features, algorithm, estimated time. Options: APPROVE, REJECT, EDIT_BLUEPRINT.
3. **`model_selection_v1`** (EVALUATION): Model comparison — metrics, pros/cons, recommendation. Options: SELECT_MODEL, RETRAIN_ALL, SKIP_MODELING.
4. **`circuit_breaker_v1`** (Any stage): Escalation after 3 failed iterations — error context, suggestions. Options: CHOOSE_SUGGESTION, PROVIDE_GUIDANCE, ABORT_SESSION.

### 3.4 ChatInput

* The user **may** send free-text messages to the agent at any time via a text input at the bottom of the Dialogue panel.
* Messages are sent via `POST /api/v1/lab/agent/sessions/{id}/message` and rendered optimistically.

---

## 4. 🌉 Deployment (The Lab-to-Floor Bridge)

* **Promotion Contract:** A model is only eligible for "The Floor" if it exists in the MLflow Registry with a `lifecycle: valid` tag.
* **Signal Isolation:** The Bridge **shall** only pass the model's `weights` and `feature_map`. No execution logic (sizing/orders) is permitted to leave the Lab.

---

## 5. 📜 Contract Reference

All event schemas, payload structures, endpoint definitions, and the 3-Cell routing contract are defined in the root [API_CONTRACTS.md](/API_CONTRACTS.md) (v1.3). That file is the single source of truth for all JSON payloads.
