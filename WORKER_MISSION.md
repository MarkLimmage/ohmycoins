# 🪟 WORKER MISSION: Glass Agent (v1.3.1 Enforcement Sprint)

**Branch:** `fix/glass-enforcement`
**Directory:** `../omc-lab-ui`
**Sprint:** 2.52 — Gap Remediation
**Role:** You are the Glass Agent. You are the sole developer in this worktree.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` (v1.3.1) §0.1 Enforcement Rules as the strict acceptance criteria.

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

# Type checking
docker compose exec frontend npx tsc --noEmit

# Lint checking
docker compose exec frontend npx biome check src/
```

### Using the Mock WebSocket Server

```bash
cd /home/mark/claude/ohmycoins
python mock_ws_v13.py
# → Listening on ws://localhost:8002
```

---

## 🎯 Mission: Fix 8 Frontend Enforcement Violations

Sprint 2.51 production testing revealed that the Scientific Grid has 8 frontend gaps. Your job is to fix all of them. The 3-column layout, event routing, and component structure from Sprint 2.51 are CORRECT — you are fixing enforcement violations, not rebuilding.

---

## 📋 Workstream G: Enforcement Fixes (8 Tasks)

### G1. Sequence ID Deduplication in Event Router

**File:** `frontend/src/features/lab/context/LabContext.tsx`
**Enforcement Rule:** E5 — Dedup Mandatory

**Problem:** Events from rehydration and live WS are both fed into the reducer without dedup, causing duplicate messages (same `stream_chat` appearing 2-3 times).

**Fix:**
1. Add `lastSequenceId: number` to `LabState` (if not already present)
2. In the reducer's event handling, check: if `event.sequence_id <= state.lastSequenceId`, discard the event (return state unchanged)
3. On successful event processing, update `lastSequenceId = Math.max(state.lastSequenceId, event.sequence_id)`
4. On rehydration completion, set `lastSequenceId` to the max `sequence_id` from the replayed events

### G2. Render `action_request` as Inline HITL Cards

**Files:** `frontend/src/features/lab/components/DialoguePanel.tsx`, new files per subtype
**Enforcement Rule:** E6 — Inline HITL Only

**Problem:** `action_request` events are either ignored in the Dialogue or shown as an external `ActionRequestBanner`. They must render inline.

**Fix:**
1. In `DialoguePanel`, when rendering a message with `event_type: "action_request"`, dispatch to a subtype component based on `payload.action_id`:
   - `scope_confirmation_v1` → `ScopeConfirmationCard` (shows interpretation table + CONFIRM/ADJUST buttons)
   - `approve_modeling_v1` → `ApprovalCard` (shows blueprint + APPROVE/REJECT/EDIT buttons)
   - `model_selection_v1` → `ModelSelectionCard` (shows model comparison + radio select)
   - `circuit_breaker_v1` → `CircuitBreakerCard` (shows error + suggestions + option buttons)
2. Each card calls the appropriate backend endpoint (`/approve`, `/clarifications`, `/choices`) on user action
3. After user responds, mark the card as "resolved" (gray out buttons, show chosen action)
4. Reuse existing `AgentService.approveRequest` for approve/reject flows

### G3. Remove Legacy "Resume Workflow (HITL)" Button

**File:** `frontend/src/features/lab/LabSessionView.tsx` (line ~24)
**Enforcement Rule:** E6 — Inline HITL Only

**Problem:** There's a standalone `<button>Resume Workflow (HITL)</button>` rendered outside the grid between the pipeline and the 3-column area.

**Fix:** Remove the button entirely. All HITL is now inline in the Dialogue via G2.

### G4. Fix Pipeline Node Colors

**File:** `frontend/src/features/lab/components/LabHeader.tsx` (lines ~132-133)
**Enforcement Rule:** E7 — Pipeline Node Colors

**Problem:** COMPLETE stages show yellow background (`#FEFCBF`) with yellow border (`#D69E2E`). Should be green.

**Fix:**
- COMPLETE: background `#C6F6D5` (green-100), border `#38A169` (green-500)
- ACTIVE: background `#BEE3F8` (blue-100), border `#3182CE` (blue-500), bold, box-shadow `0 0 0 2px #3182CE`
- PENDING: background `#EDF2F7` (gray-100), border `#DDD` (gray-300)

### G5. Enable ChatInput During Active Sessions

**File:** `frontend/src/features/lab/components/ChatInput.tsx` (line ~51)
**Enforcement Rule:** E8 — ChatInput Enabled

**Problem:** `isDisabled = !state.isConnected || state.isDone || isLoading` — but `state.isDone` may be true even when session is AWAITING_APPROVAL.

**Fix:** The input should be enabled when:
- Session status is RUNNING or AWAITING_APPROVAL
- WebSocket is connected
- Not currently sending a message

Disabled when: COMPLETED, FAILED, CANCELLED, or WS disconnected.

### G6. Stage Outputs Driven by Selection

**File:** `frontend/src/features/lab/components/StageOutputs.tsx` (lines ~35-44)
**Enforcement Rule:** E9 — Stage Outputs Selection

**Problem:** Right Cell may not respond to pipeline node clicks for stage selection.

**Fix:** Ensure `StageOutputs` reads `selectedStage` from LabContext (set when user clicks a pipeline node in LabHeader). Default to the most recently active stage. Update `LabHeader` to dispatch `SELECT_STAGE` action on node click if not already wired.

### G7. Fix Rehydration/WS Overlap

**File:** `frontend/src/features/lab/hooks/useLabWebSocket.ts` (line ~72-73)
**Enforcement Rule:** E5 — Dedup Mandatory

**Problem:** After rehydration replays events, the WS may deliver the same events again if `after_seq` is not correctly passed.

**Fix:** Ensure `useLabWebSocket` reads `lastSequenceId` from LabContext state and passes it as `?after_seq={lastSequenceId}` in the WS URL. The WS should only connect AFTER rehydration completes (not in parallel).

### G8. Differentiate Message Senders

**File:** `frontend/src/features/lab/components/DialoguePanel.tsx`
**Enforcement Rule:** Contract §2.1/2.2

**Problem:** All messages show "System Agent" with the same CPU icon regardless of sender.

**Fix:**
- `stream_chat` → Agent bubble (left-aligned, blue accent, robot icon, "Agent")
- `user_message` → User bubble (right-aligned, gray background, user icon, "You")
- `action_request` → HITL card (full-width, orange accent) — handled by G2
- `error` → Error card (full-width, red accent, alert icon)

---

## 🚫 Constraints

- **DO NOT** write Python/backend code. That's the Graph Agent's job.
- **DO NOT** invent new event types. Consume only what's in API_CONTRACTS.md v1.3.1.
- **DO NOT** remove existing components (CellRenderer, BlueprintCard, Tearsheet, PromoteModal). Reuse them.
- **DO NOT** break the ReactFlow pipeline header. Modify only the node coloring logic.
- **DO NOT** install npm packages on the host. All work runs in containers.

## ✅ Acceptance Criteria

After all 8 fixes, refreshing a completed session must show:
1. Zero duplicate messages in Dialogue
2. HITL cards rendered inline (no external buttons/banners)
3. Pipeline: green for complete, blue for active, gray for pending
4. ChatInput enabled during RUNNING sessions
5. Stage Outputs change when clicking pipeline nodes
6. Different visual styling for agent vs user vs system messages
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
