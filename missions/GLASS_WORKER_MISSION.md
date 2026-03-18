# 🪟 WORKER MISSION: Glass Agent (Scientific Grid UI)

**Branch:** `feature/react-frontend`
**Directory:** `../omc-lab-ui`
**Port:** 5173 (Vite Dev Server)
**Mock WS:** Connect to `ws://localhost:8002` during development
**Role:** You are the Glass Agent. You are the sole developer in this worktree.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` (v1.3) as the strict schema contract.

---

## 🎯 Mission: Build the 3-Cell Scientific Grid

The current Lab UI is a single-column layout of collapsible stage rows. Status updates create clutter cells ("Step: initialization"). The approval gate is a disconnected orange banner. There is no dialogue, no activity tracking, no structured output panel, and no way for the user to send messages.

Your job is to rebuild the Lab session view as a **3-column Scientific Grid** with a Dialogue panel (Left), Activity Tracker (Center), and Stage Outputs (Right).

---

## 📋 Workstream G: Scientific Grid Refactor (8 Tasks)

### G1. 3-Column Grid Layout

**Files:** `frontend/src/features/lab/components/LabGrid.tsx`, `frontend/src/features/lab/components/LabSessionView.tsx`

Replace the single-column stage-row layout with a CSS Grid:

```css
.lab-grid {
  display: grid;
  grid-template-columns: 350px 1fr 300px;
  gap: 1rem;
  height: 100%;
}
```

| Column | Width | Component | Content |
|--------|-------|-----------|---------|
| Left | 350px | `DialoguePanel` | Agent chat, user messages, HITL cards |
| Center | 1fr | `ActivityTracker` | Status checklist grouped by stage |
| Right | 300px | `StageOutputs` | Rich artifacts for active/selected stage |

Keep the `LabHeader` (ReactFlow pipeline) above the grid. It drives stage selection for the Right Cell.

### G2. DialoguePanel Component (NEW)

**File:** `frontend/src/features/lab/components/DialoguePanel.tsx`

The conversational heart of the Lab. Renders events routed to the Left Cell:

- **`stream_chat`** → Agent chat bubble (left-aligned, blue border)
- **`user_message`** → User chat bubble (right-aligned, gray background)
- **`action_request`** → Interactive HITL card (inline, not a banner):
  - `scope_confirmation_v1` → Shows interpreted scope + question form + CONFIRM/ADJUST buttons
  - `approve_modeling_v1` → Shows blueprint context + APPROVE/REJECT/EDIT buttons
  - `model_selection_v1` → Shows model comparison table + radio select + CONFIRM button
  - `circuit_breaker_v1` → Shows error context + suggestion list + buttons
- **`error`** → Error card with red border, code, message, details

**Layout:**
```
┌─ Dialogue & Approval ────── WS: LIVE ─┐
│                                         │
│  [Agent bubble] I've analyzed your      │
│  goal. Here's my interpretation...      │
│                                         │
│  [ACTION CARD] Scope Confirmation       │
│  Assets: BTC  Timeframe: 30d           │
│  Q1: Include ETH?  Q2: Window ok?      │
│  [CONFIRM SCOPE]  [ADJUST SCOPE]       │
│                                         │
│  [User bubble] Yes, but add ETH too    │
│                                         │
│  [Agent bubble] Got it! Including       │
│  BTC and ETH with 30d window...        │
│                                         │
├─────────────────────────────────────────┤
│  [Type your response...]         [Send] │
└─────────────────────────────────────────┘
```

Auto-scrolls to the latest message. Shows "WS: LIVE" or "WS: DISCONNECTED" in the header.

### G3. ActivityTracker Component (NEW)

**File:** `frontend/src/features/lab/components/ActivityTracker.tsx`

Renders events routed to the Center Cell as a checklist:

1. **Initialize from `plan_established` event:** When a `plan_established` event arrives, render all tasks as PENDING (gray circles) grouped by stage section headers.

2. **Update from `status_update` events:** Match `task_id` to update specific items:
   - `ACTIVE` → blue spinner
   - `COMPLETE` → green check
   - `STALE` → gray strikethrough (skipped)

3. **Fallback for unmatched status_update:** If a `status_update` has no `task_id` or doesn't match any plan item, append it as a new item in the appropriate stage group.

**Layout:**
```
┌─ Activity Tracker ──────────────────────┐
│                                          │
│ ◉ Business Understanding                │
│   ✓ Scope confirmed                     │
│   ✓ Plan established                    │
│                                          │
│ ◉ Data Acquisition                      │
│   ✓ Fetch BTC/ETH OHLCV data           │
│   ◎ Fetch sentiment scores...           │
│   ○ Fetch on-chain metrics              │
│                                          │
│ ○ Preparation                           │
│   ○ Run data quality checks             │
│   ○ Detect price anomalies              │
│                                          │
│ ○ Exploration                           │
│   ○ Calculate technical indicators      │
│   ○ Analyze sentiment correlation       │
│                                          │
│ [... more stages ...]                   │
└──────────────────────────────────────────┘
```

`◉` = stage active, `✓` = done, `◎` = task active (spinner), `○` = pending

### G4. StageOutputs Component (NEW)

**File:** `frontend/src/features/lab/components/StageOutputs.tsx`

Renders `render_output` events for the currently active or user-selected stage:

- Uses existing `CellRenderer` (markdown, plotly, blueprint, tearsheet, PNG)
- Stage selection: clicking a stage in the `LabHeader` pipeline switches the output panel
- Default: shows outputs for the most recently active stage
- Empty state: "No outputs yet for this stage" when a stage has no `render_output` events

**Layout:**
```
┌─ Stage Outputs ─────────────────────────┐
│  ► Data Acquisition                     │
│                                          │
│  ┌─ Transformations ─────────────────┐  │
│  │ Lags:     t-1, t-3, t-5          │  │
│  │ Scaling:  StandardScaler          │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌─ Validation Status ───────────────┐  │
│  │ ████████████████░░░ 85%           │  │
│  │ 85% variance maintained           │  │
│  └───────────────────────────────────┘  │
│                                          │
│  [Plotly chart if available]            │
└──────────────────────────────────────────┘
```

### G5. ChatInput Component (NEW)

**File:** `frontend/src/features/lab/components/ChatInput.tsx`

Text input at the bottom of the DialoguePanel:

- `<textarea>` with send button
- On submit: `POST /api/v1/lab/agent/sessions/{id}/message` with `{ "content": text }`
- **Optimistic rendering:** Immediately append user bubble to dialogueMessages with the returned `sequence_id`
- Disabled states: no session, session completed, session errored
- Placeholder text changes contextually:
  - During scope confirmation: "Adjust the scope or confirm..."
  - During active processing: "Send a message to the agent..."
  - During approval gate: "Respond to the agent's request..."

### G6. Event Router Refactor in LabContext

**File:** `frontend/src/features/lab/context/LabContext.tsx`

Refactor the reducer to route events by type to the correct cell. **This is the critical architectural change.**

```typescript
// NEW event routing (replaces current cell-creation logic)
switch (event.event_type) {
  case 'stream_chat':
    // Append to state.dialogueMessages[] as agent message
    break;
  case 'user_message':
    // Append to state.dialogueMessages[] as user message
    break;
  case 'action_request':
    // Append to state.dialogueMessages[] as interactive card
    // Also set state.pendingAction for button handlers
    break;
  case 'status_update':
    // DO NOT create cells anymore
    // Append to state.activityItems[]
    // If task_id matches a plan item, update its status
    // If status is ACTIVE for a stage, add stage to activeStages (triggers container visibility)
    break;
  case 'plan_established':
    // Set state.masterPlan = payload.plan
    // Initialize activityItems from plan tasks (all PENDING)
    break;
  case 'render_output':
    // Append to state.stageOutputs[stage][] (existing cell logic, unchanged)
    break;
  case 'error':
    // Append to state.dialogueMessages[] as error card
    break;
}
```

**Critical:** `status_update` with `status: "ACTIVE"` for a stage MUST trigger the visibility of that stage's row in the grid. The stage container appears; the three cells populate from subsequent events.

### G7. Updated State Shape

**File:** `frontend/src/features/lab/types.ts`

```typescript
interface DialogueMessage {
  id: string;              // sequence_id as string
  type: 'agent' | 'user' | 'action' | 'error';
  content: any;            // text for chat, payload for action/error
  timestamp: string;
  stage: LabStage;
}

interface ActivityItem {
  taskId: string;          // matches plan_established task_id
  label: string;
  stage: LabStage;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETE' | 'STALE';
  message?: string;        // latest status message
}

interface LabState {
  sessionId: string | null;

  // Left Cell: Dialogue
  dialogueMessages: DialogueMessage[];
  pendingAction: ActionRequest | null;

  // Center Cell: Activity
  masterPlan: PlanStage[] | null;    // from plan_established event
  activityItems: ActivityItem[];

  // Right Cell: Outputs
  stageOutputs: Record<LabStage, LabCell[]>;
  selectedStage: LabStage | null;    // which stage's outputs to show in right cell

  // Pipeline
  activeStages: Set<LabStage>;
  lastSequenceId: number;
  isConnected: boolean;
  isDone: boolean;

  // Existing
  metrics: any[];
  blueprint: any | null;
}
```

### G8. Rehydration Replays All 3 Cells

**File:** `frontend/src/features/lab/context/LabContext.tsx` (rehydration handler)

When `useRehydration` fetches the event ledger on mount, it MUST replay every event through the same event router (G6). This ensures:

- Left Cell: All `stream_chat` + `user_message` + `action_request` messages restored
- Center Cell: `plan_established` rebuilds the master checklist, `status_update` events mark items as done/active
- Right Cell: `render_output` events populate stage outputs

**The UI after rehydration must be pixel-identical to the UI before refresh.**

---

## 🔌 Development Against Mock WS Server

During development, connect to `ws://localhost:8002` (Supervisor's mock server). The mock server emits the full v1.3 event sequence:

1. `status_update` (BUSINESS_UNDERSTANDING, ACTIVE)
2. `stream_chat` (agent interpretation of goal)
3. `action_request` (scope_confirmation_v1)
4. — pause for approval —
5. `plan_established` (master checklist)
6. `status_update` (DATA_ACQUISITION, ACTIVE, task_id: fetch_price_data)
7. `stream_chat` (data retrieval narration)
8. `status_update` (DATA_ACQUISITION, COMPLETE, task_id: fetch_price_data)
9. `render_output` (markdown summary of data)
10. ... continues through all stages ...

Use `mock_ws_v13.py` at port 8002 to develop against the full event sequence without needing the real backend.

---

## 🚫 Constraints

- **DO NOT** write Python/backend code. That's the Graph Agent's job.
- **DO NOT** invent new event types. Consume only what's in API_CONTRACTS.md v1.3.
- **DO NOT** remove existing components (CellRenderer, BlueprintCard, Tearsheet, PromoteModal). Reuse them in StageOutputs.
- **DO NOT** break the ReactFlow pipeline header. It continues to show stage status.
- If the UI needs data not in the contract, write a `CONTRACT_RFC.md` and halt.

## ✅ Definition of Done

1. 3-column grid layout renders correctly (350px | 1fr | 300px)
2. DialoguePanel shows agent messages, user messages, and HITL cards
3. ActivityTracker shows master checklist from `plan_established`, updated by `status_update`
4. StageOutputs shows `render_output` cells for selected stage
5. ChatInput sends messages via `POST /message` and renders optimistically
6. Event router correctly routes all 7 event types to their cells
7. Rehydration replays all events through the router — all 3 cells reconstruct
8. ActionRequestBanner replaced with inline HITL cards in DialoguePanel
9. Existing Playwright tests adapted to new layout
10. New tests: dialogue rendering, activity tracker updates, chat input submission
