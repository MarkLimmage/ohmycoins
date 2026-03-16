To align with **Workstream A+ (Event Sequencing)** and **Workstream B+ (State Rehydration)**, the `API_CONTRACTS.md` must be updated to move from an ephemeral chat-style interaction to a **Causal Ledger System**.

The primary shift here is that every message is now a "Fact" in a sequence, allowing the Lab to be perfectly reconstructed after a crash or refresh.

---

# 📜 API_CONTRACTS.md: The Lab 2.0 (v1.2)

## 🔄 DIFF: Messaging & Rehydration Upgrades

The following changes are mandatory for all Phase 5 integration work:

* [ ] **Enveloped Headers:** Added `sequence_id` (int) and `timestamp` (ISO-8601) to the base message wrapper.
* [ ] **Deterministic Ordering:** The `sequence_id` must be monotonic per `session_id`.
* [ ] **Rehydration Endpoint:** Added `GET /api/v1/lab/agent/sessions/{id}/rehydrate` for browser-refresh recovery.
* [ ] **Mime-Type Lockdown:** Restricted `render_output` to a specific whitelist of 5 types.
* [ ] **HITL Action Schema:** Added `action_request` payload for approval gates.

---

## 1. 📬 The Message Wrapper (The Envelope)

Every message sent over the WebSocket (`/ws/agent/{session_id}/stream`) **must** follow this structure. Out-of-order messages arriving at the frontend with a lower `sequence_id` than the current state **shall** be discarded.

```json
{
  "event_type": "stream_chat | status_update | render_output | error | action_request",
  "stage": "BUSINESS_UNDERSTANDING | DATA_ACQUISITION | PREPARATION | EXPLORATION | MODELING | EVALUATION | DEPLOYMENT",
  "sequence_id": 142,
  "timestamp": "2026-03-16T17:14:29.123Z", 
  "payload": { ... }
}

```

> **Law of Timestamps:** All timestamps must use ISO-8601 with millisecond precision in UTC (`Z`). This is non-negotiable for Karpathy-style event auditing.

---

## 2. 💎 Event Payloads

### 2.1 `render_output` (The Grid Driver)

Used to populate the stage-specific cells in the Scientific Grid.

| Mime-Type | Description | Payload Structure |
| --- | --- | --- |
| `text/markdown` | Logs/Reports | `{ "content": "## Analysis..." }` |
| `application/vnd.plotly.v1+json` | Interactive Charts | `{ "content": { "data": [...], "layout": {...} } }` |
| `application/json+blueprint` | Model Specs | `{ "content": { "target": "str", "features": [] } }` |
| `application/json+tearsheet` | Performance Metrics | `{ "content": { "accuracy": 0.85, "mlflow_run": "uuid" } }` |
| `image/png` | Static Plots | `{ "content": "base64_string..." }` |

### 2.2 `status_update` (The Node Driver)

Used to update the React Flow graph and the Grid's active cell status.

```json
{
  "status": "PENDING | ACTIVE | COMPLETE | STALE | AWAITING_APPROVAL",
  "message": "Model training initialized in Dagger sandbox."
}

```

### 2.3 `action_request` (The HITL Gate)

Used when the Graph hits an `interrupt_before` breakpoint.

```json
{
  "action_id": "approve_modeling_v1",
  "description": "Please review the feature set and hyperparameter blueprint.",
  "options": ["APPROVE", "REJECT", "EDIT_BLUEPRINT"]
}

```

---

## 3. 🔄 Rehydration Contract

To support browser refreshes without losing the Lab state, the frontend **shall** call the rehydration endpoint upon component mounting.

**Endpoint:** `GET /api/v1/lab/agent/sessions/{session_id}/rehydrate`

**Response Schema:**

```json
{
  "session_id": "uuid",
  "last_sequence_id": 142,
  "event_ledger": [
    { "sequence_id": 1, "event_type": "status_update", "stage": "BUSINESS_UNDERSTANDING", ... },
    { "sequence_id": 2, "event_type": "render_output", "stage": "BUSINESS_UNDERSTANDING", ... },
    ...
  ]
}

```

*The frontend shall iterate through the `event_ledger` in ascending order of `sequence_id` to rebuild the Grid UI.*

---

## 4. 🛑 Error & Guardrail Contract

If the Safety Bridge (D+ ) triggers a kill-switch:

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

---

**First Action for the MSG Agent:** Acknowledge this updated contract. Your first implementation task is to update the `BaseEvent` Pydantic model in `lab_schema.py` to match Section 1.

**Would you like me to generate the "Validation Script" for the Supervisor to use when checking if the worker's payloads are compliant with these 1.2 Mime-Types?**


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