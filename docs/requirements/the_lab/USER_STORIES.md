# 📖 User Stories: "The Lab" (v1.3 — Conversational Scientific Grid)

## 🔄 DIFF: v1.2 → v1.3

* **3-Column Grid:** Replaced "Causal Cells" with 3-column layout (Dialogue | Activity | Outputs).
* **Scope Confirmation:** Added mandatory scope confirmation epic (no conditional skip).
* **Conversational Dialogue:** Added epics for agent narration and user messaging.
* **Plan Established:** Added story for master checklist initialization.
* **Model Selection:** Added story for model comparison gate.
* **Circuit Breaker Escalation:** Recoverable errors → `action_request`, not `TERMINAL_ERROR`.

---

## Epic 1: Workspace & State Management (The 3-Column Grid)

### 1.1 The Visual Graph & Sync

**As an** Algo Architect,
**I want** the visual stage graph (ReactFlow header) to persist across browser refreshes,
**So that** I don't lose context of my research progress if my connection drops.

* **AC 1:** Upon page load, the UI calls the `/rehydrate` endpoint and reconstructs the stage colors (Green/Amber/Blue) based on the `EventLedger`.
* **AC 2:** All three cells (Dialogue, Activity, Outputs) are fully populated from the replayed ledger — the UI is pixel-identical to pre-refresh.

### 1.2 The 3-Column Scientific Grid

**As an** Algo Architect,
**I want** my Lab session displayed as three columns — Dialogue, Activity Tracker, and Stage Outputs —
**So that** I can see the conversation, progress, and artifacts simultaneously without scrolling through a single column of mixed content.

* **AC 1:** The Lab session view renders as a CSS Grid with columns: 350px | 1fr | 300px.
* **AC 2:** Dialogue (Left) shows agent chat, user messages, and HITL cards.
* **AC 3:** Activity Tracker (Center) shows a checklist of tasks grouped by stage.
* **AC 4:** Stage Outputs (Right) shows rich artifacts for the active or selected stage.

---

## Epic 2: Business Understanding (Scope Confirmation)

### 2.1 Natural Language Initiation

**As an** Algo Architect,
**I want** to describe my analysis goal in plain English,
**So that** the agent can translate my intent into a precise ML specification.

* **AC 1:** The session starts with a text input for the user's goal.

### 2.2 Mandatory Scope Confirmation

**As an** Algo Architect,
**I want** the agent to always stop and present its interpretation of my goal before proceeding,
**So that** I can correct misunderstandings before any compute is wasted.

* **AC 1:** The agent emits a `stream_chat` event explaining its interpretation of the user's goal.
* **AC 2:** The agent emits an `action_request` with `action_id: "scope_confirmation_v1"` containing parsed scope (assets, timeframe, analysis type, indicators) and clarifying questions.
* **AC 3:** The workflow **does not** proceed until the user explicitly clicks CONFIRM_SCOPE or ADJUST_SCOPE. There is no conditional skip.
* **AC 4:** If the user adjusts, the agent re-interprets and re-presents scope confirmation.

### 2.3 Plan Establishment

**As an** Algo Architect,
**I want** to see a master checklist of all planned tasks after confirming scope,
**So that** I know what the agent will do and can track progress through each stage.

* **AC 1:** After scope confirmation, the agent emits a `plan_established` event with tasks grouped by stage.
* **AC 2:** The Activity Tracker initializes all tasks as PENDING with stage section headers.

### 2.4 The Blueprint Gate

**As an** Algo Architect,
**I want** the agent to stop and wait for my approval after generating the feature Blueprint,
**So that** I can catch feature-engineering errors before any code is executed in the sandbox.

* **AC 1:** The workflow triggers `action_request` with `action_id: "approve_modeling_v1"` after the Blueprint is rendered.
* **AC 2:** The card renders inline in the Dialogue panel with APPROVE/REJECT/EDIT_BLUEPRINT buttons.

---

## Epic 3: Conversational Dialogue

### 3.1 Agent Narration

**As an** Algo Architect,
**I want** the agent to narrate its reasoning in the Dialogue panel at every decision point,
**So that** I understand what it's doing and why without having to inspect internal logs.

* **AC 1:** Every LangGraph node emits at least one `stream_chat` event with a human-readable explanation.
* **AC 2:** Chat bubbles appear in the Left Cell with agent styling (left-aligned, blue border).
* **AC 3:** Narration includes concrete details (e.g., "Retrieved 720 BTC candles", "RSI at 72, indicating overbought").

### 3.2 User Messaging

**As an** Algo Architect,
**I want** to send free-text messages to the agent at any point during the session,
**So that** I can steer the analysis, ask questions, or provide additional context.

* **AC 1:** A text input at the bottom of the Dialogue panel lets me type and send messages.
* **AC 2:** My message is immediately rendered as a user bubble (right-aligned, gray background).
* **AC 3:** The message is sent via `POST /message` and returns a `sequence_id`. The agent's response is `sequence_id` N+1.

---

## Epic 4: Data Acquisition & Safety

### 4.1 The "Poisoned Data" Rejection

**As an** Algo Architect,
**I want** the Lab to automatically abort if the retrieved data is statistically "dead",
**So that** I don't waste time training on corrupted signals.

* **AC 1:** If the Safety Bridge detects zero variance or >90% outliers, the UI renders an `error` card in the Dialogue panel.

### 4.2 Circuit Breaker Escalation

**As an** Algo Architect,
**I want** the agent to ask me for guidance after 3 failed attempts instead of just dying,
**So that** I can provide alternative approaches or choose to abort gracefully.

* **AC 1:** After 3 failed iterations in any stage, the agent emits `action_request` with `action_id: "circuit_breaker_v1"`.
* **AC 2:** The card shows the error context, suggestions, and buttons (CHOOSE_SUGGESTION, PROVIDE_GUIDANCE, ABORT_SESSION).
* **AC 3:** Only truly unrecoverable errors (zero-variance, sandbox crash) show as `error` events.

---

## Epic 5: Modeling & Sandboxing

### 5.1 Cold-Start Performance

**As an** Algo Architect,
**I want** repeated training runs on the same dataset to start instantly,
**So that** I can iterate on hyperparameters without waiting for the data export process.

* **AC 1:** The Activity Tracker shows a "Using Cached Data" indicator when Parquet cache hits.

### 5.2 Model Selection Gate

**As an** Algo Architect,
**I want** to compare trained models side-by-side and choose which to promote,
**So that** I have informed control over which model reaches production.

* **AC 1:** After evaluation, the agent emits `action_request` with `action_id: "model_selection_v1"` containing model comparison data (metrics, pros, cons, recommendation).
* **AC 2:** The card renders inline in the Dialogue panel with a radio select for model choice.
* **AC 3:** Only the selected model proceeds to promotion.

---

## Epic 6: Evaluation & Registry Lifecycle

### 6.1 The Tear Sheet & MLflow Link

**As an** Algo Architect,
**I want** the Tear Sheet to show me the specific `mlflow_run_id`,
**So that** I can verify the model lineage in the experiment tracker.

### 6.2 Automated Model Discarding

**As an** Algo Architect,
**I want** the system to automatically tag models as "Discarded" if they fail my performance threshold,
**So that** my production Model Registry doesn't get cluttered with "junk" experiments.

* **AC 1:** If evaluation fails the gate, the UI renders a "Model Discarded" warning and disables the "Promote to Floor" button.

---

## Epic 7: Deployment (The Bridge)

### 7.1 Lineage-Locked Promotion

**As an** Algo Architect,
**I want** the "Promote to Floor" action to be immutable,
**So that** I know exactly which Lab session and which dataset produced the model currently trading live.

* **AC 1:** Promoting a model creates a permanent link in the `Algorithm` table between the MLflow Artifact and the Lab `session_id`.

---

## Epic 8: Activity Tracking

### 8.1 Master Checklist

**As an** Algo Architect,
**I want** a central Activity Tracker that shows all planned tasks and their status,
**So that** I can see at a glance how far the session has progressed.

* **AC 1:** The `plan_established` event populates the Activity Tracker with all tasks grouped by stage (all PENDING).
* **AC 2:** `status_update` events with matching `task_id` update specific items (ACTIVE → COMPLETE).
* **AC 3:** Unmatched `status_update` events append as new items to the appropriate stage group.
* **AC 4:** Stage icons: active (◉), complete (✓), task active (◎ spinner), pending (○).
