# 🛠️ Implementation Brief: "The Lab" (Algo Development Module)

**Version:** 1.3 (Conversational Scientific Grid)
**Context:** This document provides the architectural instructions and data contracts required to build "The Lab." Developers and AI Agents must follow these technical patterns strictly.

## 🔄 DIFF: v1.2 → v1.3

* [x] **Chakra UI → Tailwind CSS**: The frontend uses Tailwind CSS, not Chakra UI.
* [x] **MemorySaver → PostgresSaver**: Checkpoints now survive process restarts. Phase 6.1 is COMPLETE.
* [x] **Graph Consolidation**: `lab_graph.py` deleted. `LangGraphWorkflow` is the sole runtime graph. Phase 6.2 is COMPLETE.
* [ ] **3-Column Grid**: Replace single-column stage cells with 3-column layout (Dialogue | Activity | Outputs).
* [ ] **7 Event Types**: Added `stream_chat` (active), `user_message`, `plan_established` to the existing 5.
* [ ] **4 Interrupt Points**: Expanded from 2 (`train_model`, `finalize`) to 4 (`scope_confirmation`, `train_model`, `model_selection`, `finalize`).
* [ ] **Mandatory Scope Confirmation**: `scope_confirmation` node wired at BUSINESS_UNDERSTANDING. No conditional skip.
* [ ] **`POST /message`**: New endpoint for bi-directional user messaging with `sequence_id` guarantee.
* [ ] **Circuit Breaker Escalation**: 3-cycle breaker emits `action_request` instead of `TERMINAL_ERROR`.
* [ ] **Agent Narration**: All nodes emit `stream_chat` events explaining reasoning.
* [ ] **`plan_established` Event**: Master checklist emitted after scope confirmation.

---

## 1. System Architecture Overview

The Lab operates on a decoupled architecture comprising five pillars:

1. **The Orchestrator:** A FastAPI backend wrapping a LangGraph state machine (`LangGraphWorkflow` in `langgraph_workflow.py`). Uses `PostgresSaver` for persistent checkpointing.
2. **The Sandbox:** Ephemeral Dagger containers for executing agent-generated Python using the `omc-agent-base:latest` image.
3. **The Interface:** A React frontend using Tailwind CSS, React Query, and React Flow for the 3-Column Scientific Grid.
4. **The Tracker:** A local MLflow instance for artifact versioning and lifecycle tagging.
5. **The EventLedger:** An immutable, monotonically-sequenced log of all system events. The Lab's state is valid only if it can be reconstructed by replaying this ledger.

---

## 2. Backend Implementation (FastAPI + LangGraph)

### 2.1 LangGraph State Machine Definition

The orchestration logic is built using `langgraph`. The canonical runtime graph is `LangGraphWorkflow` in `langgraph_workflow.py`.

* **Graph Nodes:** `initialize`, `scope_confirmation`, `reason`, `retrieve_data`, `validate_data`, `analyze_data`, `train_model`, `evaluate_model`, `model_selection`, `generate_report`, `finalize`, plus agent-specific nodes.
* **4 Interrupt Points:** `interrupt_before` on `scope_confirmation`, `train_model`, `model_selection`, `finalize`.
* **Scope Confirmation (MANDATORY):** The `scope_confirmation` node parses the user goal, emits `stream_chat` explaining the interpretation, emits `action_request` with `action_id: "scope_confirmation_v1"`, and emits `plan_established` with the task checklist. There is no conditional skip — every session starts with scope confirmation.
* **Model Selection:** The `model_selection` node after `evaluate_model` emits `action_request` with `action_id: "model_selection_v1"` containing comparison data.
* **Agent Narration:** The reasoning node and all agent `execute()` methods emit `stream_chat` events narrating what they're doing and why.

#### The EventLedger Schema

All agent output must flow through the typed event envelope. The `BaseEvent` model **must** include:

```python
class BaseEvent(BaseModel):
    event_type: str          # stream_chat | status_update | render_output | error | action_request | user_message | plan_established
    stage: str               # DSLC stage ID
    sequence_id: int         # Monotonic per session — assigned by the runner
    timestamp: datetime      # ISO-8601 with millisecond precision (UTC)
    payload: dict            # Type-specific content
```

#### The `action_request` Event Types (4 subtypes)

| action_id | Stage | Purpose |
|-----------|-------|---------|
| `scope_confirmation_v1` | BUSINESS_UNDERSTANDING | Mandatory scope lock |
| `approve_modeling_v1` | MODELING | Blueprint approval |
| `model_selection_v1` | EVALUATION | Model comparison & selection |
| `circuit_breaker_v1` | Any | 3-cycle failure escalation |

See root `API_CONTRACTS.md` v1.3 §2.3 for exact payload schemas.

#### Per-Stage Circuit Breaker

No DSLC stage shall exceed 3 reasoning iterations. On the 4th attempt, the system emits `action_request` with `action_id: "circuit_breaker_v1"` presenting the user with recovery options. Only truly unrecoverable errors (zero-variance, sandbox crash) use the `error` event type.

#### `POST /message` Endpoint

New endpoint: `POST /api/v1/lab/agent/sessions/{id}/message`

1. Assigns `sequence_id` N from the session's monotonic counter.
2. Persists the `user_message` event to the EventLedger (DB).
3. Broadcasts via Redis pub/sub to all WS clients.
4. The agent's next response **must** be `sequence_id` N+1.

### 2.2 Initialization & Rehydration Protocol ("REST-first, WebSocket-live")

The Lab must support browser-refresh recovery. The initialization sequence is:

1. Frontend calls `GET /api/v1/lab/agent/sessions/{id}/rehydrate` (REST). Returns full `event_ledger`.
2. Frontend replays the `event_ledger` through the event router to rebuild ALL 3 cells (Dialogue, Activity, Outputs).
3. Frontend opens WebSocket with `?after_seq={last_sequence_id}`.
4. WebSocket skips history replay when `after_seq` is provided.

### 2.3 WebSocket Gateway

* **Async Streaming:** LangGraph agent uses `astream_events`. LLM tokens route to `stream_chat`, tool executions trigger `status_update`.
* **`after_seq` Parameter:** Skips history replay for rehydrated clients.
* **Bidirectional:** User can send messages via `POST /message` which are broadcast to all WS clients.

---

## 3. The Execution Engine (Dagger SDK)

Unchanged from v1.2. See `PHASE_5_INTEGRATION_PLAN.md` §4 for Dagger implementation details.

* Sub-second startup via pre-built `omc-agent-base:latest` image.
* "Disposable Script" pattern — agent generates standalone training scripts.
* Parquet caching via `PipelineManager` row-count check.
* Air-gapped: no Postgres or internet access from sandbox.

---

## 4. Frontend Implementation (React + Tailwind CSS)

### 4.1 The 3-Column Scientific Grid

The Lab UI is a **Conversational Dashboard of Evidence**, organized as a 3-column grid:

```css
.lab-grid {
  display: grid;
  grid-template-columns: 350px 1fr 300px;
  gap: 1rem;
  height: 100%;
}
```

| Column | Component | Renders |
|--------|-----------|---------|
| Left (350px) | `DialoguePanel` | `stream_chat`, `user_message`, `action_request`, `error` |
| Center (1fr) | `ActivityTracker` | `plan_established` (master checklist), `status_update` (item updates) |
| Right (300px) | `StageOutputs` | `render_output` for active/selected stage |

The `LabHeader` (ReactFlow pipeline) sits above the grid and drives stage selection for the Right Cell.

### 4.2 Event Router (LabContext Reducer)

The reducer routes events by `event_type` to the correct state slice:

* `stream_chat` → `dialogueMessages[]` as agent message
* `user_message` → `dialogueMessages[]` as user message
* `action_request` → `dialogueMessages[]` as interactive card + `pendingAction`
* `status_update` → `activityItems[]` (NO cells — just checklist updates)
* `plan_established` → `masterPlan` + initialize `activityItems`
* `render_output` → `stageOutputs[stage][]`
* `error` → `dialogueMessages[]` as error card

### 4.3 Rehydration Hook (`useRehydration`)

On mount: call `/rehydrate`, replay all events through the same router (§4.2), store `last_sequence_id`, then open WebSocket with `?after_seq={last_sequence_id}`. **The UI after rehydration must be pixel-identical to the UI before refresh.**

### 4.4 HITL Action Rendering

`action_request` events render as inline cards in the Dialogue panel (not a banner):
* `scope_confirmation_v1` → Parsed scope + questions + CONFIRM/ADJUST buttons
* `approve_modeling_v1` → Blueprint context + APPROVE/REJECT/EDIT buttons
* `model_selection_v1` → Model comparison table + radio select + CONFIRM
* `circuit_breaker_v1` → Error context + suggestions + recovery buttons

### 4.5 ChatInput

Text input at the bottom of DialoguePanel. Sends `POST /message` with optimistic rendering. Contextual placeholder text.

### 4.6 Mime-Type Dispatcher (Right Cell)

| Mime-Type | React Component |
|-----------|----------------|
| `text/markdown` | Markdown renderer |
| `application/vnd.plotly.v1+json` | Plotly React wrapper |
| `application/json+blueprint` | `BlueprintCard` |
| `application/json+tearsheet` | `Tearsheet` |
| `image/png` | `<img>` with Base64 `src` |

---

## 5. Integration: MLflow & The Floor

Unchanged from v1.2. Lifecycle tagging (`valid`/`discarded`) gates promotion eligibility. Only `lifecycle: valid` models can be promoted via `POST /api/v1/algorithms/promote`.

---

## 6. Contract Reference

All event schemas, payload structures, and endpoint definitions are in root `API_CONTRACTS.md` v1.3. That file is the single source of truth for all JSON payloads.
