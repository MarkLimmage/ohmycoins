# Phase 5 Integration Plan: Agent Service Hardening

**Version:** 1.2  
**Status:** Pre-Implementation  
**Prerequisite:** Phases 0–4 complete per `ROADMAP_STRATEGY.md`  
**Reference Audit:** `backend/app/services/agent/ARCHITECTURE.md`

## 🔄 DIFF: v1.1 → v1.2

* [ ] **Workstream A+:** `BaseEvent` now includes `sequence_id` (int) and `timestamp` (ISO-8601). New `ActionRequestEvent` Pydantic model added to `lab_schema.py`.
* [ ] **Workstream B+:** Added `GET /api/v1/lab/agent/sessions/{id}/rehydrate` REST endpoint. WebSocket gains `?after_seq` query parameter to skip history replay. MemorySaver limitation documented.
* [ ] **Workstream D+:** Global 10-iteration cap replaced with per-stage 3-cycle circuit breaker using `stage_iteration_counts: dict[str, int]`.
* [ ] **Workstream E (NEW):** Frontend remediation — 7 sub-items covering Causal Grid, sequence-ID ordering, rehydration hook, mime-type dispatcher, HITL rendering, Model Discarded UI, Cached Parquet badge.
* [ ] **Dependency Graph:** Updated — E depends on A+B completion.
* [ ] **Risk Register:** Added MemorySaver data loss, rehydration race condition, frontend state management complexity.
* [ ] **Testing Strategy:** Added 4 Integration Gate tests.

---

## 1. Problem Statement

The agent service audit (`ARCHITECTURE.md`) reveals three systemic gaps that prevent the Lab from meeting its requirements:

| # | Gap | Impact | Requirements Violated |
|---|-----|--------|-----------------------|
| 1 | Agents append raw dicts to state instead of using the typed event envelope from `lab_schema.py` | Frontend cannot distinguish chat text from structured artifacts (blueprints, tearsheets, plots) — the UI renders everything as flat text | `REQUIREMENTS.md` §4.2 (Structured Visuals), `API_CONTRACTS.md` §1.2C (`render_output`) |
| 2 | `AgentRunner` uses bare `workflow.compile()` with no checkpointer or interrupt gates, despite `lab_graph.py` already defining both | HiTL approval gates are never enforced — the workflow runs straight through without waiting for user approval | `REQUIREMENTS.md` §1.2 (Approval Gates), `IMPLEMENTATION_BRIEF.md` §2.1 (`interrupt_before`) |
| 3 | `ModelTrainingAgent` calls local sklearn tools (`train_classification_model`) that never log to MLflow | Trained models are ephemeral — no experiment tracking, no artifact registry, no "Promote to Floor" lineage | `REQUIREMENTS.md` §5 (Evaluation & MLflow), `USER_STORIES.md` Epic 5.2 (Silent Artifact Logging) |

These three gaps must be resolved before the Phase 5 hardening work (air-gap, HP overlays, graceful degradation) can proceed, because Phase 5 assumes the messaging, state, and persistence layers are functional.

> **v1.1 — Hardening Upgrades:** Each workstream now includes a companion "+" upgrade that addresses resilience, performance, data quality, and event ordering concerns discovered during integration testing. These upgrades are denoted **A+**, **B+**, **C+**, and **D+** and are scoped within their parent workstream.

---

## 2. Workstream A — Upgrade the Messaging Layer ("Flat UI" Fix)

### 2.1 Diagnosis

The `lab_schema.py` file already defines the correct event types:

```
StatusUpdateEvent  →  { event_type: "status_update", payload: StatusUpdatePayload }
RenderOutputEvent  →  { event_type: "render_output", payload: RenderOutputPayload }
StreamChatEvent    →  { event_type: "stream_chat",   payload: StreamChatPayload }
ErrorEvent         →  { event_type: "error",         payload: ErrorPayload }
```

However, no agent is required to use them. Each specialised agent (`DataAnalystAgent`, `ModelTrainingAgent`, etc.) currently returns plain dicts from `execute()`, and the `LangGraphWorkflow` node methods merge those dicts directly into `AgentState`. The `AgentRunner._run()` method then attempts to classify the output for Redis pub/sub, but the classification is ad-hoc and fragile.

### 2.2 Changes Required

#### 2.2.1 Add `emit_event()` helper to `BaseAgent`

**File:** `backend/app/services/agent/agents/base.py`

Add a method that forces all agent output to comply with the `API_CONTRACTS.md` §1 envelope:

```python
class BaseAgent:
    def emit_event(self, event_type: str, stage: str, payload: dict) -> dict:
        """Wrap agent output in the standard event envelope.

        Forces compliance with API_CONTRACTS.md §1 and lab_schema.py event models.
        Note: sequence_id and timestamp are assigned by the runner, not by the agent.
        """
        return {
            "event_type": event_type,
            "stage": stage,
            "payload": payload,
            "agent_name": self.name,
        }
```

This does not change the return type of `execute()`. It provides a builder that agents call internally to construct properly typed events that the runner can relay verbatim.

#### 2.2.2 Update each agent to use `emit_event()`

For every specialised agent, wrap structured outputs with the envelope. The key transitions:

| Agent | Current Output Key | New Event Type | Payload Content |
|-------|-------------------|------|-----------------|
| `DataRetrievalAgent` | `retrieved_data` (raw dict) | `status_update` | `{ "status": "COMPLETE", "message": "Retrieved N records" }` |
| `DataAnalystAgent` | `analysis_results` (raw dict) | `render_output` | `{ "mime_type": "application/vnd.plotly.v1+json", "content": <plotly_json> }` |
| `ModelTrainingAgent` | `trained_models` (raw dict) | `render_output` | `{ "mime_type": "application/json+blueprint", "content": <blueprint_json> }` |
| `ModelEvaluatorAgent` | `evaluation_results` (raw dict) | `render_output` | `{ "mime_type": "application/json+tearsheet", "content": <tearsheet_json> }` |
| `ReportingAgent` | `reporting_results` (raw dict) | `render_output` | `{ "mime_type": "text/markdown", "content": <report_md> }` |

Agents continue to set their existing state keys for internal workflow routing. The `emit_event()` output is appended to a new `pending_events` list in `AgentState` that the runner drains and publishes.

#### 2.2.3 Add `pending_events` to `AgentState`

**File:** `backend/app/services/agent/langgraph_workflow.py`

Add to the `AgentState` TypedDict:

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    pending_events: list[dict]   # Queue of enveloped events for the runner to drain
```

#### 2.2.4 Update `AgentRunner._run()` to drain events

**File:** `backend/app/services/agent/runner.py`

After each graph step, drain `pending_events` from the state and publish each one verbatim to the Redis pub/sub channel. Remove the ad-hoc event classification logic currently in `_run()`.

```python
# After each streamed state update:
for event in state.get("pending_events", []):
    await self._publish(redis, channel, event)
state["pending_events"] = []
```

### 2.3 Acceptance Criteria

- [ ] Every `render_output` event reaching the frontend matches the `API_CONTRACTS.md` §2.1 schema exactly.
- [ ] The `mock_ws_server.py` (DevOps Protocol §3) can be replaced by recording actual backend output — schemas must be identical.
- [ ] Blueprint cards render as structured UI components, not raw JSON text.
- [ ] Tearsheet cards render with metric visualisations.
- [ ] **[A+]** Every event envelope includes `sequence_id` (int, monotonic per session) and `timestamp` (ISO-8601 UTC).
- [ ] **[A+]** `ActionRequestEvent` is a valid Pydantic model in `lab_schema.py` with `action_id`, `description`, and `options` fields.

### 2.4 [A+] `BaseEvent` v1.2 Upgrade & `ActionRequestEvent`

#### 2.4.1 Update `BaseEvent` in `lab_schema.py`

**File:** `backend/app/services/agent/lab_schema.py`

The `BaseEvent` Pydantic model must include `sequence_id` and `timestamp` per `API_CONTRACTS.md` §1:

```python
from datetime import datetime

class BaseEvent(BaseModel):
    event_type: str
    stage: str
    sequence_id: int = 0        # Assigned by the runner, not by the agent
    timestamp: datetime = None   # Assigned by the runner at publish time
    payload: dict
```

#### 2.4.2 Add `ActionRequestEvent` model

**File:** `backend/app/services/agent/lab_schema.py`

```python
class ActionRequestPayload(BaseModel):
    action_id: str
    description: str
    options: list[str]

class ActionRequestEvent(BaseEvent):
    event_type: str = "action_request"
```

#### 2.4.3 Runner assigns `sequence_id` and `timestamp`

**File:** `backend/app/services/agent/runner.py`

The runner maintains a per-session counter. Before publishing any event to Redis or persisting to the database:

```python
from datetime import datetime, timezone

self._seq_counter += 1
event["sequence_id"] = self._seq_counter
event["timestamp"] = datetime.now(timezone.utc).isoformat()
```

### 2.5 Files Modified

| File | Nature of Change |
|------|-----------------|
| `backend/app/services/agent/agents/base.py` | Add `emit_event()` method |
| `backend/app/services/agent/agents/data_retrieval.py` | Call `emit_event()` for status updates |
| `backend/app/services/agent/agents/data_analyst.py` | Call `emit_event()` for Plotly/analysis output |
| `backend/app/services/agent/agents/model_training.py` | Call `emit_event()` for blueprint output |
| `backend/app/services/agent/agents/model_evaluator.py` | Call `emit_event()` for tearsheet output |
| `backend/app/services/agent/agents/reporting.py` | Call `emit_event()` for markdown report output |
| `backend/app/services/agent/langgraph_workflow.py` | Add `pending_events` to `AgentState` |
| `backend/app/services/agent/runner.py` | Drain `pending_events` instead of ad-hoc classification; assign `sequence_id` and `timestamp` |
| `backend/app/services/agent/lab_schema.py` | **[A+]** Add `sequence_id` and `timestamp` to `BaseEvent`; add `ActionRequestEvent` model |

---

## 3. Workstream B — Implement HiTL Breakpoints ("Looping" Fix)

### 3.1 Diagnosis

Two parallel graph implementations exist:

| Graph | File | Checkpointer | Interrupts | Used by Runner? |
|-------|------|-------------|------------|-----------------|
| `LangGraphWorkflow` | `langgraph_workflow.py` | **None** | **None** | **Yes** |
| `lab_graph` (`app`) | `lab_graph.py` | `MemorySaver` | `interrupt_before=[PREPARATION, MODELING]` | **No** |

The `AgentRunner` exclusively uses `LangGraphWorkflow`, which compiles the graph with bare `workflow.compile()` at line 302. The `lab_graph.py` graph with its `MemorySaver` checkpointer and interrupt gates is orphaned — nothing calls it at runtime.

Additionally, `_route_after_error` correctly routes to `END` when `retry_count > max_retries`, but the routing logic for _data insufficiency_ (when retrieved data is too sparse to train on) does not exist — the workflow just retries the same data fetch.

### 3.2 Changes Required

#### 3.2.1 Add checkpointer and interrupts to `LangGraphWorkflow._build_graph()`

**File:** `backend/app/services/agent/langgraph_workflow.py`

```python
from langgraph.checkpoint.memory import MemorySaver

class LangGraphWorkflow:
    def __init__(self, ...):
        ...
        self._checkpointer = MemorySaver()

    def _build_graph(self):
        ...
        # BEFORE (line 302):
        # return workflow.compile()

        # AFTER:
        return workflow.compile(
            checkpointer=self._checkpointer,
            interrupt_before=["train_model", "finalize"],
        )
```

The interrupt points map to the requirements:

| Interrupt | Requirement |
|-----------|-------------|
| `train_model` | `REQUIREMENTS.md` §1.2: approval gate before `MODELING` |
| `finalize` | `REQUIREMENTS.md` §1.2: approval gate before deployment |

#### 3.2.2 Update `AgentRunner._run()` to handle interrupts

**File:** `backend/app/services/agent/runner.py`

When the graph yields an interrupt, the runner must:

1. Persist the thread state via `SessionManager.save_session_state()`.
2. Publish an `action_request` event (per `API_CONTRACTS.md` §2.3) with the interrupt details.
3. Publish a `status_update` event with `status: "AWAITING_APPROVAL"`.
4. Exit the execution loop (do not mark session as completed).

```python
# Inside _run(), after streaming a graph step:
if state.get("__interrupt__"):
    # Emit action_request with structured options
    await self._publish(redis, channel, {
        "event_type": "action_request",
        "stage": state.get("current_step", "UNKNOWN"),
        "payload": {
            "action_id": f"approve_{state.get('current_step', 'unknown').lower()}",
            "description": "User approval required to proceed.",
            "options": ["APPROVE", "REJECT", "EDIT_BLUEPRINT"],
        },
    })
    await self._publish(redis, channel, {
        "event_type": "status_update",
        "stage": state.get("current_step", "UNKNOWN"),
        "payload": {
            "status": "AWAITING_APPROVAL",
            "message": "User approval required to proceed.",
        },
    })
    await session_manager.save_session_state(session_id, state)
    return  # Yield control back; resume via resume_session()
```

#### 3.2.3 Wire `AgentOrchestrator.resume_session()` to use thread_id

**File:** `backend/app/services/agent/orchestrator.py`

The `resume_session()` method must load the checkpointed state and continue execution from the interrupt point. It must pass the same `thread_id` (derived from `session_id`) to the graph's `invoke()` / `astream()` call so the checkpointer can resume.

```python
async def resume_session(self, db, session_id):
    state = await self.session_manager.get_session_state(session_id)
    config = {"configurable": {"thread_id": str(session_id)}}
    # Continue from interrupt
    result = await self.workflow.graph.ainvoke(None, config=config)
    ...
```

#### 3.2.4 Add data-insufficiency routing to `_route_after_validation`

**File:** `backend/app/services/agent/langgraph_workflow.py`

Currently, failed validation triggers a retry or routes to `reason`. Add an explicit path to `finalize` with a meaningful error when data is genuinely insufficient (e.g., < 50 rows):

```python
def _route_after_validation(self, state):
    ...
    record_count = len(state.get("retrieved_data", {}).get("price_data", []))
    if record_count < 50 and state.get("retry_count", 0) >= 1:
        state["status"] = "completed_with_errors"
        state["error"] = (
            f"Insufficient data: only {record_count} records retrieved. "
            "A minimum of 50 records is required for meaningful analysis."
        )
        return "finalize"
    ...
```

### 3.3 Reconciling `lab_graph.py` and `LangGraphWorkflow`

`lab_graph.py` (Phase 2 graph) was built as a prototype with `LabState`. Now that `LangGraphWorkflow` (with `AgentState`) is the runtime graph, the plan is:

1. **Keep `lab_graph.py` as a reference** — do not delete it.
2. **Port the interrupt and checkpointer patterns** from `lab_graph.py` into `LangGraphWorkflow` (as described in §3.2.1).
3. **Deprecate** `lab_graph.py` by adding a docstring: `# DEPRECATED: interrupt/checkpoint logic has been ported to langgraph_workflow.py`.
4. Long-term, `lab_graph.py` can be removed once all Phase 2 node logic (the `node_*` functions in `nodes/lab_nodes.py`) is also consolidated into `LangGraphWorkflow`.

### 3.4 Acceptance Criteria

- [ ] The workflow pauses before `train_model` and `finalize` nodes, emitting `AWAITING_APPROVAL` status.
- [ ] The frontend receives the `action_request` event (`API_CONTRACTS.md` §2.3) with structured `action_id`/`description`/`options`, and the backend resumes from the correct checkpoint on approval.
- [ ] Insufficient data (< 50 records after retry) terminates the session with a descriptive error rather than looping.
- [ ] Session state survives a WebSocket disconnect — reconnecting resumes from the last checkpoint.
- [ ] **[B+]** `GET /api/v1/lab/agent/sessions/{id}/rehydrate` returns the full `event_ledger` with canonical `sequence_id` values conforming to `API_CONTRACTS.md` §3.
- [ ] **[B+]** WebSocket with `?after_seq=N` skips history replay and only streams live events with `sequence_id > N`.

### 3.5 [B+] Rehydration Endpoint & WebSocket `after_seq`

#### 3.5.1 Add `GET /rehydrate` endpoint

**File:** `backend/app/api/routes/agent.py`

Add a REST endpoint that returns the full event ledger for a session:

```python
@router.get("/sessions/{session_id}/rehydrate")
async def rehydrate_session(session_id: uuid.UUID, db: SessionDep):
    messages = db.exec(
        select(AgentSessionMessage)
        .where(AgentSessionMessage.session_id == session_id)
        .order_by(AgentSessionMessage.sequence_id.asc())
    ).all()
    return {
        "session_id": str(session_id),
        "last_sequence_id": messages[-1].sequence_id if messages else 0,
        "event_ledger": [msg.to_event_dict() for msg in messages],
    }
```

The response schema matches `API_CONTRACTS.md` §3 exactly.

#### 3.5.2 Add `after_seq` parameter to WebSocket

**File:** `backend/app/api/routes/websockets.py`

Modify `websocket_agent_stream` to accept an optional `after_seq` query parameter. If provided, skip the `AgentSessionMessage` history replay loop (lines 373-385). Only subscribe to Redis for live events with `sequence_id > after_seq`:

```python
@router.websocket("/ws/agent/{session_id}/stream")
async def websocket_agent_stream(
    websocket: WebSocket,
    session_id: str,
    after_seq: int | None = Query(default=None),
):
    ...
    if after_seq is None:
        # Full replay for clients that did not rehydrate via REST
        for idx, msg in enumerate(history, start=1):
            await websocket.send_json({...})
    # else: skip replay — client already has state from /rehydrate
    
    # Subscribe to Redis for live events only
    ...
```

This is backward-compatible — existing clients that don't pass `after_seq` still get the full replay.

> **⚠️ MemorySaver Limitation:** `MemorySaver` is in-memory only. Checkpoints do not survive process restarts. Sessions paused at HITL gates will require re-execution if the server restarts. This is acceptable for Phase 5.5. Phase 6 migrates to `PostgresSaver`. Interim guidance: users should not leave sessions paused overnight.

### 3.6 Files Modified

| File | Nature of Change |
|------|-----------------|
| `backend/app/services/agent/langgraph_workflow.py` | Add `MemorySaver` checkpointer, `interrupt_before`, data-insufficiency route |
| `backend/app/services/agent/runner.py` | Handle interrupt state, publish `action_request` + `AWAITING_APPROVAL`, exit loop cleanly |
| `backend/app/services/agent/orchestrator.py` | Wire `resume_session()` to use `thread_id` with checkpointer |
| `backend/app/services/agent/lab_graph.py` | Add deprecation docstring |
| `backend/app/api/routes/agent.py` | **[B+]** Add `GET /sessions/{id}/rehydrate` endpoint |
| `backend/app/api/routes/websockets.py` | **[B+]** Add `after_seq` query parameter; skip history replay when provided |

---

## 4. Workstream C — Wire Training to Dagger + MLflow ("Persistence" Fix)

### 4.1 Diagnosis

The `ModelTrainingAgent` imports exclusively from local tools:

```python
from ..tools import (
    cross_validate_model,
    train_classification_model,
    train_regression_model,
)
```

These tools (`model_training_tools.py`) run sklearn in the FastAPI process — violating `REQUIREMENTS.md` §2 (no agent code on the host) — and never call MLflow.

Meanwhile, the codebase already has:

- `run_code_in_dagger()` (`tools/dagger_tool.py`) — executes code in a Dagger container with MLflow tracking.
- `PipelineManager` (`pipeline.py`) — exports materialized views to Parquet.
- `SandboxExecutor` (`execution.py`) — wraps the Dagger SDK.

The training path must be rerouted through Dagger to satisfy the sandbox and tracking requirements.

### 4.2 Changes Required

#### 4.2.1 Refactor `ModelTrainingAgent.execute()` to use Dagger

**File:** `backend/app/services/agent/agents/model_training.py`

Replace the direct sklearn calls with code generation + Dagger execution:

```python
from ..tools import run_code_in_dagger

class ModelTrainingAgent(BaseAgent):
    async def execute(self, state):
        # 1. Determine task type and features (unchanged)
        task_type = self._determine_task_type(...)
        target_col = self._infer_target_column(task_type)
        
        # 2. Generate the training script as a string
        code = self._generate_training_script(
            task_type=task_type,
            model_type=training_params.get("model_type", "random_forest"),
            target_column=target_col,
            feature_columns=feature_columns,
            hyperparameters=training_params.get("hyperparameters", {}),
        )
        
        # 3. Execute inside Dagger with MLflow tracking
        result = await run_code_in_dagger(
            session_id=state["session_id"],
            code=code,
            mv_name=state.get("dataset_name", "mv_training_set_v1"),
            run_name=f"{task_type}_{model_type}",
        )
        
        # 4. Parse result — the Dagger tool already logs to MLflow
        if result["status"] == "success":
            state["model_trained"] = True
            state["trained_models"] = {
                model_type: {
                    "artifact_paths": result.get("artifact_paths", []),
                    "stdout": result.get("stdout", ""),
                }
            }
            ...
```

#### 4.2.2 Add `_generate_training_script()` method

**File:** `backend/app/services/agent/agents/model_training.py`

A new private method that builds the Python script string the Dagger container will execute. The script must:

1. Load the Parquet from `/data/`.
2. Split train/test with time-series awareness.
3. Train the model (sklearn/XGBoost).
4. Save the `.pkl` to `/workspace/out/`.
5. Print metrics to stdout in a parsable JSON format.

```python
def _generate_training_script(self, task_type, model_type, target_column,
                               feature_columns, hyperparameters):
    """Generate a self-contained Python training script for Dagger execution."""
    features_str = str(feature_columns)
    hp_str = str(hyperparameters)
    return f"""
import pandas as pd
import json
import joblib
from pathlib import Path

df = pd.read_parquet("/data/dataset.parquet")
features = {features_str}
target = "{target_column}"

# Time-series split (last 20% for test)
split_idx = int(len(df) * 0.8)
X_train, X_test = df[features][:split_idx], df[features][split_idx:]
y_train, y_test = df[target][:split_idx], df[target][split_idx:]

# ... model construction based on model_type and task_type ...
# ... fit, evaluate, save to /workspace/out/model.pkl ...
# ... print(json.dumps({{"metrics": metrics}})) ...
"""
```

> **Note:** The actual script generation must handle all supported model types (`random_forest`, `xgboost`, `gradient_boosting`, etc.) and both task types. The snippet above is a structural template; the full implementation must produce complete, runnable scripts.

#### 4.2.3 Keep local training tools as fallback

Do not delete `model_training_tools.py`. It serves as a fallback for:

- Unit testing (where Dagger is unavailable).
- Environments without Docker/Dagger installed.

Add a configuration flag to control the training backend:

```python
# backend/app/core/config.py
TRAINING_BACKEND: str = "dagger"  # or "local"
```

The `ModelTrainingAgent.execute()` method checks this flag and falls back to the local tools when `TRAINING_BACKEND == "local"`.

#### 4.2.4 Log failure artifacts in `_handle_error_node()`

**File:** `backend/app/services/agent/langgraph_workflow.py`

When the workflow terminates unexpectedly (after exhausting retries), save a failure report artifact:

```python
async def _handle_error_node(self, state):
    ...
    if state["retry_count"] > max_retries:
        state["status"] = "completed_with_errors"
        # Persist the failure report as an artifact
        from .artifacts import ArtifactManager
        import tempfile, json
        manager = ArtifactManager()
        report = {
            "session_id": str(state.get("session_id")),
            "error": state.get("error"),
            "retry_count": state.get("retry_count"),
            "reasoning_trace": state.get("reasoning_trace", []),
            "last_step": state.get("current_step"),
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(report, f, indent=2, default=str)
            f.flush()
            manager.save_artifact(
                session_id=state["session_id"],
                artifact_type="failure_report",
                name="workflow_failure_report.json",
                file_path=f.name,
                description=f"Workflow failed: {state.get('error', 'unknown')}",
            )
    ...
```

#### 4.2.5 [C+] Parquet Caching in `PipelineManager`

The `PipelineManager.export_mv_to_parquet()` method currently re-queries the materialized view and re-exports the Parquet file on every call. For large MVs this adds significant cold-start lag to every Dagger run, even when the underlying data has not changed.

**File:** `backend/app/services/agent/pipeline.py`

Add a caching layer that checks whether the existing Parquet file is still valid before re-exporting:

```python
import hashlib

class PipelineManager:
    def export_mv_to_parquet(self, mv_name: str, limit: int = 1000) -> str:
        parquet_path = self.session_dir / f"{mv_name}.parquet"
        
        # 1. Query the MV for current row count + checksum
        current_count = self._get_mv_row_count(mv_name, limit)
        cache_meta_path = self.session_dir / f"{mv_name}.cache_meta"
        
        # 2. Check if cached Parquet is still valid
        if parquet_path.exists() and cache_meta_path.exists():
            cached_count = int(cache_meta_path.read_text().strip())
            if cached_count == current_count:
                return str(parquet_path)  # Cache hit — skip export
        
        # 3. Cache miss — full export
        df = self._query_mv(mv_name, limit)
        df.to_parquet(parquet_path, index=False)
        cache_meta_path.write_text(str(len(df)))
        return str(parquet_path)

    def _get_mv_row_count(self, mv_name: str, limit: int) -> int:
        """Fast COUNT(*) query against the MV."""
        ...

    def invalidate_cache(self, mv_name: str) -> None:
        """Force re-export on next call (e.g., after MV refresh)."""
        cache_meta_path = self.session_dir / f"{mv_name}.cache_meta"
        if cache_meta_path.exists():
            cache_meta_path.unlink()
```

**Why row count and not a hash?** Hashing the full MV output defeats the purpose of caching (it requires reading all the data). Row count is a fast SQL `COUNT(*)` query. If the MV is refreshed (rows change), the count will differ and trigger a re-export. For same-count-different-content edge cases (rare for append-only MVs), the cache can be explicitly invalidated via `invalidate_cache()`.

#### 4.2.6 [C+] MLflow Lifecycle Tagging for Discarded Models

When `ModelEvaluatorAgent` determines a trained model has fatally poor performance (e.g., accuracy below a configurable threshold, or the model fails basic sanity checks), the corresponding MLflow run must be tagged to prevent Model Registry pollution.

**File:** `backend/app/services/agent/agents/model_evaluator.py`

After evaluation, if the model fails quality gates, tag the MLflow run:

```python
import mlflow

class ModelEvaluatorAgent(BaseAgent):
    MINIMUM_ACCURACY = 0.5   # Below random chance = discard
    MINIMUM_F1 = 0.3         # Below this = not worth promoting

    async def execute(self, state):
        ...
        # After evaluation completes:
        metrics = evaluation_results.get("metrics", {})
        accuracy = metrics.get("accuracy", metrics.get("r2", 0))
        f1 = metrics.get("f1_score", 0)
        mlflow_run_id = state.get("mlflow_run_id")

        if mlflow_run_id and (accuracy < self.MINIMUM_ACCURACY or f1 < self.MINIMUM_F1):
            with mlflow.start_run(run_id=mlflow_run_id):
                mlflow.set_tag("lifecycle", "discarded")
                mlflow.set_tag(
                    "discard_reason",
                    f"Fatal performance: accuracy={accuracy:.3f}, f1={f1:.3f}"
                )
            state["model_discarded"] = True
            state["evaluation_insights"].append(
                f"⚠️ Model discarded: performance below minimum thresholds "
                f"(accuracy={accuracy:.3f} < {self.MINIMUM_ACCURACY}, "
                f"f1={f1:.3f} < {self.MINIMUM_F1}). "
                f"MLflow run {mlflow_run_id} tagged as 'discarded'."
            )
```

**File:** `backend/app/services/agent/langgraph_workflow.py`

Add `mlflow_run_id` to `AgentState` so it flows from the training step to the evaluation step:

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    mlflow_run_id: str | None   # Set by Dagger tool after training
```

The `run_code_in_dagger` tool already returns the MLflow run ID in its result dict. The `_train_model_node` must propagate it into state:

```python
async def _train_model_node(self, state):
    ...
    result = await self.training_agent.execute(state)
    state["mlflow_run_id"] = result.get("mlflow_run_id")
    ...
```

**Downstream impact:** The `_route_after_evaluation` function should check `state.get("model_discarded")` and, if `True`, route to `finalize` with a descriptive error rather than proceeding to `generate_report` → deployment:

```python
def _route_after_evaluation(self, state):
    if state.get("model_discarded"):
        state["status"] = "completed_with_errors"
        state["error"] = "Model discarded due to fatal performance failure."
        return "finalize"
    ...
```

### 4.3 Acceptance Criteria

- [ ] `ModelTrainingAgent` executes training code inside a Dagger container, not in the FastAPI process.
- [ ] Every training run creates an MLflow experiment with logged params, metrics, and the model artifact.
- [ ] The tearsheet (`API_CONTRACTS.md` §2.2) includes a valid `mlflow_run_id` that links to the logged run.
- [ ] Setting `TRAINING_BACKEND=local` in the environment falls back to the existing sklearn tools (for CI/test).
- [ ] Workflow failures produce a `failure_report` artifact discoverable via `ArtifactManager.list_artifacts()`.
- [ ] **[C+]** Repeated Dagger runs against the same MV reuse the cached Parquet file (no re-export) unless the MV row count has changed.
- [ ] **[C+]** A model with accuracy < 0.5 or F1 < 0.3 causes the MLflow run to be tagged `lifecycle: discarded` and the workflow routes to `finalize` instead of deployment.
- [ ] **[C+]** The MLflow Model Registry contains zero runs tagged `lifecycle: discarded` in the "Production" stage.

### 4.4 Files Modified

| File | Nature of Change |
|------|------------------|
| `backend/app/services/agent/agents/model_training.py` | Replace local tool calls with `run_code_in_dagger()`, add `_generate_training_script()` |
| `backend/app/services/agent/langgraph_workflow.py` | Add failure artifact logging in `_handle_error_node()`; add `mlflow_run_id` to `AgentState`; propagate in `_train_model_node`; check `model_discarded` in `_route_after_evaluation` |
| `backend/app/core/config.py` | Add `TRAINING_BACKEND` setting |
| `backend/app/services/agent/pipeline.py` | **[C+]** Add Parquet caching with row-count validation and `invalidate_cache()` |
| `backend/app/services/agent/agents/model_evaluator.py` | **[C+]** Add MLflow lifecycle tagging for discarded models |

---

## 5. Workstream D — Error Routing & Loop Prevention

### 5.1 Diagnosis

While `_route_after_error` does route to `END` when retries are exhausted, two looping risks remain:

1. **Data fetch loop:** If the data source is genuinely empty (no data for the requested coin/date range), the workflow cycles through `retrieve → validate → reason → retrieve` indefinitely because `_route_after_validation` sends it back to `reason` which re-requests data.
2. **Analysis loop:** If analysis fails on sparse data, `_route_after_analysis` routes to `reason` which may re-request analysis on the same data.

### 5.2 Changes Required

#### 5.2.1 Add loop-breaking guards to routing functions

**File:** `backend/app/services/agent/langgraph_workflow.py`

In `_route_after_validation`:

```python
def _route_after_validation(self, state):
    # If we've already retried data retrieval, do not loop
    retrieval_attempts = state.get("retrieval_attempts", 0)
    if retrieval_attempts >= 2 and not state.get("data_retrieved"):
        state["error"] = "Data retrieval failed after 2 attempts. No data available for the requested parameters."
        return "finalize"
    ...
```

In `_determine_next_action`:

```python
def _determine_next_action(self, state):
    # Per-stage 3-cycle circuit breaker (REQUIREMENTS v1.2 §1.2)
    current_stage = state.get("current_step", "UNKNOWN")
    counts = state.get("stage_iteration_counts", {})
    stage_count = counts.get(current_stage, 0)
    if stage_count >= 3:
        # 4th attempt — trigger HITL interrupt or terminal error
        state["error"] = (
            f"CIRCUIT_BREAKER: Stage '{current_stage}' exceeded 3 reasoning iterations. "
            f"Triggering Human-in-the-Loop interrupt."
        )
        return "finalize"
    ...
```

#### 5.2.2 Add `stage_iteration_counts` to `AgentState`

**File:** `backend/app/services/agent/langgraph_workflow.py`

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    stage_iteration_counts: dict[str, int]  # Per-stage reasoning cycle counter
```

Increment in each node method:

```python
async def _some_node(self, state):
    stage = state.get("current_step", "UNKNOWN")
    counts = state.get("stage_iteration_counts", {})
    counts[stage] = counts.get(stage, 0) + 1
    state["stage_iteration_counts"] = counts
    ...
```

#### 5.2.3 [D+] Statistical Data Health Checks in `_validate_data_node`

The current `_validate_data_node` only checks record count. This is insufficient — the model can still train on "poisoned" data (flatline prices, datasets dominated by outliers, or constant-value features) which produces meaningless models that waste Dagger compute.

**Directive:** Enhance `_validate_data_node` to perform statistical health checks using the existing `get_data_statistics` tool from the retrieval tools (§7.1).

**File:** `backend/app/services/agent/langgraph_workflow.py`

```python
from .tools import get_data_statistics
import numpy as np

async def _validate_data_node(self, state):
    ...
    price_data = state.get("retrieved_data", {}).get("price_data", [])

    # Existing check: record count
    if len(price_data) < 50:
        ...

    # [D+] Statistical health checks
    data_health_errors = []

    if price_data:
        prices = [r.get("close", r.get("price", 0)) for r in price_data]

        # 1. Flatline detection: zero variance means the price never moved
        if len(set(prices)) <= 1:
            data_health_errors.append(
                "FLATLINE: Price data has zero variance (all values identical). "
                "This indicates a data collection failure or a dead market."
            )

        # 2. Outlier dominance: if >90% of values are statistical outliers,
        #    the data is likely corrupted
        if len(prices) >= 20:
            arr = np.array(prices, dtype=float)
            mean, std = np.mean(arr), np.std(arr)
            if std > 0:
                z_scores = np.abs((arr - mean) / std)
                outlier_ratio = np.sum(z_scores > 3) / len(z_scores)
                if outlier_ratio > 0.9:
                    data_health_errors.append(
                        f"OUTLIER_DOMINANCE: {outlier_ratio:.0%} of price data points "
                        f"are >3σ from the mean. This suggests data corruption "
                        f"or an extreme market event that would poison the model."
                    )

        # 3. Constant features: check key numeric columns for zero variance
        if price_data:
            numeric_keys = [k for k in price_data[0] if isinstance(price_data[0].get(k), (int, float))]
            constant_features = []
            for key in numeric_keys:
                values = [r.get(key) for r in price_data if r.get(key) is not None]
                if len(set(values)) <= 1 and len(values) > 10:
                    constant_features.append(key)
            if constant_features:
                data_health_errors.append(
                    f"CONSTANT_FEATURES: {len(constant_features)} feature(s) have zero variance: "
                    f"{constant_features[:5]}. These carry no predictive signal."
                )

    if data_health_errors:
        state["status"] = "completed_with_errors"
        state["error"] = (
            "TERMINAL_DATA_ERROR: Data failed statistical health checks.\n"
            + "\n".join(f"  • {e}" for e in data_health_errors)
        )
        state["data_health_errors"] = data_health_errors
        return state  # _route_after_validation routes to finalize
    ...
```

**Routing integration:** The `_route_after_validation` function must check for `data_health_errors`:

```python
def _route_after_validation(self, state):
    if state.get("data_health_errors"):
        return "finalize"  # Terminal — do not retry, do not train
    ...
```

This is distinct from the record-count check (§3.2.4) which allows a retry. Statistical health failures are **terminal** — retrying the same MV will produce the same poisoned data.

**File:** `backend/app/services/agent/langgraph_workflow.py`

Add `data_health_errors` to `AgentState`:

```python
class AgentState(TypedDict, total=False):
    # ... existing fields ...
    data_health_errors: list[str]  # Terminal data quality failures
```

### 5.3 Acceptance Criteria

- [ ] A session targeting a coin with no data terminates with a descriptive error within 2 retrieval attempts.
- [ ] No DSLC stage exceeds 3 reasoning iterations — the circuit breaker triggers on the 4th attempt.
- [ ] Terminal errors surface as `error` events to the frontend, not silent hangs.
- [ ] **[D+]** Flatline data (zero variance in price) triggers a `TERMINAL_DATA_ERROR` and routes directly to `finalize` — no retry, no training.
- [ ] **[D+]** Data where >90% of values are >3σ outliers triggers a `TERMINAL_DATA_ERROR`.
- [ ] **[D+]** Features with zero variance are detected and reported in the error message.
- [ ] **[D+]** `data_health_errors` is persisted in the session state so the failure report artifact (§4.2.4) can include the specific health check failures.

### 5.4 Files Modified

| File | Nature of Change |
|------|------------------|
| `backend/app/services/agent/langgraph_workflow.py` | Add `stage_iteration_counts` and `data_health_errors` to state; per-stage circuit breaker in routing functions; statistical health checks in `_validate_data_node`; terminal route for health failures |

---

## 6. Workstream E — Frontend Remediation (NEW in v1.2)

### 6.1 Diagnosis

The current React frontend was built during Phase 3 against the v1.0 spec. It implements a "Flat Chat" model with type-based rendering. The v1.2 requirements demand a "Scientific Grid" with causal event ordering, mime-type dispatch, and rehydration support.

| # | Gap | Current State | v1.2 Requirement |
|---|-----|---------------|-------------------|
| E1 | Flat cell list | `LabContext.tsx` stores `LabCell[]` | Stage-grouped `Map<StageID, LabCell[]>` |
| E2 | No sequence ordering | `useLabWebSocket.ts` deduplicates by random `msgId` | Sort by `sequence_id`, discard out-of-order |
| E3 | No rehydration | State resets on mount | REST-first rehydration via `/rehydrate` |
| E4 | Type-based rendering | `LabStageRow.tsx` switches on `cell.type` | Mime-type dispatcher per `API_CONTRACTS.md` §2.1 |
| E5 | No HITL rendering | Blueprint approval is a separate card | Inline Approve/Reject/Edit on `action_request` |
| E6 | No discarded model UI | Promote always enabled | Disable Promote when `lifecycle: discarded` |
| E7 | No cache badge | No visual feedback | "Using Cached Data" badge on cache hit |

### 6.2 Changes Required

#### 6.2.1 [E1] Causal Grid Refactor

**Files:** `frontend/src/features/lab/context/LabContext.tsx`, `frontend/src/features/lab/components/LabGrid.tsx`

Replace the flat `LabCell[]` state with a stage-grouped structure:

```typescript
type LabState = {
  cells: Map<StageID, LabCell[]>;
  activeStages: Set<StageID>;
  lastSequenceId: number;
};
```

The reducer must route incoming events to the correct stage group based on `event.stage`. Stages with no events remain hidden.

#### 6.2.2 [E2] Sequence-ID Ordering

**File:** `frontend/src/features/lab/hooks/useLabWebSocket.ts`

Replace `msgId` deduplication with `sequence_id` ordering:

```typescript
const onMessage = (event: MessageEvent) => {
  const msg = JSON.parse(event.data);
  if (msg.sequence_id <= lastSequenceId.current) return; // Discard out-of-order
  lastSequenceId.current = msg.sequence_id;
  dispatch({ type: msg.event_type, payload: msg });
};
```

#### 6.2.3 [E3] Rehydration Hook

**Files:** `frontend/src/features/lab/hooks/useRehydration.ts` (new), `frontend/src/features/lab/hooks/useLabWebSocket.ts`

```typescript
export function useRehydration(sessionId: string) {
  return useQuery({
    queryKey: ["lab", "rehydrate", sessionId],
    queryFn: () => fetch(`/api/v1/lab/agent/sessions/${sessionId}/rehydrate`).then(r => r.json()),
    staleTime: Infinity,
  });
}
```

**Ordering constraint:** `useRehydration()` **must** complete before `useLabWebSocket()` opens the connection. Enforced by:

```typescript
const { data: rehydration, isSuccess } = useRehydration(sessionId);
useLabWebSocket(sessionId, {
  enabled: isSuccess,
  afterSeq: rehydration?.last_sequence_id ?? 0,
});
```

#### 6.2.4 [E4] Mime-Type Dispatcher

**File:** `frontend/src/features/lab/components/LabStageRow.tsx`

Replace type-based rendering (`cell.type === "result"`) with mime-type dispatch:

```typescript
function renderOutput(cell: LabCell) {
  switch (cell.payload.mime_type) {
    case "text/markdown": return <MarkdownRenderer content={cell.payload.content} />;
    case "application/vnd.plotly.v1+json": return <PlotlyChart data={cell.payload.content} />;
    case "application/json+blueprint": return <BlueprintCard data={cell.payload.content} />;
    case "application/json+tearsheet": return <Tearsheet data={cell.payload.content} />;
    case "image/png": return <img src={`data:image/png;base64,${cell.payload.content}`} />;
    default: return <pre>{JSON.stringify(cell.payload, null, 2)}</pre>;
  }
}
```

#### 6.2.5 [E5] HITL `action_request` Rendering

**File:** `frontend/src/features/lab/components/LabStageRow.tsx`

When `event_type === "action_request"` or `status === "AWAITING_APPROVAL"`, render high-contrast action buttons:

```typescript
if (cell.event_type === "action_request") {
  return (
    <HStack spacing={4} p={4} bg="orange.50" borderRadius="md">
      <Text fontWeight="bold">{cell.payload.description}</Text>
      {cell.payload.options.map(opt => (
        <Button key={opt} colorScheme={opt === "APPROVE" ? "green" : "red"}
          onClick={() => submitApproval(sessionId, opt)}>
          {opt}
        </Button>
      ))}
    </HStack>
  );
}
```

The approval response is sent via `POST /api/v1/lab/agent/sessions/{id}/approvals`.

#### 6.2.6 [E6] Model Discarded UI

**File:** `frontend/src/features/lab/components/Tearsheet.tsx`

When the tearsheet payload contains `lifecycle: "discarded"`:

* Disable the "Promote to Floor" button.
* Render a warning badge: "⚠️ Model discarded: performance below minimum thresholds."

#### 6.2.7 [E7] Cached Parquet Badge

**File:** `frontend/src/features/lab/components/LabStageRow.tsx`

When a `status_update` event for `DATA_ACQUISITION` indicates a Parquet cache hit (via a flag in the payload), display a "Using Cached Data" badge.

### 6.3 Acceptance Criteria

- [ ] Each DSLC stage renders as a separate, isolated section in the Grid.
- [ ] Messages within a stage are sorted by `sequence_id` — no out-of-order rendering.
- [ ] Closing and reopening the browser reconstructs the full Grid state from the `/rehydrate` endpoint.
- [ ] The WebSocket does not replay history when the client provides `?after_seq`.
- [ ] Blueprint, Tearsheet, Plotly, and Markdown outputs are rendered by their specific React components — not as raw text.
- [ ] `action_request` events render inline Approve/Reject/Edit buttons within the active stage cell.
- [ ] The Promote button is disabled when `lifecycle: discarded`.
- [ ] Cache hits display a "Using Cached Data" badge.

### 6.4 Files Modified

| File | Nature of Change |
|------|------------------|
| `frontend/src/features/lab/context/LabContext.tsx` | Replace flat `LabCell[]` with `Map<StageID, LabCell[]>`; add `lastSequenceId` |
| `frontend/src/features/lab/components/LabGrid.tsx` | Iterate stage groups instead of flat list |
| `frontend/src/features/lab/hooks/useLabWebSocket.ts` | Replace `msgId` dedup with `sequence_id` ordering; accept `afterSeq` parameter |
| `frontend/src/features/lab/hooks/useRehydration.ts` | **NEW** — REST rehydration hook |
| `frontend/src/features/lab/components/LabStageRow.tsx` | Mime-type dispatcher; `action_request` rendering; cached Parquet badge |
| `frontend/src/features/lab/components/Tearsheet.tsx` | Discarded model warning; disable Promote |

---

## 7. Implementation Sequence

## 7. Implementation Sequence

These workstreams have the following dependency graph (including hardening upgrades):

```
       ┌──────────┐
       │   D/D+   │  (Error Routing + Data Health — no deps)
       └──────────┘
       ┌──────────┐
       │   A/A+   │  (Messaging + Event Sequencing — no deps)
       └────┬─────┘
            │ pending_events + sequence_id must exist for B to publish correctly
       ┌────▼─────┐
       │   B/B+   │  (HiTL Breakpoints + Rehydration — depends on A/A+)
       └────┬─────┘
            │ checkpointer must work for C's resume-after-approval flow
       ┌────▼─────┐
       │   C/C+   │  (Dagger Training + Caching/Lifecycle — depends on B/B+)
       └────┬─────┘
            │ compliant events + rehydration endpoint must exist for frontend
       ┌────▼─────┐
       │    E     │  (Frontend Remediation — depends on A/A+ and B/B+)
       └──────────┘
```

### Recommended Execution Order

| Step | Workstream | Estimated Scope | Rationale |
|------|-----------|-----------------|-----------|
| 1 | **D/D+** (Error Routing + Data Health) | 1 file, ~80 lines | Quick win. Eliminates infinite loops and poisoned-data training immediately. No dependencies. |
| 2 | **A/A+** (Messaging + Event Sequencing) | 10 files, ~150 lines | Foundation for all downstream event publishing. Sequencing required for B+ rehydration and E ordering. |
| 3 | **B/B+** (HiTL Breakpoints + Rehydration) | 7 files, ~150 lines | Requires `pending_events` + `sequence_id` from A/A+. Rehydration endpoint required for E3. |
| 4 | **C/C+** (Dagger Training + Caching/Lifecycle) | 5 files, ~200 lines | Requires interrupt gates from B/B+. Lifecycle tagging requires `mlflow_run_id` flow. |
| 5 | **E** (Frontend Remediation) | 6 files, ~250 lines | Requires compliant events from A/A+ and rehydration endpoint from B/B+. |

### Testing Strategy

Each workstream must include tests before proceeding to the next:

| Workstream | Test Type | What to Verify |
|------------|-----------|----------------|
| **D** | Unit test | `_route_after_validation` returns `"finalize"` after 2 failed retrievals |
| **D+** | Unit test | `_validate_data_node` detects flatline data (zero variance) and returns `TERMINAL_DATA_ERROR` |
| **D+** | Unit test | `_validate_data_node` detects >90% outlier dominance |
| **D+** | Unit test | `_route_after_validation` returns `"finalize"` when `data_health_errors` is populated |
| **A** | Unit test | `BaseAgent.emit_event()` produces schema-compliant envelopes |
| **A+** | Unit test | `emit_event()` output includes `sequence_id` (int) and `timestamp` (ISO 8601) |
| **A+** | Unit test | Runner's global `seq` counter is monotonically increasing across all events in a session |
| **A** | Integration test | Runner drains `pending_events` and publishes to Redis |
| **B** | Integration test | Graph pauses at `train_model`, resumes on `resume_session()` |
| **B** | Unit test | `_route_after_validation` returns `"finalize"` for < 50 records |
| **B+** | Integration test | WebSocket reconnect to a paused session replays `AWAITING_APPROVAL` status and last `render_output` per stage |
| **B+** | Unit test | `get_rehydration_state()` returns correct stage results from checkpointed state |
| **C** | Integration test | `ModelTrainingAgent.execute()` calls `run_code_in_dagger()`, MLflow run exists |
| **C** | Unit test | `_handle_error_node` creates `failure_report` artifact |
| **C+** | Unit test | `PipelineManager.export_mv_to_parquet()` returns cached path when row count unchanged |
| **C+** | Unit test | `PipelineManager.invalidate_cache()` forces re-export on next call |
| **C+** | Integration test | `ModelEvaluatorAgent` tags MLflow run as `lifecycle: discarded` when accuracy < 0.5 |
| **C+** | Unit test | `_route_after_evaluation` returns `"finalize"` when `model_discarded` is True |

### Integration Gate Tests (v1.2)

These end-to-end acceptance tests validate cross-workstream integration:

| Test Name | Workstreams | What to Verify |
|-----------|-------------|----------------|
| **The Refresh Test** | B+ + E3 | Close browser mid-session. Reopen. Call `/rehydrate`. Grid reconstructs completely. WebSocket with `?after_seq` does not replay duplicates. |
| **The Flatline Data Test** | D+ + A | Submit a session targeting a dead coin. `TERMINAL_DATA_ERROR` error event arrives with zero-variance details. Session terminates cleanly. |
| **The Circuit Breaker Test** | D+ | Force a stage to loop 4 times. Verify `CIRCUIT_BREAKER` error is emitted and workflow routes to `finalize`. |
| **The Mime Compliance Test** | A + E4 | Record all WebSocket messages for a full session. Assert every `render_output` has a valid `mime_type` from the whitelist. Assert every event has `sequence_id` and `timestamp`. |
| **The HITL Round-Trip Test** | B + E5 | Trigger an `interrupt_before` gate. Verify `action_request` event arrives. Submit approval via POST. Verify graph resumes from checkpoint. |

---

## 8. Consolidated File Change Matrix

| File | A | A+ | B | B+ | C | C+ | D | D+ | E | Total |
|------|---|----|----|----|----|----|----|----|---|---------|
| `agents/base.py` | ✓ | ✓ | | | | | | | | 2 |
| `agents/data_retrieval.py` | ✓ | | | | | | | | | 1 |
| `agents/data_analyst.py` | ✓ | | | | | | | | | 1 |
| `agents/model_training.py` | ✓ | | | | ✓ | | | | | 2 |
| `agents/model_evaluator.py` | ✓ | | | | | ✓ | | | | 2 |
| `agents/reporting.py` | ✓ | | | | | | | | | 1 |
| `langgraph_workflow.py` | ✓ | | ✓ | | ✓ | ✓ | ✓ | ✓ | | 6 |
| `runner.py` | ✓ | ✓ | ✓ | | | | | | | 3 |
| `orchestrator.py` | | | ✓ | ✓ | | | | | | 2 |
| `lab_graph.py` | | | ✓ | | | | | | | 1 |
| `lab_schema.py` | | ✓ | | | | | | | | 1 |
| `pipeline.py` | | | | | | ✓ | | | | 1 |
| `core/config.py` | | | | | ✓ | | | | | 1 |
| `api/routes/agent.py` | | | | ✓ | | | | | | 1 |
| `api/routes/websockets.py` | | | | ✓ | | | | | | 1 |
| `lab/context/LabContext.tsx` | | | | | | | | | ✓ | 1 |
| `lab/components/LabGrid.tsx` | | | | | | | | | ✓ | 1 |
| `lab/hooks/useLabWebSocket.ts` | | | | | | | | | ✓ | 1 |
| `lab/hooks/useRehydration.ts` | | | | | | | | | ✓ | 1 |
| `lab/components/LabStageRow.tsx` | | | | | | | | | ✓ | 1 |
| `lab/components/Tearsheet.tsx` | | | | | | | | | ✓ | 1 |

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `MemorySaver` is in-memory only — server restart loses all checkpoints | High | Medium | Acceptable for Phase 5.5. Phase 6 migrates to `PostgresSaver` for persistence across restarts. Interim: document that users should not leave sessions paused overnight. |
| `run_code_in_dagger` requires a running Docker daemon — CI environments may not have Docker | Medium | High | The `TRAINING_BACKEND=local` flag (§4.2.3) provides a no-Docker fallback for CI and tests. |
| Adding `pending_events` to `AgentState` changes the state shape — existing serialised sessions in Redis will lack this key | Medium | Low | Use `.get("pending_events", [])` everywhere. Existing sessions drain cleanly. |
| Script generation in `_generate_training_script()` is fragile — edge cases in feature names or hyperparameter types could produce invalid Python | Medium | Medium | Validate generated scripts with `ast.parse()` before passing to Dagger. Add integration tests with representative datasets. |
| **[A+]** `sequence_id` overflow for very long-running sessions | Low | Low | Python integers are unbounded. No practical risk. |
| **[B+]** Rehydration replays stale `render_output` if the graph has advanced past the cached stage since the last checkpoint save | Medium | Medium | Only replay stages whose `NodeStatus` is `COMPLETE` in the checkpointed state. Verify `current_stage` before replaying. |
| **[B+]** Rehydration + WebSocket duplicate messages if `?after_seq` not passed | Medium | Medium | Frontend enforces REST-first, WebSocket-live sequence. `useRehydration()` must complete before `useLabWebSocket()` connects. Client-side `sequence_id` guard discards duplicates as safety net. |
| **[C+]** Parquet row-count cache produces false positives if MV is refreshed with same number of rows but different content | Low | Medium | The `invalidate_cache()` method provides an explicit override. MV refresh scripts should call it. For audit safety, log cache-hit decisions so they can be traced. |
| **[C+]** MLflow `lifecycle: discarded` tag can be manually removed by users | Low | Low | The Promote API (§5.2 of `IMPLEMENTATION_BRIEF.md`) must independently check model metrics before allowing promotion — the tag is a convenience filter, not a security gate. |
| **[D+]** Z-score outlier detection assumes normally distributed data, which price data rarely is | Medium | Low | The 90% threshold is intentionally extreme — it catches data corruption, not legitimate fat tails. For more nuanced checks, a future iteration could use IQR-based detection (already available in `clean_data` from analysis tools). |
| **[E]** Frontend state management complexity increases significantly with stage-grouped `Map` and sequence ordering | Medium | Medium | Implement incrementally: E1 (structure) → E2 (ordering) → E3 (rehydration) → E4-E7 (rendering). Each sub-item is independently testable. |

---

## 10. Relationship to Phase 5 Roadmap Items

Once Workstreams A–E (and their hardening upgrades) are complete, the original Phase 5 items from `ROADMAP_STRATEGY.md` can proceed:

| Phase 5 Item | Dependency on This Plan |
|-------------|------------------------|
| **5.1 Air-Gap & Limits** | Requires Workstream C/C+ (training runs inside Dagger, where air-gap and resource limits are enforced; Parquet caching reduces cold-start penalty of repeated sandbox runs) |
| **5.2 Hyperparameter UI Overlays** | Requires Workstream A/A+ (the `render_output` envelope with `hyperparameters` field must be correctly populated; `sequence_id` ensures slider-triggered re-evaluation events arrive in order) |
| **5.3 Graceful Degradation** | Requires Workstream B/B+ (WebSocket reconnect must load checkpointed state and replay stage outputs via rehydration — the checkpointer and `get_rehydration_state()` provide this) |
