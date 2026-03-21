# 📜 API_CONTRACTS.md: The Lab 2.0 (v1.4 — Stage-Row Architecture & Stale Protocol)

> **v1.4 Changeset (from v1.3.1):**
> - Added `revision_start` event type for revision boundaries (persisted in ledger)
> - Added stage COMPLETE signaling: `status_update` with `status: COMPLETE` at stage transitions
> - Added optional `stage` parameter to `POST /message` for revision-mode messages
> - Added `POST /sessions/{id}/revise` endpoint (checkpoint rewind + stale cascade)
> - Added `POST /sessions/{id}/rerun` endpoint (re-execute from stale stage)
> - Added `POST /sessions/{id}/keep-stale` endpoint (accept stale results)
> - Updated §3 Grid Layout contract to describe per-stage rows (was single 3-column grid)
> - Deprecated ReactFlow pipeline visualization (LabHeader removed; stage row headers replace it)
> - Added §3.3 Sidebar & Session Drawer contract
> - Added §3.4 Stage Row Behavior contract (expand/collapse, status colors)
>
> **v1.3.1 Enforcement Addendum (from Sprint 2.52 Gap Analysis):**
> - Added §0.1: Explicit enforcement rules discovered from production testing
> - Added §2.3.1 fallback rule: LLM failure in scope_confirmation MUST escalate via circuit_breaker, not silent fallback
> - Added §2.4 task_id mandate: Every `status_update` MUST include `task_id` for Activity Tracker item matching
> - Added §3.1: Deduplication law — frontend MUST discard events where `sequence_id ≤ max_seen`
> - Added §3.2: Rehydration/WS overlap rule — WS reconnects with `?after_seq=N` to prevent duplicates
> - Added §6.1: Pipeline node coloring contract — COMPLETE=green, ACTIVE=blue, PENDING=gray
> - Added §7: HITL rendering rules — action_request cards MUST render inline in Dialogue, no external buttons

---

## 0. 🏗️ Architectural Principle: The EventLedger Is the UI

The EventLedger is the **single source of truth** for the entire Lab UI. Every fact — agent reasoning, user responses, status changes, rich outputs, approval gates — is an immutable entry in the ledger with a monotonic `sequence_id`. The frontend renders by replaying the ledger. There is no separate state.

**Corollary:** If it's not in the ledger, it doesn't exist in the UI. If the user refreshes, the rehydration endpoint returns the full ledger, and the frontend replays it through the same event router to reconstruct all three cells identically.

### 0.1 Enforcement Rules (Discovered from Production Testing)

These rules were implicit in v1.3 but are now stated explicitly after Sprint 2.51 production testing revealed violations.

**E1 — No Silent Fallbacks:** If any LLM call fails (scope parsing, reasoning, etc.), the node MUST NOT emit a stub `stream_chat` with "Fallback due to error." Instead, it MUST escalate via `action_request` with `action_id: "circuit_breaker_v1"` containing the error details and user options. Silent continuation degrades the entire downstream pipeline (no scope → no plan → empty Activity Tracker → broken HITL).

**E2 — Node Events vs Runner Events:** When a node emits `pending_events` (e.g., `scope_confirmation_node` emitting a structured `action_request`), the runner MUST publish those node-level events to the frontend. The runner's generic interrupt detection (`state_snapshot.next`) MUST NOT emit a duplicate generic `action_request` that overwrites or conflicts with the node's structured event. The node's events take priority.

**E3 — Every `status_update` MUST carry `task_id`:** The Activity Tracker matches status updates to checklist items by `task_id`. A `status_update` without `task_id` is un-routable and creates orphan entries. Nodes MUST include `task_id` in every `status_update` payload.

**E4 — `plan_established` MUST emit even on fallback:** If scope confirmation fails or is bypassed, the backend MUST still emit a `plan_established` event with a simplified/default plan. The Activity Tracker cannot function without it.

**E5 — Deduplication is mandatory:** The frontend MUST track `max_seen_sequence_id` and discard any event where `sequence_id ≤ max_seen_sequence_id`. This prevents duplicate messages during rehydration+WS overlap and reconnection scenarios.

**E6 — No orphan HITL buttons:** All approval/rejection/selection interactions MUST be rendered as inline `action_request` cards within the Dialogue panel (Left Cell). There MUST NOT be standalone buttons, banners, or modals for HITL outside the Dialogue. The legacy "Resume Workflow (HITL)" button pattern is deprecated.

**E7 — Pipeline node coloring:** The ReactFlow pipeline MUST use these colors: COMPLETE stage = green (`#38A169`), ACTIVE stage = blue (`#3182CE`) with bold+shadow, PENDING = gray (`#EDF2F7`). Yellow is not a valid stage state.

**E8 — ChatInput enabled during active sessions:** The text input in the Dialogue panel MUST be enabled whenever the session status is RUNNING or AWAITING_APPROVAL. It MUST only be disabled for COMPLETED, FAILED, or CANCELLED sessions.

**E9 — Right Cell driven by selection:** The Stage Outputs panel MUST show outputs for the user-selected stage (via pipeline click) or the most recently active stage by default. It MUST NOT be hardcoded to a single stage.

---

## 1. 📬 The Message Wrapper (The Envelope)

Every message sent over the WebSocket (`/ws/agent/{session_id}/stream`) **must** follow this structure.

```json
{
  "event_type": "stream_chat | status_update | render_output | error | action_request | user_message | plan_established | revision_start",
  "stage": "BUSINESS_UNDERSTANDING | DATA_ACQUISITION | PREPARATION | EXPLORATION | MODELING | EVALUATION | DEPLOYMENT",
  "sequence_id": 142,
  "timestamp": "2026-03-16T17:14:29.123Z",
  "payload": { ... }
}
```

**Ordering Laws:**
- `sequence_id` MUST be strictly monotonic per `session_id`. No gaps, no reuse.
- Out-of-order messages arriving at the frontend with a `sequence_id` ≤ the current max SHALL be discarded.
- When a user sends a message via `POST /message`, the response returns the assigned `sequence_id` N. The agent's next event MUST have `sequence_id` N+1.

> **Law of Timestamps:** All timestamps must use ISO-8601 with millisecond precision in UTC (`Z`).

---

## 2. 💎 Event Payloads & 3-Cell Routing

Every event type has a designated cell in the Scientific Grid:

| Event Type | Routes To | Purpose |
| --- | --- | --- |
| `stream_chat` | **Left Cell** (Dialogue) | Agent reasoning, explanations, conversational turns |
| `user_message` | **Left Cell** (Dialogue) | Human responses, clarification answers, steering input |
| `action_request` | **Left Cell** (Dialogue) | Interactive HITL cards (approve, clarify, select model) |
| `revision_start` | **Left Cell** (Dialogue) + **State** | Revision boundary divider + marks downstream stages STALE |
| `status_update` | **Center Cell** (Activity Tracker) | Step progress checklist items (done/active/pending) |
| `plan_established` | **Center Cell** (Activity Tracker) | Master checklist template for the session |
| `render_output` | **Right Cell** (Stage Outputs) | Rich artifacts (markdown, plotly, blueprint, tearsheet) |
| `error` | **Left Cell** (Dialogue) | Error cards with details |

**Critical:** A `status_update` with `status: "ACTIVE"` for a stage MUST trigger the visibility of that stage's 3-cell container in the UI. The stage container appears when the first `status_update` arrives; the content of each cell is populated by subsequent events routed per the table above.

### 2.1 `stream_chat` (The Dialogue Driver) → Left Cell

Agent-to-human conversational messages. Used for reasoning narration, explanations, and context-setting.

```json
{
  "text_delta": "I've analyzed 720 hourly BTC candles. RSI is at 72 indicating overbought conditions. I'll now compute MACD crossovers to confirm the momentum signal."
}
```

**Usage:** The agent MUST emit `stream_chat` events to narrate its reasoning at every significant decision point. This replaces the invisible internal `reasoning_trace`. The human should always know *what* the agent is doing and *why*.

### 2.1.1 `status_update` with `status: COMPLETE` (v1.4)

When a DSLC stage finishes processing and the next stage activates, the backend MUST emit a `status_update` with `status: "COMPLETE"` for the departing stage. This is distinct from individual task completion — it signals the entire stage is done.

```json
{
  "event_type": "status_update",
  "stage": "DATA_ACQUISITION",
  "payload": {
    "status": "COMPLETE",
    "message": "Data acquisition complete. Moving to preparation.",
    "task_id": "stage_complete"
  }
}
```

**Trigger:** Emitted by the runner when the first `status_update ACTIVE` arrives for a new stage. The previous stage receives a COMPLETE signal.

### 2.1.2 `revision_start` (v1.4 — Revision Boundary) → Left Cell + State

Emitted when a user initiates a revision of a completed stage. Persisted in the EventLedger to survive rehydration. Routes to Dialogue as a visual divider and triggers state updates (downstream stale marking).

```json
{
  "event_type": "revision_start",
  "stage": "DATA_ACQUISITION",
  "payload": {
    "revised_stage": "DATA_ACQUISITION",
    "stale_stages": ["PREPARATION", "EXPLORATION", "MODELING", "EVALUATION", "DEPLOYMENT"],
    "revision_epoch": 1
  }
}
```

**Frontend behavior:**
- Render a `--- Revision ---` divider in the revised stage's Dialogue column
- Mark all `stale_stages` as STALE in the state (amber left-border, dimmed content)
- Re-expand the revised stage row, enable ChatInput for that stage

### 2.2 `user_message` (The Human Voice) → Left Cell

Human-to-agent messages, persisted in the ledger and broadcast to all connected clients.

```json
{
  "content": "Focus on ETH instead, use a 7-day window."
}
```

**Lifecycle:** User submits via `POST /message` → backend assigns `sequence_id` N, persists to DB, broadcasts via WS → agent processes and responds with `stream_chat` at `sequence_id` N+1.

### 2.3 `action_request` (The HITL Gate) → Left Cell

Interactive decision cards rendered inline in the Dialogue panel. Three subtypes:

#### 2.3.1 Scope Confirmation (BUSINESS_UNDERSTANDING — MANDATORY)

Every session MUST begin with the agent presenting its interpretation of the user's goal and requesting confirmation. There is no "skip clarification" path.

```json
{
  "action_id": "scope_confirmation_v1",
  "description": "Here's my interpretation of your research goal. Please confirm or adjust.",
  "interpretation": {
    "assets": ["BTC"],
    "timeframe": "30d",
    "analysis_type": "trend_analysis",
    "indicators": ["RSI", "MACD", "Bollinger Bands"],
    "modeling_target": "price_direction_1h"
  },
  "questions": [
    "Should I include additional assets (ETH, SOL, etc.)?",
    "Is a 30-day lookback appropriate, or do you need a different window?",
    "Do you want price prediction, anomaly detection, or correlation analysis?"
  ],
  "options": ["CONFIRM_SCOPE", "ADJUST_SCOPE"]
}
```

#### 2.3.2 Stage Approval (MODELING, DEPLOYMENT)

```json
{
  "action_id": "approve_modeling_v1",
  "description": "Please review the feature set and hyperparameter blueprint before training begins.",
  "context": {
    "features": ["volatility_24h", "sentiment_1h", "rsi_14"],
    "algorithm": "XGBClassifier",
    "estimated_time": "~30s"
  },
  "options": ["APPROVE", "REJECT", "EDIT_BLUEPRINT"]
}
```

#### 2.3.3 Model Selection (EVALUATION)

```json
{
  "action_id": "model_selection_v1",
  "description": "I've trained and evaluated 3 models. Which should we promote?",
  "models": [
    {
      "name": "XGBClassifier",
      "accuracy": 0.85,
      "f1_score": 0.84,
      "training_time": 12.5,
      "pros": ["High accuracy (85%)", "Fast training"],
      "cons": ["Prone to overfitting on small datasets"]
    }
  ],
  "recommendation": {
    "model": "XGBClassifier",
    "confidence": 0.9,
    "reasoning": "Best F1 score with acceptable training time"
  },
  "options": ["SELECT_MODEL", "RETRAIN_ALL", "SKIP_MODELING"]
}
```

#### 2.3.4 Circuit Breaker Escalation (Any Stage)

When the 3-cycle circuit breaker fires, the agent MUST escalate to the human via the Dialogue cell rather than emitting a `TERMINAL_ERROR` (unless the error is truly unrecoverable like zero-variance data).

```json
{
  "action_id": "circuit_breaker_v1",
  "description": "I've attempted this stage 3 times without success. I need your guidance.",
  "stage": "DATA_ACQUISITION",
  "attempts": 3,
  "last_error": "Insufficient price data: only 12 records found for SOL/USDT",
  "suggestions": [
    "Switch to a more liquid pair (BTC/USDT has 720+ records)",
    "Reduce the analysis timeframe to match available data",
    "Skip this data source and proceed with what we have"
  ],
  "options": ["CHOOSE_SUGGESTION", "PROVIDE_GUIDANCE", "ABORT_SESSION"]
}
```

### 2.4 `status_update` (The Activity Tracker Driver) → Center Cell

Drives the checklist in the Activity Tracker. Each update is a line item.

```json
{
  "status": "PENDING | ACTIVE | COMPLETE | STALE | AWAITING_APPROVAL",
  "message": "Computing RSI(14), MACD(12,26,9), and Bollinger Bands...",
  "task_id": "compute_technical_indicators"
}
```

**New field: `task_id`** — Optional stable identifier that allows the Activity Tracker to update an existing checklist item's status (e.g., transition "Compute indicators" from ACTIVE → COMPLETE) rather than always appending new items.

### 2.5 `plan_established` (The Master Checklist) → Center Cell

Emitted once during BUSINESS_UNDERSTANDING after scope confirmation. Defines the anticipated task list for the entire session. This becomes the template for the Activity Tracker's "pending" items.

```json
{
  "plan": [
    {
      "stage": "DATA_ACQUISITION",
      "tasks": [
        { "task_id": "fetch_price_data", "label": "Fetch OHLCV price data" },
        { "task_id": "fetch_sentiment", "label": "Fetch sentiment scores" },
        { "task_id": "fetch_on_chain", "label": "Fetch on-chain metrics" }
      ]
    },
    {
      "stage": "PREPARATION",
      "tasks": [
        { "task_id": "validate_quality", "label": "Run data quality checks" },
        { "task_id": "detect_anomalies", "label": "Detect price anomalies" }
      ]
    },
    {
      "stage": "EXPLORATION",
      "tasks": [
        { "task_id": "compute_technical_indicators", "label": "Calculate technical indicators" },
        { "task_id": "analyze_sentiment_trends", "label": "Analyze sentiment correlation" },
        { "task_id": "perform_eda", "label": "Exploratory data analysis" }
      ]
    },
    {
      "stage": "MODELING",
      "tasks": [
        { "task_id": "train_models", "label": "Train ML models" },
        { "task_id": "cross_validate", "label": "Cross-validation" }
      ]
    },
    {
      "stage": "EVALUATION",
      "tasks": [
        { "task_id": "evaluate_metrics", "label": "Compute evaluation metrics" },
        { "task_id": "compare_models", "label": "Compare model performance" }
      ]
    },
    {
      "stage": "DEPLOYMENT",
      "tasks": [
        { "task_id": "generate_report", "label": "Generate final report" },
        { "task_id": "register_artifacts", "label": "Register model artifacts" }
      ]
    }
  ]
}
```

**The plan is a living document:** If the agent decides to skip modeling (e.g., the user only wants an analysis), it emits a `status_update` with `status: "STALE"` for the skipped `task_id`s, and the Activity Tracker grays them out.

### 2.6 `render_output` (The Stage Output Driver) → Right Cell

Unchanged from v1.2. Populates the right cell with rich artifacts.

| Mime-Type | Description | Payload Structure |
| --- | --- | --- |
| `text/markdown` | Logs/Reports | `{ "mime_type": "text/markdown", "content": "## Analysis..." }` |
| `application/vnd.plotly.v1+json` | Interactive Charts | `{ "mime_type": "...", "content": { "data": [...], "layout": {...} } }` |
| `application/json+blueprint` | Model Specs | `{ "mime_type": "...", "content": { "target": "str", "features": [] } }` |
| `application/json+tearsheet` | Performance Metrics | `{ "mime_type": "...", "content": { "accuracy": 0.85, "mlflow_run": "uuid" } }` |
| `image/png` | Static Plots | `{ "mime_type": "...", "content": "base64_string..." }` |

### 2.7 `error` → Left Cell

Rendered as an error card in the Dialogue panel.

```json
{
  "code": "TERMINAL_DATA_ERROR",
  "message": "Zero variance detected in price signal. Aborting research loop.",
  "details": { "variance": 0.0, "null_count": 0 }
}
```

**Escalation rule:** Only truly unrecoverable errors (zero-variance, sandbox timeout) use the `error` event type. Recoverable failures (insufficient data, API timeout) MUST use`action_request` with `action_id: "circuit_breaker_v1"` to ask the human for guidance (see §2.3.4).

---

## 3. 🔄 Rehydration Contract (All 3 Cells)

The rehydration endpoint returns the **complete** EventLedger. The frontend MUST replay every event through the same event router used for live WebSocket events, populating all three cells identically to the pre-refresh state.

**Endpoint:** `GET /api/v1/lab/agent/sessions/{session_id}/rehydrate`

**Response Schema:**

```json
{
  "session_id": "uuid",
  "last_sequence_id": 142,
  "event_ledger": [
    { "sequence_id": 1, "event_type": "status_update", "stage": "BUSINESS_UNDERSTANDING", "timestamp": "...", "payload": {...} },
    { "sequence_id": 2, "event_type": "stream_chat", "stage": "BUSINESS_UNDERSTANDING", "timestamp": "...", "payload": {...} },
    { "sequence_id": 3, "event_type": "action_request", "stage": "BUSINESS_UNDERSTANDING", "timestamp": "...", "payload": {...} },
    { "sequence_id": 4, "event_type": "user_message", "stage": "BUSINESS_UNDERSTANDING", "timestamp": "...", "payload": {...} },
    { "sequence_id": 5, "event_type": "plan_established", "stage": "BUSINESS_UNDERSTANDING", "timestamp": "...", "payload": {...} },
    { "sequence_id": 6, "event_type": "status_update", "stage": "DATA_ACQUISITION", "timestamp": "...", "payload": {...} },
    { "sequence_id": 7, "event_type": "render_output", "stage": "DATA_ACQUISITION", "timestamp": "...", "payload": {...} }
  ]
}
```

**Reconstruction guarantees:**
- **Left Cell (Dialogue):** Rebuilt from `stream_chat` + `user_message` + `action_request` + `error` events
- **Center Cell (Activity):** Rebuilt from `plan_established` (the template) + `status_update` events (marking items done/active)
- **Right Cell (Outputs):** Rebuilt from `render_output` events grouped by stage

*The frontend shall iterate through the `event_ledger` in ascending order of `sequence_id`, routing each event to the correct cell via the same dispatcher used for live events.*

### 3.1 Grid Layout Contract (v1.4 — Per-Stage Rows)

The single 3-column grid layout (v1.3) is replaced with a per-stage-row architecture. Each DSLC stage renders as its own collapsible 3-column row.

**Row Structure:**
```
<StageRow stage={stage} status={status}>
  <Grid templateColumns="2fr 1fr 1fr" gap={2} maxH="450px">
    <DialoguePanel stage={stage} />   ← filtered by event.stage
    <ActivityTracker stage={stage} /> ← filtered by event.stage
    <StageOutputs stage={stage} />   ← filtered by event.stage
  </Grid>
</StageRow>
```

**Column Proportions:** `2fr 1fr 1fr` — Dialogue gets 50% (carries chat + HITL cards), Tasks 25%, Outputs 25%.

### 3.2 Stage Row Behavior Contract (v1.4)

| Status | Left Border | Expand | Content | Header Actions |
|--------|-------------|--------|---------|----------------|
| ACTIVE | `blue.500` | Auto-expanded | Live 3-column grid | Spinner indicator |
| COMPLETE | `green.500` | Collapsed (click to expand) | Historical events, dimmed slightly | "Revise" button |
| PENDING | `gray.300` | Not expandable | None | None |
| STALE | `orange.400` | Collapsed | Original content, dimmed | "Re-run from here" / "Keep results" |

**Auto-expand rule:** When `status_update ACTIVE` arrives for stage N, expand stage N's row, collapse the previous active stage's row, and smooth-scroll to bring stage N into view.

**Collapsed summary:** Collapsed COMPLETE/STALE rows show a compact summary line (e.g., "3 tasks done, 2 outputs").

### 3.3 Sidebar & Session Drawer Contract (v1.4)

**Sidebar:**
- Desktop: collapsible between 48px (icon-only rail) and 200px (icons + text)
- Toggle: chevron button at bottom of sidebar
- Persistence: `localStorage` key `sidebar-collapsed`
- Collapse does NOT hide navigation — icons remain visible

**Session Drawer:**
- Trigger: Button in Lab page top area with FiList icon + active session count badge
- Implementation: Chakra `DrawerRoot` with `placement="start"`, width 350px
- Contents: Search/filter input, SessionList, "New Session" button
- Behavior: Overlays grid content (does not push), auto-closes on session select

### 3.4 ReactFlow Deprecation (v1.4)

The ReactFlow pipeline visualization (LabHeader, 150px) is deprecated and removed. Stage row headers with status badges, colored left borders, and expand/collapse behavior provide equivalent stage-progress visibility with less vertical overhead.

---

## 4. 📡 REST Endpoints

### 4.1 Session CRUD (Unchanged from v1.2)

- `POST /api/v1/lab/agent/sessions/` — Create session
- `GET /api/v1/lab/agent/sessions/` — List sessions
- `GET /api/v1/lab/agent/sessions/{id}` — Get session
- `DELETE /api/v1/lab/agent/sessions/{id}` — Cancel & delete

### 4.2 HITL Endpoints

#### Approve / Reject (Existing)
`POST /api/v1/lab/agent/sessions/{id}/approve`
```json
{ "approved": true }
```

#### Clarification Response (Existing, now mandatory)
`POST /api/v1/lab/agent/sessions/{id}/clarifications`
```json
{
  "responses": {
    "assets": "BTC and ETH",
    "timeframe": "7 days",
    "analysis_type": "price prediction"
  }
}
```

#### Model Selection (Existing, now mandatory)
`POST /api/v1/lab/agent/sessions/{id}/choices`
```json
{ "selected_model": "XGBClassifier" }
```

### 4.3 User Message (NEW in v1.3)

`POST /api/v1/lab/agent/sessions/{id}/message`

**Request:**
```json
{ "content": "Focus on ETH instead, use a 7-day window.", "stage": "DATA_ACQUISITION" }
```

The `stage` field is **optional** (v1.4). When provided, the message is directed to that specific stage's context (used for revisions of completed stages). When omitted, the message targets the current active stage.

**Response:**
```json
{
  "message": "Received",
  "sequence_id": 42
}
```

**Contract guarantees:**
1. The backend assigns `sequence_id` N to the user message and persists it in the EventLedger.
2. The backend broadcasts the `user_message` event (with `sequence_id` N) to all connected WS clients.
3. The agent's next response event MUST have `sequence_id` N+1. No other event may be interleaved.
4. The frontend renders the user's message immediately on submit (optimistic), then confirms via the WS broadcast matching `sequence_id` N.

### 4.5 Revision Endpoints (NEW in v1.4)

#### Initiate Revision
`POST /api/v1/lab/agent/sessions/{id}/revise`

Initiates a revision of a completed DSLC stage. Rewinds the LangGraph checkpoint, marks downstream stages as STALE, and resumes graph execution.

**Request:**
```json
{ "stage": "DATA_ACQUISITION", "message": "Add ETH data alongside BTC" }
```

**Response:**
```json
{
  "sequence_id": 85,
  "stale_stages": ["PREPARATION", "EXPLORATION", "MODELING", "EVALUATION", "DEPLOYMENT"]
}
```

**Behavior:**
1. Validate `stage` is COMPLETE for this session.
2. Emit `revision_start` event (persisted in ledger).
3. Emit `status_update STALE` for each downstream stage.
4. Emit `status_update ACTIVE` for the revised stage.
5. Rewind LangGraph checkpoint to post-completion of the revised stage.
6. Inject revision message into state and resume graph execution.

#### Re-run from Stale Stage
`POST /api/v1/lab/agent/sessions/{id}/rerun`

Re-executes the pipeline from a stale stage onward.

**Request:**
```json
{ "from_stage": "PREPARATION", "skip_to": "MODELING" }
```

`skip_to` is **optional**. When omitted, re-runs from `from_stage` through all downstream stages. When provided, only runs from `skip_to`, leaving stages between `from_stage` and `skip_to` stale.

**Response:**
```json
{ "message": "Re-run initiated", "from_stage": "PREPARATION" }
```

#### Accept Stale Results
`POST /api/v1/lab/agent/sessions/{id}/keep-stale`

Clears STALE flags without re-running. User asserts downstream results remain valid.

**Response:**
```json
{ "message": "Stale flags cleared", "cleared_stages": ["PREPARATION", "EXPLORATION", "MODELING", "EVALUATION", "DEPLOYMENT"] }
```

### 4.4 Rehydration (Updated)

`GET /api/v1/lab/agent/sessions/{id}/rehydrate` — See §3.

---

## 5. 🔀 Interrupt Topology (v1.3)

The LangGraph workflow pauses at these 4 nodes:

| Interrupt | Stage | Gate Type | Action ID |
| --- | --- | --- | --- |
| `scope_confirmation` | BUSINESS_UNDERSTANDING | Scope lock | `scope_confirmation_v1` |
| `train_model` | MODELING | Blueprint approval | `approve_modeling_v1` |
| `model_selection` | EVALUATION | Model choice | `model_selection_v1` |
| `finalize` | DEPLOYMENT | Final sign-off | `approve_finalize_v1` |

**Plus conditional interrupts:**
- After `validate_data`: If quality is `"fair"` or `"poor"`, emit `action_request` asking user whether to proceed with degraded data.
- Circuit breaker (any stage): After 3 failed iterations, escalate to human via `action_request` (§2.3.4) instead of `TERMINAL_ERROR`.

---

## 6. 🛑 Error & Guardrail Contract

**Unrecoverable errors** (zero-variance kill-switch, sandbox crash):
```json
{
  "event_type": "error",
  "stage": "DATA_ACQUISITION",
  "payload": {
    "code": "TERMINAL_DATA_ERROR",
    "message": "Zero variance detected in price signal. Aborting research loop.",
    "details": { "variance": 0.0, "null_count": 0 }
  }
}
```

**Recoverable errors** (insufficient data, API timeout, 3-cycle breaker): Use `action_request` with `action_id: "circuit_breaker_v1"` (§2.3.4). The agent asks the human for help before giving up.


# REFERENCE ONLY - OLD API_CONTRACTS.md content

Here is the **API_CONTRACTS.md**. This document is the strict "source of truth" for data boundaries. By locking these JSON schemas in place, the Frontend (React) and Backend (FastAPI) agents can work in complete isolation without fear of integration failures.

---

# 🤝 API & Data Contracts: "The Lab"

**Version:** 1.0
**Context:** This document defines the strict communication protocols, JSON schemas, and API endpoints shared between the Frontend Interface and the Backend Orchestrator. **Agents must not deviate from these schemas or add unapproved keys.**

---

## 1. WebSocket Protocol (`/ws/lab/{session_id}`)

All conversational and state-syncing data flows through a bi-directional WebSocket connection.

### 1.1 Enums & Standard Types

* **`StageID`**: `"BUSINESS_UNDERSTANDING" | "DATA_ACQUISITION" | "PREPARATION" | "EXPLORATION" | "MODELING" | "EVALUATION" | "DEPLOYMENT"`
* **`NodeStatus`**: `"PENDING" | "ACTIVE" | "COMPLETE" | "STALE" | "RETRYING_OPTIMIZATION"`
* **`MimeType`**: `"text/markdown" | "application/vnd.plotly.v1+json" | "image/png" | "application/json+blueprint" | "application/json+tearsheet"`

---

### 1.2 Server-to-Client Messages (Backend ➔ Frontend)

Every message sent from the FastAPI backend to the React frontend must strictly adhere to the following wrapper schema:

```json
{
  "event_type": "stream_chat | status_update | render_output | error",
  "stage": "<StageID>",
  "payload": { ... } 
}

```

#### A. `stream_chat`

Used by the LangGraph agent to stream LLM tokens to the UI.

```json
{
  "event_type": "stream_chat",
  "stage": "BUSINESS_UNDERSTANDING",
  "payload": {
    "text_delta": "I will setup an XGBoost model "
  }
}

```

#### B. `status_update`

Used to trigger color/status changes on the React Flow header graph.

```json
{
  "event_type": "status_update",
  "stage": "DATA_ACQUISITION",
  "payload": {
    "status": "ACTIVE"
  }
},
{
  "event_type": "status_update",
  "stage": "MODELING",
  "payload": {
    "status": "RETRYING_OPTIMIZATION",
    "message": "Agent optimizing code due to memory limits (Attempt 1/2)..."
  }
}

```

#### C. `render_output` (The Multi-Modal Cell)

Used to deliver the results of a Dagger execution or an agentic JSON artifact.

```json
{
  "event_type": "render_output",
  "stage": "EXPLORATION",
  "payload": {
    "mime_type": "application/vnd.plotly.v1+json",
    "content": { "data": [...], "layout": [...] },
    "code_snippet": "import pandas as pd\n...", 
    "hyperparameters": null 
  }
}

```

*Note: `code_snippet` is optional and populates the collapsible code accordion. `hyperparameters` is optional and triggers the UI sliders if present.*

#### D. `error`

Used to halt the UI and display a toast/alert.

```json
{
  "event_type": "error",
  "stage": "MODELING",
  "payload": {
    "message": "Dagger Sandbox Timeout (Exceeded 300s)",
    "code": 504
  }
}

```

---

### 1.3 Client-to-Server Messages (Frontend ➔ Backend)

Messages sent from the user's browser to the LangGraph orchestrator.

#### A. `user_message`

When the user types a prompt into the chat box.

```json
{
  "action": "user_message",
  "stage": "BUSINESS_UNDERSTANDING",
  "payload": {
    "text": "Predict BTC price jumps of 5% using news sentiment."
  }
}

```

#### B. `update_hyperparameters`

Triggered when the user adjusts a slider in the UI, prompting a re-run of the Dagger sandbox.

```json
{
  "action": "update_hyperparameters",
  "stage": "MODELING",
  "payload": {
    "hyperparameters": {
      "learning_rate": 0.05,
      "max_depth": 6
    }
  }
}

```

#### C. `approve_gate`

Triggered when the user clicks "Approve & Continue" at the `Human_in_the_Loop` interrupts.

```json
{
  "action": "approve_gate",
  "stage": "BUSINESS_UNDERSTANDING",
  "payload": {
    "approved": true
  }
}

```

---

## 2. Core JSON Artifact Schemas

When the backend sends a `render_output` event with a custom application JSON mime type, the `content` must adhere to these schemas.

### 2.1 The Model Blueprint (`application/json+blueprint`)

Generated by the agent during `BUSINESS_UNDERSTANDING`.

```json
{
  "target_variable": "target_return_1h",
  "feature_list": ["volatility_24h", "sentiment_1h", "news_vol_1h"],
  "ml_task_type": "CLASSIFICATION",
  "algorithm_recommendation": "XGBClassifier",
  "primary_evaluation_metric": "f1_score"
}

```

### 2.2 The Tear Sheet (`application/json+tearsheet`)

Generated by the agent/MLflow during `EVALUATION`.

```json
{
  "metrics": {
    "f1_score": 0.82,
    "precision": 0.85,
    "recall": 0.79
  },
  "assumed_pnl_percent": 14.5,
  "mlflow_run_id": "abc123xyz890"
}

```

---

## 3. REST API Contract: The Deployment Bridge

The only standard HTTP REST call in The Lab. Triggered by the "Promote to Floor" button.

### 3.1 `POST /api/v1/algorithms/promote`

**Headers:**

* `Content-Type: application/json`
* `Authorization: Bearer <token>`

**Request Body:**

```json
{
  "mlflow_run_id": "abc123xyz890",
  "algorithm_name": "BTC_Sentiment_XGB_v1",
  "signal_type": "CLASSIFICATION"
}

```

**Success Response (201 Created):**

```json
{
  "status": "success",
  "message": "Algorithm successfully registered to the Floor.",
  "data": {
    "algorithm_id": "alg_987654321",
    "name": "BTC_Sentiment_XGB_v1",
    "state": "INACTIVE"
  }
}

```

**Error Response (404 Not Found):**
*(If the MLflow run ID cannot be validated locally)*

```json
{
  "detail": "MLflow run_id abc123xyz890 not found in local registry."
}

```