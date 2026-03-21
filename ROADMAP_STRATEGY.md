# 🗺️ Roadmap & Execution Strategy: "The Lab"

**Version:** 1.3.2  
**Context:** This document outlines the strategic implementation phases for "The Lab" (Algo Development Module). Because this system involves stateful AI orchestration, isolated container execution, and real-time WebSockets, **strict adherence to the phase order is mandatory**.

## 🔄 DIFF: v1.3.1 → v1.3.2

* [x] **Phases 0–6:** COMPLETE (baseline).
* [x] **Phase 7 (Sprint 2.51):** COMPLETE — Initial v1.3 Conversational Scientific Grid.
* [x] **Phase 7.1 (Sprint 2.52):** COMPLETE — v1.3.1 Enforcement. 6 Severity-A backend + 8 frontend violations remediated. Merged at `8efcab0`. 41 PASS / 0 FAIL / 6 SKIP.
* [ ] **Phase 7.2 (Sprint 2.53+, NEW):** Stage-Row Architecture & Stale Protocol — Per-DSLC-stage 3-column rows, collapsible sidebar, session drawer, revision flow with stale cascade. 3 sub-phases (~2.5 sprints). See §Phase 7.2 below.

---

## 🧭 Strategy Overview: The "Inside-Out" Approach

The team must build from the core execution engine outward to the user interface.

1. **First:** The Sandbox (Where code runs).
2. **Second:** The Orchestrator (The brain that writes the code).
3. **Third:** The Frontend (The glass through which the user watches the brain).
4. **Fourth:** The Bridge (Connecting the results to the rest of the platform).

---

## 🏁 Phase 0: Infrastructure & Scaffolding ✅ COMPLETE

*Establish the local backing services before any application logic is written.*

* **0.1 MLflow Service Setup:** Configure a local MLflow tracking server using the existing Postgres instance as the backend store and a local directory for artifact storage.
* **0.2 Dagger Daemon Verification:** Ensure the Dagger engine is accessible to the FastAPI environment. Define the base `python:3.11-slim` container specification with the strict dependency list (`scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`).
* **0.3 Directory Scaffolding:** Create the session-specific temporary directory structure on the host for Parquet data exports and Dagger artifact retrieval.
* **0.4 Base Image Construction:** Create a `Dockerfile.agent` in the repository root containing the `python:3.11-slim` base and the `RUN pip install` commands for the expanded library list (including `ta-lib` and `shap`). Build and tag this image locally as `omc-agent-base:latest`. This must be completed before Phase 1 begins.
* **Dependencies:** None. This phase blocks all subsequent development.

---

## 🏗️ Phase 1: The "Solid Gate" (Execution & Data Pipeline) ✅ COMPLETE

*Build the isolated execution environment and the data ingestion bridge. The LangGraph agent cannot exist until the tools it relies on are built.*

* **1.1 The MV-to-Parquet Pipeline:** Implement the Python logic to query `mv_training_set_v1`, serialize the output to a `.parquet` file in the session's temporary directory, and return the file path.
* **1.2 The Dagger Execution Tool:** Build the Python wrapper that accepts a code string, mounts the `.parquet` file to `/data`, executes the code within the Dagger sandbox, and captures `stdout`/`stderr`.
* **1.3 Artifact Extraction:** Extend the execution tool to retrieve generated `.pkl` models or `.json` Plotly charts from the container's `/workspace/out` directory before container termination.
* **1.4 The Leakage Validator:** Build the standalone Python function that checks for time-series overlap between target variables and features to prevent look-ahead bias.
* **Dependencies:** Blocked by Phase 0. Blocks Phase 2.

---

## 🧠 Phase 2: The Orchestrator (LangGraph & WebSockets) ✅ COMPLETE

*Construct the AI state machine and the communication gateway.*

* **2.1 The `DSLCState` Schema:** Define the Pydantic models representing the session state, the chat history, the artifacts dictionary, and the `stale_flags` dictionary.
* **2.2 The Node Graph:** Implement the 7 LangGraph nodes (`Business_Understanding` through `Deployment`). Wire them together with conditional edges, ensuring the `Human_in_the_Loop` interrupts are placed before `Modeling` and `Evaluation`.
* **2.3 The "Stale" Reducer:** Implement the mutator logic that cascades "Stale" flags to downstream nodes if an upstream node is modified.
* **2.4 Tool Binding:** Bind the tools built in Phase 1 (Data Extraction, Code Execution) to the LangGraph agent.
* **2.5 The WebSocket Gateway:** Create the FastAPI WebSocket endpoint. Implement the routing logic that translates LangGraph async streams into standardized JSON payloads (`status_update`, `stream_chat`, `render_output`) for the frontend.
* **Dependencies:** Blocked by Phase 1. Blocks Phase 3.
* **2.6 Self-Healing Logic:** Implement the `Remediation` node and conditional edges for resource optimization retries.
---

## 🖥️ Phase 3: The Interactive Grid (React Frontend) ✅ COMPLETE

*Build the user interface that translates the complex backend state into a cohesive notebook experience.*

* **3.1 The WebSocket Client & State Store:** Implement the React hook/store to manage the WebSocket connection and maintain the localized `DSLCState`.
* **3.2 The React Flow Header:** Integrate React Flow at the top of the interface. Bind node colors/status directly to the `status_update` events from the WebSocket.
* **3.3 The `LabStageRow` Component:** Build the reusable row component containing the Chat dialogue, the collapsible Code accordion, and the Output panel.
* **3.4 Visual Rendering Engine:** Implement the logic in the Output panel to parse and natively render Plotly JSON objects and Base64 images without relying on raw console text.
* **Dependencies:** Blocked by Phase 2. Blocks Phase 4.

---

## 🌉 Phase 4: Tracking & Deployment (The Lab-to-Floor Bridge) ✅ COMPLETE

*Finalize the lifecycle by creating the permanent paper trail and the deployment API.*

* **4.1 MLflow Tool Implementation:** Build the backend tool that the agent calls post-evaluation to log hyperparameters, metrics, and the Dagger-exported `.pkl` artifact to the MLflow server.
* **4.2 The Tear Sheet UI:** Update the `Evaluation` stage in the frontend to render the standardized performance card (F1-score, Confusion Matrix) using data returned from the MLflow run.
* **4.3 The "Promote" API:** Build the FastAPI REST endpoint that takes an MLflow `run_id`, verifies its existence, and writes a new, inactive record into the `Algorithm` database table.
* **4.4 Deployment UI Trigger:** Add the "Promote to Floor" button in the final DSLC stage row, wired to the Promote API.
* **Dependencies:** Blocked by Phase 3.

---

## 🛡️ Phase 5: Hardening & UX Polish (The Final 10%) ✅ COMPLETE

*Implement the strict constraints and low-code overlays that make the platform safe and user-friendly.*

> **Status:** Phase 5 is blocked by systemic gaps discovered during integration audit. See `PHASE_5_INTEGRATION_PLAN.md` v1.2 for Workstreams A–E that must complete before the original Phase 5 items can proceed.

* **5.1 Air-Gap & Limits Enforcement:** Enforce the 300-second timeout and 2GB RAM limits on the Dagger containers. Ensure internet access is disabled for the `Preparation`, `Exploration`, and `Modeling` sandbox runs. *(Requires Workstream C/C+)*
* **5.2 Hyperparameter UI Overlays:** Implement the logic that detects a `hyperparameters` dictionary in the agent's Blueprint payload and renders HTML range sliders in the React frontend. Wire these sliders to send re-evaluation requests via WebSocket. *(Requires Workstream A/A+)*
* **5.3 Graceful Degradation:** Ensure WebSocket disconnects trigger a clear UI warning and implement auto-reconnect logic that fetches the latest graph state upon reconnection. *(Requires Workstream B/B+)*
* **Dependencies:** Blocked by Phase 5.5 (Workstreams A–E).

---

## 🔧 Phase 5.5: The Hardening Bridge ✅ COMPLETE

*Bridge the gap between the Phase 3 "Flat Chat" prototype and the Phase 5 "Scientific Grid" architecture. This phase resolves the systemic gaps discovered in the integration audit (`PHASE_5_INTEGRATION_PLAN.md` v1.2).*

* **5.5.0 Backend Workstreams A–D:** Messaging layer (EventLedger + typed events), HiTL breakpoints (checkpointer + interrupt gates), Dagger training bridge, error routing & circuit breaker. These are the prerequisite foundations.
* **5.5.1 Rehydration Endpoint & EventLedger:** Add `GET /api/v1/lab/agent/sessions/{id}/rehydrate` REST endpoint. Add `sequence_id` and `timestamp` to `BaseEvent`. Add `?after_seq` parameter to WebSocket to prevent duplicate replay.
* **5.5.2 Frontend Causal Grid Refactor:** Replace flat `LabCell[]` with stage-isolated `Map<StageID, LabCell[]>`. Implement `sequence_id` ordering. Add mime-type dispatcher for `render_output`.
* **5.5.3 Frontend HITL & Rehydration Integration:** Implement `useRehydration()` hook (REST-first, WebSocket-live). Implement `action_request` rendering with Approve/Reject/Edit buttons. Add Model Discarded UI and Cached Parquet badge.
* **5.5.4 Integration Gate Tests:** End-to-end acceptance tests — The Refresh Test (rehydration), The Flatline Data Test (D+ data health), The Circuit Breaker Test (3-cycle cap), The Mime Compliance Test (typed events), The HITL Round-Trip Test (action_request → approval → resume).
* **Dependencies:** Blocked by Phase 5 pre-work (Workstreams A–D). Blocks Phase 5 hardening items (5.1–5.3) and Phase 6.

---

## 🚀 Phase 6: Production Readiness ✅ COMPLETE

*Finalize the platform for production deployment by resolving known limitations and completing deferred work.*

* **6.1 Persistent Checkpointer:** ✅ Migrated to `PostgresSaver` (`langgraph-checkpoint-postgres`). HITL sessions survive restarts.
* **6.2 Graph Consolidation:** ✅ Deleted `lab_graph.py`, merged into `LangGraphWorkflow`. Single graph implementation.
* **6.3 Air-Gap, HP Overlays & Graceful Degradation:** Complete the original Phase 5 hardening items.
* **Dependencies:** Blocked by Phase 5.5. ✅ COMPLETE.

---

## 🌐 Phase 7: The Conversational Scientific Grid (NEW in v1.3) 🔄 IN PROGRESS

*Transform the single-column Causal Grid into a 3-column Conversational Scientific Grid. The Lab becomes a dialogue between the researcher and the AI agent, with mandatory human gates at 4 critical decision points.*

**Contract:** API_CONTRACTS.md v1.3 is the canonical source of truth.

* **7.1 Backend (Workstream F — Graph Agent):**
  * F1: Wire `scope_confirmation` interrupt (mandatory, no conditional skip)
  * F2: Wire `model_selection` interrupt (evaluation gate)
  * F3: Emit reasoning as `stream_chat` from every LangGraph node
  * F4: Emit `plan_established` event after scope confirmation
  * F5: Add `task_id` field to `status_update` events
  * F6: Implement `POST /message` endpoint with `sequence_id` guarantee
  * F7: Circuit breaker escalation → `action_request` (not TERMINAL_ERROR)

* **7.2 Frontend (Workstream G — Glass Agent):**
  * G1: 3-column CSS Grid layout (350px | 1fr | 300px)
  * G2: DialoguePanel (stream_chat + user_message + action_request + error)
  * G3: ActivityTracker (plan_established + status_update with task_id)
  * G4: StageOutputs (render_output with mime-type dispatch)
  * G5: ChatInput (POST /message, optimistic rendering)
  * G6: Event router refactor (3-cell routing by event_type)
  * G7: Updated state shape (LabSession with 3 cell arrays)
  * G8: Rehydration replays all 3 cells

* **Dependencies:** Blocked by Phase 6. Parallel worktree execution (omc-lab-graph, omc-lab-ui).

---

## 🏗️ Phase 7.2: Stage-Row Architecture & Stale Protocol (NEW) 🔜 UPCOMING

*Transform the single 3-column grid into per-DSLC-stage rows. Each stage gets its own collapsible 3-column row with stage-filtered events. Add stale protocol for downstream invalidation when a completed stage is revised. Enable revision flow with LangGraph checkpoint rewind.*

**Contract:** API_CONTRACTS.md v1.4 — adds `revision_start` event, stage COMPLETE signaling, revision/rerun/keep-stale endpoints, per-stage row layout contract.

**Design Decisions (Resolved):**
| Decision | Choice | Rationale |
|---|---|---|
| Stage dialogue model | Single session, events filtered by `event.stage` | Avoids 3-5 sprint rearchitecture of multi-session; LangGraph checkpointing supports rewind natively |
| Session list placement | Drawer overlay (slide-out panel) | Saves horizontal space; sessions are selected infrequently vs grid which is always visible |
| Graph visualization | Remove entirely | Low value; stage rows themselves indicate progress via headers with status badges |
| Downstream invalidation | Stale protocol with user override | Semantic diffing is fragile for ML pipelines; user sees stale markers and chooses re-run scope |
| Stage row architecture | Each DSLC stage = one 3-column row (dialogue, tasks, outputs) | Matches original `LabStageRow` intent from §3.3 |

* **7.2.1 Layout Foundations (Workstream H — Glass Agent, frontend-only, ~1 sprint):**
  * H1: Collapsible desktop sidebar (48px icon rail ↔ 200px expanded, localStorage)
  * H2: Reduce whitespace / maximize grid area
  * H3: Session list → drawer overlay (Chakra `DrawerRoot`, left slide, 350px)
  * H4: Remove LabHeader (ReactFlow pipeline) — recover 150px
  * H5: Add `stage` field to `DialogueMessage` + `processEvent()`
  * H6: Stage lifecycle state (`staleStages`, `completedStages`, `getStageStatus()`)
  * H7: `StageRow` component (per-stage 3-column grid: `2fr 1fr 1fr`, status-colored left border)
  * H8: `StageRowHeader` (stage name + status icon + expand/collapse + Revise button)
  * H9: `StageRowList` (replaces LabGrid — vertical list of stage rows, auto-scroll to active)
  * H10: Stage-filtered DialoguePanel, ActivityTracker, StageOutputs (`stage` prop)
  * H11: Max-height (450px) + overflow scroll on expanded rows
  * H12: Cleanup — delete LabHeader.tsx, LabGrid.tsx, LabStageRow.tsx

* **7.2.2 Stale Protocol (Workstream I — Graph + Glass Agents, ~0.5 sprint):**
  * I1: Backend emits `status_update COMPLETE` at stage transitions
  * I2: Frontend processes COMPLETE status_update → stage lifecycle
  * I3: `revision_start` event type in schema + runner
  * I4: Frontend processes `revision_start` → stale markers, dialogue dividers
  * I5: Add optional `stage` param to `POST /messages`
  * I6: ChatInput sends `stage` param

* **7.2.3 Revision Flow (Workstream J — Graph + Glass Agents, ~1 sprint):**
  * J1: `POST /sessions/{id}/revise` endpoint (checkpoint rewind + stale cascade)
  * J2: LangGraph checkpoint rewind (PostgresSaver `get_tuple`, reset downstream flags)
  * J3: `POST /sessions/{id}/rerun` + `POST /sessions/{id}/keep-stale` endpoints
  * J4: "Revise" button on COMPLETE row headers
  * J5: "Re-run from here" / "Keep results" buttons on STALE row headers
  * J6: Revision divider in dialogue panel (revision_start event → divider marker)

* **Dependencies:** Blocked by Phase 7.1.  
  Phase 7.2.1 is frontend-only, can be verified against existing rehydrated sessions.  
  Phase 7.2.2 depends on 7.2.1.  
  Phase 7.2.3 depends on 7.2.2.

---

### 📋 Agentic Dev Team Instructions:

1. Do not initiate work on a subsequent phase until the current phase's acceptance criteria (from `USER_STORIES.md`) are demonstrably met and tests are passing.
2. If a roadblock requires a change to the underlying architecture, halt execution and update the `REQUIREMENTS.md` and `IMPLEMENTATION_BRIEF.md` documents before writing compensatory code.
3. All documents in `docs/requirements/the_lab/` are versioned at **v1.2**. The v1.2 specifications (`REQUIREMENTS.md`, `API_CONTRACTS.md`, `USER_STORIES.md`) are the canonical source of truth.
4. Phase 5.5 workstreams must be executed in dependency order: **D → A → B → C → E**. See `PHASE_5_INTEGRATION_PLAN.md` §7 for rationale.