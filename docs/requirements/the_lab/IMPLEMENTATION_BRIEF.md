# 🛠️ Implementation Brief: "The Lab" (Algo Development Module)

**Version:** 1.2  
**Context:** This document provides the architectural instructions and data contracts required to build "The Lab." Developers and AI Agents must follow these technical patterns strictly to ensure security, state integrity, and real-time frontend synchronization.

## 🔄 DIFF: v1.0 → v1.2

* [ ] **Architecture Layer:** Vue.js → React + Chakra UI + React Query + React Flow.
* [ ] **EventLedger:** Added as 5th architectural pillar — all state must be reconstructable from an immutable event sequence.
* [ ] **Rehydration Protocol:** Added "REST-first, WebSocket-live" initialization sequence for browser-refresh recovery.
* [ ] **`action_request` Event:** Added for HITL approval gates (Approve/Reject/Edit).
* [ ] **Per-Stage Circuit Breaker:** 3-cycle cap per DSLC stage replaces global iteration cap.
* [ ] **Lifecycle Tagging:** MLflow runs tagged `lifecycle: valid` or `lifecycle: discarded` to gate promotion eligibility.
* [ ] **Parquet Caching:** `PipelineManager` caches Parquet exports by MV row count.
* [ ] **Known Limitations:** `MemorySaver` is in-memory only — checkpoints do not survive restarts (Phase 6 migrates to `PostgresSaver`).
* [ ] **Graph Consolidation:** `lab_graph.py` deprecated. `LangGraphWorkflow` is the sole runtime graph.

---

## 1. System Architecture Overview

The Lab operates on a decoupled architecture comprising five pillars:

1. **The Orchestrator:** A FastAPI backend wrapping a LangGraph state machine (`LangGraphWorkflow` in `langgraph_workflow.py`).
2. **The Sandbox:** Ephemeral Dagger containers for executing agent-generated Python using the `omc-agent-base:latest` image.
3. **The Interface:** A React frontend using Chakra UI, React Query, and React Flow for the Scientific Grid.
4. **The Tracker:** A local MLflow instance for artifact versioning and lifecycle tagging.
5. **The EventLedger:** An immutable, monotonically-sequenced log of all system events. The Lab's state is valid only if it can be reconstructed by replaying this ledger.

---

## 2. Backend Implementation (FastAPI + LangGraph)

### 2.1 LangGraph State Machine Definition

The orchestration logic is built using `langgraph`. The canonical runtime graph is `LangGraphWorkflow` in `langgraph_workflow.py`.

> **Note:** `lab_graph.py` exists as a deprecated Phase 2 prototype. It is not used at runtime. See `ROADMAP_STRATEGY.md` Phase 6 for consolidation plan.

* **Graph Nodes:** Define exact nodes for `Business_Understanding`, `Data_Acquisition`, `Preparation`, `Exploration`, `Modeling`, `Evaluation`, and `Deployment`.
* **Graph Edges:** Define conditional edges between nodes. Implement an explicit `interrupt_before` condition prior to the `Modeling` and `Evaluation` nodes to force the "Human-in-the-Loop" approval gate.
* **The "Stale" Mutator:** Implement a state-reducer function. If a payload arrives modifying Node $N$, the reducer must iterate through the `stale_flags` dictionary and set all keys for Nodes > $N$ to `True`.
* **The Self-Healing Edge:** Implement a conditional edge exiting the `Modeling` and `Preparation` nodes. Catch execution exceptions. If the error contains `Exit code 137` (OOM) or a `TimeoutError`, route the graph to a `Remediation` node. This node must append a system prompt to the chat history: "Your code exceeded the 2GB RAM / 300s limit. Optimize your Pandas operations (e.g., use chunking, drop unused columns) and generate a new script."

#### The EventLedger Schema

All agent output must flow through the typed event envelope defined in `lab_schema.py`. The `BaseEvent` Pydantic model **must** include:

```python
class BaseEvent(BaseModel):
    event_type: str          # stream_chat | status_update | render_output | error | action_request
    stage: str               # DSLC stage ID
    sequence_id: int         # Monotonic per session — assigned by the runner
    timestamp: datetime      # ISO-8601 with millisecond precision (UTC)
    payload: dict            # Type-specific content
```

Agents produce events via `BaseAgent.emit_event()`. The `AgentRunner` assigns `sequence_id` and `timestamp` before publishing to Redis and persisting to the database. This is the **single source of truth** for event ordering.

#### The `action_request` Event Type

When the graph hits an `interrupt_before` breakpoint, the runner must emit an `action_request` event:

```json
{
  "event_type": "action_request",
  "stage": "MODELING",
  "sequence_id": 87,
  "timestamp": "2026-03-16T17:14:29.123Z",
  "payload": {
    "action_id": "approve_modeling_v1",
    "description": "Please review the feature set and hyperparameter blueprint.",
    "options": ["APPROVE", "REJECT", "EDIT_BLUEPRINT"]
  }
}
```

The client responds to HITL gates using the existing `POST /api/v1/lab/agent/sessions/{id}/approvals` endpoint — no new endpoint is needed.

#### Per-Stage Circuit Breaker

No DSLC stage shall exceed 3 reasoning iterations. The `AgentState` must include:

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    stage_iteration_counts: dict[str, int]   # e.g., {"MODELING": 2, "PREPARATION": 1}
```

Each node method increments its stage counter. Routing functions check `stage_iteration_counts[stage] >= 3` and trigger either a HITL interrupt or `TERMINAL_ERROR` on the 4th attempt.

#### Known Limitations (Phase 5.5)

> **⚠️ MemorySaver:** Phase 5.5 uses `MemorySaver` (in-memory checkpointer). Checkpoints do not survive process restarts. Sessions paused at HITL gates will require re-execution if the server restarts. Phase 6 migrates to `PostgresSaver` (`langgraph-checkpoint-postgres`). See `ROADMAP_STRATEGY.md` §Phase 6.1.

### 2.2 Initialization & Rehydration Protocol ("REST-first, WebSocket-live")

The Lab must support browser-refresh recovery. The initialization sequence is:

1. **Step 1:** Frontend calls `GET /api/v1/lab/agent/sessions/{id}/rehydrate` (REST). This returns the full `event_ledger` with canonical `sequence_id` values.
2. **Step 2:** Frontend replays the `event_ledger` into the `LabContext` reducer to rebuild the Grid. Records `last_sequence_id`.
3. **Step 3:** Frontend opens the WebSocket connection to `/ws/agent/{session_id}/stream?after_seq={last_sequence_id}`.
4. **Step 4:** The WebSocket endpoint **skips history replay** when `after_seq` is provided. It subscribes only to Redis pub/sub for live events with `sequence_id > after_seq`.
5. **Step 5:** Any WebSocket message with `sequence_id <= last_sequence_id` is discarded client-side as a safety net.

### 2.3 WebSocket Gateway (`/ws/agent/{session_id}/stream`)

The user-to-agent communication layer uses a bi-directional WebSocket connection.

* **Connection Manager:** Implement a connection manager in FastAPI to handle active Lab sessions.
* **Async Streaming:** The LangGraph agent must use async streaming (`astream_events`). Standard LLM text tokens must be routed to the `stream_chat` event type, while tool executions must trigger `status_update` events.
* **`after_seq` Parameter:** If the WebSocket URL includes `?after_seq=N`, skip the `AgentSessionMessage` history replay loop. Only subscribe to Redis for live events. This prevents duplicate messages when the frontend has already rehydrated via REST.

### 2.4 The Pre-Training Leakage Validator

Before the graph transitions into `Modeling`, implement a strict Python validation function in the backend (outside the sandbox).

* **Logic:** Load the temporal index of the feature columns and the target variable. Assert that `max(feature_timestamp) < min(target_timestamp)` for every respective row. If `AssertionError` is raised, halt the graph and emit a warning payload to the frontend.

---

## 3. The Execution Engine (Dagger SDK)

The `execute_sandbox_code` tool must be implemented using the `dagger-io` Python SDK.

### 3.1 Container Instantiation
To ensure sub-second startup latency and strict air-gapped security, the sandbox must use the pre-compiled local image rather than dynamically installing heavy ML libraries on every run.

* **Client Connection:** Wrap the execution in an `async with dagger.Connection()` block.
* **Image Definition:** Chain the `.from_("omc-agent-base:latest")` method to load the pre-baked environment. *(Note: Depending on your local Dagger engine configuration, you may need to explicitly load this from the host Docker daemon).*
* **Dependency Setup:** **Do not** chain any `.with_exec(["pip", "install", ...])` commands. All approved libraries (`scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `ta-lib`, `shap`) are already compiled inside the base image. Dynamic package installation by the agent is strictly prohibited.

### 3.2 The "Disposable Script" Pattern

The agent **shall** generate a standalone, self-contained Python training script as a disposable artifact. This script is injected into the Dagger container and executed in isolation:

1. The agent generates the full script as a string (including imports, data loading from `/data/`, model training, metric output, and artifact saving to `/workspace/out/`).
2. The `ModelTrainingAgent` passes the script to `run_code_in_dagger()` — it never calls sklearn/xgboost directly in the FastAPI process.
3. Every Dagger execution **must** be accompanied by an MLflow `run_id`. The Dagger tool logs params, metrics, and artifacts to MLflow automatically.

### 3.3 The Data Mount Pipeline (with Parquet Caching)

To ensure air-gapped security, the sandbox must never connect to Postgres.

1. **Extraction:** When the agent requests data, the FastAPI backend must query the `mv_training_set_v1` materialized view via SQLAlchemy.
2. **Serialization:** Use Pandas to save the query result to a local `.parquet` file in a session-specific temporary directory on the host.
3. **Mounting:** Use Dagger's `.with_directory()` method to mount this temporary host directory into the container at `/data`.

#### Parquet Caching (`PipelineManager`)

The `PipelineManager.export_mv_to_parquet()` method must implement row-count caching to eliminate redundant re-exports:

* On each call, execute a fast `COUNT(*)` query against the MV.
* If a cached Parquet exists and the row count matches, return the cached path immediately (**cache hit**).
* If the row count differs, re-export the full MV to Parquet (**cache miss**).
* Provide an `invalidate_cache()` method for explicit cache busting (e.g., after MV refresh).

### 3.4 Execution and Artifact Retrieval

* Inject the agent's Python code using `.with_new_file("/src/run.py", contents=code)`.
* Execute via `.with_exec(["python", "/src/run.py"])`.
* **Limits:** Apply a 300-second timeout to the `with_exec` call.
* **Retrieval:** Await `.stdout()` for terminal logs. If the script generates models or plots, use `.file("/workspace/out/artifact.ext").export(...)` to pull them back to the host before the container terminates.
* **Exception Handling:** Wrap the `.with_exec()` call in a `try/except` block catching Dagger's `ExecError`. Parse the stderr/exit code specifically to identify resource exhaustion vs. standard Python syntax errors.
---

## 4. Frontend Implementation (React + Chakra UI)

### 4.1 The Scientific Grid (Causal Grid Architecture)

The Lab UI is a **Dashboard of Evidence**, organized as a vertical grid of stage-isolated cells.

* **Stage Isolation:** Each DSLC stage occupies a discrete "Cell" in the grid. Cells are stored as `Map<StageID, LabCell[]>` — not a flat list. Each stage accumulates its own ordered sequence of events.
* **State-Driven Visibility:** A cell only becomes visible when its first `status_update` event is received. Pending stages remain hidden.
* **Sequence-ID Ordering:** Within each stage group, cells are sorted by `sequence_id` (ascending). Messages arriving out of order (with `sequence_id` lower than the client's current max) are discarded.

### 4.2 React Flow Integration (The State Map)

* Mount a React Flow component fixed at the top of the Lab view.
* Bind the node data to a reactive state object that updates whenever a `status_update` WebSocket payload is received.
* **Styling Contract:** Apply CSS classes dynamically: `node-healthy` (Green) for completed stages, `node-stale` (Amber) for stages requiring re-run, `node-active` (Blue/Pulsing) for the currently executing node, and `node-awaiting` (Orange) for `AWAITING_APPROVAL` status.

### 4.3 Mime-Type Dispatcher (Output Panel)

The UI **shall** use the `mime_type` field in `render_output` events to select the rendering component:

| Mime-Type | React Component | Rendering |
|-----------|----------------|-----------|
| `text/markdown` | Markdown renderer | Logs, reports |
| `application/vnd.plotly.v1+json` | Plotly React wrapper | Interactive charts |
| `application/json+blueprint` | `BlueprintCard` | Target/feature/algorithm summary |
| `application/json+tearsheet` | `Tearsheet` | Metrics, F1, assumed PnL, MLflow link |
| `image/png` | `<img>` with Base64 `src` | Static plots |

### 4.4 Rehydration Hook (`useRehydration`)

On component mount, the frontend must execute the "REST-first, WebSocket-live" initialization sequence:

1. Call `GET /api/v1/lab/agent/sessions/{id}/rehydrate` via React Query.
2. Replay the returned `event_ledger` into the `LabContext` reducer to rebuild the Grid.
3. Store `last_sequence_id` from the response.
4. Pass `last_sequence_id` to `useLabWebSocket()`, which appends `?after_seq={last_sequence_id}` to the WebSocket URL.
5. **Ordering constraint:** `useRehydration()` **must** complete before `useLabWebSocket()` opens the connection. This is enforced by passing `enabled: rehydrationComplete` to the WebSocket hook.

### 4.5 HITL Action Rendering

* **Interrupt Rendering:** When the WebSocket delivers `event_type: "action_request"` or `status: "AWAITING_APPROVAL"`, render high-contrast Approve/Reject/Edit buttons within the active stage cell.
* **Response:** User clicks send a `POST /api/v1/lab/agent/sessions/{id}/approvals` request. The backend resumes the checkpointed graph.

### 4.6 Model Discarded UI

* **Disable Promote:** When the tearsheet contains `lifecycle: "discarded"`, disable the "Promote to Floor" button.
* **Warning:** Render a high-visibility warning: "Model discarded: performance below minimum thresholds."

### 4.7 Cached Parquet Badge

* When a `status_update` indicates a Parquet cache hit, display a "Using Cached Data" badge on the `DATA_ACQUISITION` cell.

### 4.8 Hyperparameter Overlay

* If the `render_output` payload contains a `hyperparameters` object, render HTML range sliders bound to those values.
* Emitting a change to a slider must send a re-evaluation request back over the WebSocket.

### 4.9 Code Panel

* Implement a syntax-highlighting code viewer (e.g., using Monaco Editor or PrismJS).
* Wrap it in an accordion/disclosure widget defaulting to `collapsed=true`.
* Populate from the optional `code_snippet` field in `render_output` payloads.

---

## 5. Integration: MLflow & The Floor

### 5.1 Artifact Logging

* Upon the successful completion of the `Evaluation` stage, the FastAPI backend must utilize the `mlflow` Python client.
* Call `mlflow.start_run()`.
* Log the hyperparameter dictionary using `mlflow.log_params()`.
* Log the F1-Score, RMSE, or other metrics using `mlflow.log_metrics()`.
* Log the Dagger-exported `.pkl` model using `mlflow.sklearn.log_model()` or `mlflow.xgboost.log_model()`.

### 5.2 Lifecycle Tagging

After evaluation, the MLflow run **must** be tagged to control promotion eligibility:

* **`lifecycle: valid`** — Models with Accuracy ≥ 0.5 AND F1 ≥ 0.3. Only these models are eligible for promotion to The Floor.
* **`lifecycle: discarded`** — Models with Accuracy < 0.5 OR F1 < 0.3. These runs are excluded from the Model Registry. The workflow routes to `finalize` with a descriptive error instead of proceeding to deployment.

```python
# After evaluation:
if accuracy >= 0.5 and f1 >= 0.3:
    mlflow.set_tag("lifecycle", "valid")
else:
    mlflow.set_tag("lifecycle", "discarded")
    mlflow.set_tag("discard_reason", f"accuracy={accuracy:.3f}, f1={f1:.3f}")
```

### 5.3 The Deployment Bridge

When the user clicks "Promote to Floor" in the UI:

1. The frontend sends a REST `POST` to `/api/v1/algorithms/promote`.
2. The backend queries MLflow to retrieve the `run_id` and the artifact URI.
3. **The backend verifies the run has `lifecycle: valid` before proceeding.** If the tag is `discarded` or missing, return 403 Forbidden.
4. The backend inserts a new row into the `Algorithm` database table containing: `name`, `mlflow_run_id`, `signal_type` (from the Blueprint), and `status = 'INACTIVE'`.
5. The backend returns a 201 Created, handing over responsibility to the Live Trading Floor UI.

---

## 6. Critical Data Contracts (JSON Payloads)

To prevent parsing errors between the agent, backend, and frontend, all WebSocket messages from the backend to the frontend must adhere to the v1.2 envelope defined in `API_CONTRACTS.md`:

```json
{
  "event_type": "status_update | stream_chat | render_output | error | action_request",
  "stage": "MODELING",
  "sequence_id": 142,
  "timestamp": "2026-03-16T17:14:29.123Z",
  "payload": {
    // For stream_chat
    "text_delta": "...",

    // For status_update
    "status": "PENDING | ACTIVE | COMPLETE | STALE | AWAITING_APPROVAL",

    // For render_output
    "mime_type": "text/markdown | application/vnd.plotly.v1+json | image/png | application/json+blueprint | application/json+tearsheet",
    "content": "...",
    "hyperparameters": {"learning_rate": 0.05},

    // For action_request
    "action_id": "approve_modeling_v1",
    "description": "...",
    "options": ["APPROVE", "REJECT", "EDIT_BLUEPRINT"],

    // For error
    "code": "TERMINAL_DATA_ERROR",
    "message": "...",
    "details": {}
  }
}
```

> **Compliance Rule:** Every event published by the runner must include `sequence_id` (int, monotonic per session) and `timestamp` (ISO-8601 UTC with millisecond precision). Events missing these fields are non-compliant and must be rejected by the frontend.

---

### 🚀 Next Step

The engineering team now has the structural map they need.

**Would you like me to draft the final `Roadmap_strategy.md` document next?** This will break this massive implementation into logical, executable sprints so the agentic dev team knows exactly which components to build first without creating dependency bottlenecks.