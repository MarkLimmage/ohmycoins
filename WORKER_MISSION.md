# 🪟 WORKER MISSION: Glass Agent (Scientific Grid UI)

**Branch:** `feature/react-frontend`
**Directory:** `../omc-lab-ui`
**Role:** You are the Glass Agent. You are the sole developer in this worktree.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` (v1.3) as the strict schema contract.

---

## 🔌 YOUR ISOLATED ENVIRONMENT

| Resource | Value |
|---|---|
| Compose Project | `omc-glass` |
| Proxy (Traefik) | `http://localhost:8030` |
| Traefik Dashboard | `http://localhost:8093` |
| PostgreSQL (host access) | `localhost:5435` |
| PostgreSQL (container-internal) | `db:5432` |
| Redis | container-internal only |
| Frontend (Vite) | `http://localhost:5174` |
| Mock WebSocket Server | `ws://localhost:8002` |

### How to Build & Run

```bash
# From this worktree root:
docker compose build
docker compose up -d
docker compose logs -f frontend
```

### How to Run Tests (INSIDE CONTAINERS)

All test execution MUST happen inside containers. Do NOT install npm packages on the host.

```bash
# Run frontend tests (Vitest)
docker compose exec frontend npx vitest run

# Run specific test file
docker compose exec frontend npx vitest run src/features/lab/components/DialoguePanel.test.tsx

# Run with watch mode for development
docker compose exec frontend npx vitest

# Type checking
docker compose exec frontend npx tsc --noEmit

# Lint checking
docker compose exec frontend npx biome check src/
```

### Using the Mock WebSocket Server

The Supervisor provides a mock WS server (`mock_ws_v13.py`) that emits the full v1.3 event sequence. Start it on the host BEFORE running the frontend:

```bash
# In another terminal (on the host, NOT in a container):
cd /home/mark/claude/ohmycoins
python mock_ws_v13.py
# → Listening on ws://localhost:8002
```

During development, configure your WebSocket connection to use `ws://localhost:8002` to test the full event flow without needing the real backend.

### Verifying Your Work

1. **Frontend loads:** Open `http://localhost:5174` in a browser
2. **API via proxy:** `curl http://localhost:8030/api/v1/utils/health-check/`
3. **3-column layout visible:** The Lab view shows Dialogue | Activity | Outputs columns
4. **Mock WS flow:** Start mock server, create a session, see events populate all 3 cells

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
- **`action_request`** → Interactive HITL card (inline, not a banner)
- **`error`** → Error card with red border

Auto-scrolls to the latest message. Shows "WS: LIVE" or "WS: DISCONNECTED" in the header.

### G3. ActivityTracker Component (NEW)

**File:** `frontend/src/features/lab/components/ActivityTracker.tsx`

Renders events routed to the Center Cell as a checklist:

1. **Initialize from `plan_established` event:** Render all tasks as PENDING grouped by stage.
2. **Update from `status_update` events:** Match `task_id` to update specific items.
3. **Fallback for unmatched status_update:** Append as new item to appropriate stage group.

Icons: `◉` = stage active, `✓` = done, `◎` = task active (spinner), `○` = pending

### G4. StageOutputs Component (NEW)

**File:** `frontend/src/features/lab/components/StageOutputs.tsx`

Renders `render_output` events for the currently active or user-selected stage:

- Uses existing `CellRenderer` (markdown, plotly, blueprint, tearsheet, PNG)
- Stage selection via `LabHeader` pipeline clicks
- Default: most recently active stage
- Empty state: "No outputs yet for this stage"

### G5. ChatInput Component (NEW)

**File:** `frontend/src/features/lab/components/ChatInput.tsx`

Text input at the bottom of the DialoguePanel:

- On submit: `POST /api/v1/lab/agent/sessions/{id}/message` with `{ "content": text }`
- **Optimistic rendering:** Immediately append user bubble with returned `sequence_id`
- Disabled states: no session, session completed, session errored
- Contextual placeholder text

### G6. Event Router Refactor in LabContext

**File:** `frontend/src/features/lab/context/LabContext.tsx`

Refactor the reducer to route events by type to the correct cell:

| Event Type | Destination | State Field |
|---|---|---|
| `stream_chat` | Left (Dialogue) | `dialogueMessages[]` |
| `user_message` | Left (Dialogue) | `dialogueMessages[]` |
| `action_request` | Left (Dialogue) | `dialogueMessages[]` + `pendingAction` |
| `status_update` | Center (Activity) | `activityItems[]` — NO cells |
| `plan_established` | Center (Activity) | `masterPlan` + init `activityItems` |
| `render_output` | Right (Outputs) | `stageOutputs[stage][]` |
| `error` | Left (Dialogue) | `dialogueMessages[]` |

**Critical:** `status_update` with `status: "ACTIVE"` MUST trigger stage container visibility.

### G7. Updated State Shape

**File:** `frontend/src/features/lab/types.ts`

New interfaces: `DialogueMessage`, `ActivityItem`, updated `LabState` with `dialogueMessages`, `pendingAction`, `masterPlan`, `activityItems`, `stageOutputs`, `selectedStage`, `activeStages`, `lastSequenceId`.

### G8. Rehydration Replays All 3 Cells

**File:** `frontend/src/features/lab/context/LabContext.tsx` (rehydration handler)

When `useRehydration` fetches the event ledger on mount, replay every event through the same router (G6):

- Left Cell: All `stream_chat` + `user_message` + `action_request` messages restored
- Center Cell: `plan_established` rebuilds checklist, `status_update` marks items done/active
- Right Cell: `render_output` populates stage outputs

**The UI after rehydration must be pixel-identical to the UI before refresh.**

---

## 🚫 Constraints

- **DO NOT** write Python/backend code. That's the Graph Agent's job.
- **DO NOT** invent new event types. Consume only what's in API_CONTRACTS.md v1.3.
- **DO NOT** remove existing components (CellRenderer, BlueprintCard, Tearsheet, PromoteModal). Reuse them in StageOutputs.
- **DO NOT** break the ReactFlow pipeline header. It continues to show stage status.
- **DO NOT** install npm packages on the host. All work runs in containers.
- If the UI needs data not in the contract, write a `CONTRACT_RFC.md` and halt.

## ✅ Definition of Done

1. 3-column grid layout visible at `http://localhost:5174`
2. DialoguePanel renders `stream_chat`, `user_message`, `action_request`, `error` events
3. ActivityTracker renders `plan_established` checklist and updates from `status_update`
4. StageOutputs renders `render_output` for selected stage
5. ChatInput sends messages via `POST /message` with optimistic rendering
6. Event router correctly routes all 7 event types to their target cells
7. Updated TypeScript interfaces for new state shape
8. Rehydration replays events into all 3 cells identically
9. All existing tests still pass (`docker compose exec frontend npx vitest run`)
10. Mock WS server (`ws://localhost:8002`) drives complete event flow through all components
