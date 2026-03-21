# 🔬 WORKER MISSION: Glass-Grid Agent (Stage-Row System)

**Branch:** `feature/glass-grid`
**Directory:** `../omc-lab-grid`
**Sprint:** 2.53 — Phase 7.2.1 Layout Foundations
**Role:** You are the Glass-Grid Agent. You are the sole developer in this worktree. You handle the **inner stage-row system** — types, state management, new StageRow components, and modifying existing sub-components (DialoguePanel, ActivityTracker, StageOutputs, ChatInput) to accept stage-filtering props.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` v1.4 §3.1 (Grid Layout — Per-Stage Rows) and §3.2 (Stage Row Behavior) as acceptance criteria.

---

## 🔌 YOUR ISOLATED ENVIRONMENT

| Resource | Value |
|---|---|
| Compose Project | `omc-grid` |
| Proxy (Traefik) | `http://localhost:8040` |
| Traefik Dashboard | `http://localhost:8094` |
| PostgreSQL (host access) | `localhost:5436` |
| PostgreSQL (container-internal) | `db:5432` |
| Frontend (Vite) | `http://localhost:5175` |

### How to Build & Run

```bash
# From this worktree root:
docker compose build
docker compose up -d

# Frontend dev (optional, for fast iteration):
cd frontend && npm install && npm run dev -- --port 5175
```

### docker-compose.override.yml (CREATE THIS FIRST)

```yaml
services:
  proxy:
    ports:
      - "8040:80"
      - "8094:8080"
  db:
    ports:
      - "5436:5432"
  backend:
    volumes:
      - ./backend/app:/app/app
      - ./backend/tests:/app/tests
      - agent-artifacts:/data/agent_artifacts
    environment:
      - POSTGRES_PORT=5432
  orchestrator:
    volumes:
      - ./backend/app:/app/app
      - ./backend/tests:/app/tests
      - agent-artifacts:/data/agent_artifacts
    environment:
      - POSTGRES_PORT=5432
  celery_worker:
    environment:
      - POSTGRES_PORT=5432
  prestart:
    environment:
      - POSTGRES_PORT=5432
```

Set `COMPOSE_PROJECT_NAME=omc-grid` in your `.env` or pass via CLI.

---

## 🎯 YOUR TASKS (Workstream H — Stage-Row System)

Execute these in the dependency order shown. A parallel `Glass-Shell` agent handles sidebar/drawer/LabHeader/whitespace. **DO NOT** touch any files listed in the Glass-Shell scope below.

### STEP 1: Type & State Foundation

#### H5: Add `stage` field to DialogueMessage
**File:** `frontend/src/features/lab/types.ts`
- Add `stage: LabStage` to the `DialogueMessage` interface (currently has: id, type, content, timestamp, sequence_id, actionPayload, resolved, resolvedOption)

**File:** `frontend/src/features/lab/context/LabContext.tsx`
- In `processEvent()`, wherever `DialogueMessage` objects are created, set `stage: event.stage`

#### H6: Stage Lifecycle State
**File:** `frontend/src/features/lab/types.ts`
- Add to `LabState`:
  - `staleStages: Set<LabStage>` — stages marked stale after revision
  - `completedStages: Set<LabStage>` — stages that have finished (distinct from activeStages which only tracks "ever activated")
- Add `revision_start` to `LabEventType` if an event type enum exists

**File:** `frontend/src/features/lab/context/LabContext.tsx`
- New reducer action types:
  - `MARK_STAGE_COMPLETE` — move stage from activeStages to completedStages
  - `MARK_STAGES_STALE` — add stage(s) to staleStages
  - `CLEAR_STALE` — remove stage(s) from staleStages
- Process `status_update` with `status: "COMPLETE"` → dispatch `MARK_STAGE_COMPLETE`
- Process `status_update` with `status: "STALE"` → dispatch `MARK_STAGES_STALE`
- Process new `revision_start` event → add divider to dialogueMessages + mark stale_stages
- Initialize `staleStages` and `completedStages` as `new Set()` in initial state

#### Status Helper
**File:** `frontend/src/features/lab/context/LabContext.tsx` (or a new utils file)
- Create helper: `getStageStatus(stage: LabStage, state: LabState) → 'pending' | 'active' | 'complete' | 'stale'`
- Logic:
  ```
  if (state.staleStages.has(stage)) return 'stale'
  if (state.activeStages.has(stage) && !state.completedStages.has(stage)) return 'active'
  if (state.completedStages.has(stage)) return 'complete'
  return 'pending'
  ```
- Export this so StageRowList can use it

### STEP 2: New Stage-Row Components

#### H7: StageRow Component
**File:** NEW `frontend/src/features/lab/components/StageRow.tsx`
- Props: `stage: LabStage`, `status: 'pending' | 'active' | 'complete' | 'stale'`, `isExpanded: boolean`, `onToggle: () => void`
- Structure:
  ```tsx
  <Box borderLeft="4px solid" borderLeftColor={statusColor} borderRadius="md" mb={3}>
    <StageRowHeader stage={stage} status={status} onToggle={onToggle} isExpanded={isExpanded} />
    {isExpanded && (
      <Grid templateColumns="2fr 1fr 1fr" gap={2} maxH="450px" p={3}>
        <GridItem overflowY="auto"><DialoguePanel stage={stage} /></GridItem>
        <GridItem overflowY="auto"><ActivityTracker stage={stage} /></GridItem>
        <GridItem overflowY="auto"><StageOutputs stage={stage} /></GridItem>
      </Grid>
    )}
  </Box>
  ```
- Status colors: `active` → `blue.500`, `complete` → `green.500`, `pending` → `gray.300`, `stale` → `orange.400`
- PENDING rows are not expandable (return header only with no click handler)

#### H8: StageRowHeader Component
**File:** NEW `frontend/src/features/lab/components/StageRowHeader.tsx`
- Props: `stage`, `status`, `isExpanded`, `onToggle`
- Shows: Stage number + human-readable name (e.g., "1. Business Understanding")
- Status indicators:
  - ACTIVE: pulsing blue dot or spinner
  - COMPLETE: green checkmark icon
  - PENDING: gray circle
  - STALE: orange/amber warning icon
- Expand/collapse chevron (right side)
- For COMPLETE stages: "Revise" button (small, secondary) — **stub only for now** (handler can be no-op; Phase 7.2.3 will wire it)
- For STALE stages: "Re-run" / "Keep" buttons — **stub only for now**
- Compact: ~48px height
- Collapsed COMPLETE/STALE rows should show a summary (e.g., "3 tasks, 2 outputs") if feasible

#### H9: StageRowList Component
**File:** NEW `frontend/src/features/lab/components/StageRowList.tsx`
- Import `ORDERED_STAGES` (the 7 DSLC stages in order) — define locally if no shared constant exists:
  ```ts
  const ORDERED_STAGES: LabStage[] = [
    'BUSINESS_UNDERSTANDING', 'DATA_ACQUISITION', 'PREPARATION',
    'EXPLORATION', 'MODELING', 'EVALUATION', 'DEPLOYMENT'
  ]
  ```
- Use `useLabContext()` to get state
- For each stage: compute status via `getStageStatus(stage, state)`
- Render `<StageRow>` for each stage
- Manage expanded state: `Set<LabStage>` — ACTIVE stage is always expanded
- Auto-expand on `status_update ACTIVE`: when a new stage becomes active, expand it, collapse previous active
- Auto-scroll: use `useRef` + `scrollIntoView({ behavior: 'smooth' })` when active stage changes
- User can manually expand/collapse any COMPLETE stage

### STEP 3: Modify Existing Sub-Components

#### H10a: Stage-Filtered DialoguePanel
**File:** `frontend/src/features/lab/components/DialoguePanel.tsx`
- Accept new prop: `stage?: LabStage`
- When `stage` is provided: `dialogueMessages.filter(m => m.stage === stage)`
- When `stage` is undefined: show all messages (backward compatibility during transition)
- Edge case: `error` events without a meaningful stage → show in the currently active stage's row. If `event.stage` is missing, default to the latest active stage.

#### H10b: Stage-Filtered ActivityTracker
**File:** `frontend/src/features/lab/components/ActivityTracker.tsx`
- Accept new prop: `stage?: LabStage`
- When `stage` is provided: filter to only that stage's tasks — render as a **flat task list** (no accordion)
- When `stage` is undefined: show the accordion of all stages (backward compat)
- Simplifies to: `activityItems.filter(item => item.stage === stage).map(item => <TaskRow />)`

#### H10c: Stage-Scoped StageOutputs
**File:** `frontend/src/features/lab/components/StageOutputs.tsx`
- Accept new prop: `stage?: LabStage`
- When `stage` is provided: always render `stageOutputs[stage]` directly
- Remove the selection/fallback logic when in stage-scoped mode
- Remove the stage name heading (the StageRowHeader already shows it)

#### H10d: Stage-Scoped ChatInput
**File:** `frontend/src/features/lab/components/ChatInput.tsx`
- Accept new prop: `stage?: LabStage`
- When `stage` is provided: include `stage` in the POST body: `{ content, stage }`
- ChatInput should be disabled for PENDING stages
- For ACTIVE stages: enabled as normal
- For COMPLETE stages: **hidden by default**. The "Revise" button in StageRowHeader will make it visible (Phase 7.2.3 will wire this — for now, just support the prop and send stage in the POST body)

### STEP 4: Wire Into LabSessionView + Cleanup

#### A5/A7: Replace LabGrid with StageRowList
**File:** `frontend/src/features/lab/LabSessionView.tsx`
- Replace `<LabGrid />` with `<StageRowList />`
- Keep the session heading (goal text, status badge) as a compact bar at top
- Remove the wrapper `<Box flex={1}>` if StageRowList handles its own layout

#### Cleanup: Delete Replaced Components
**Files to DELETE:**
- `frontend/src/features/lab/components/LabGrid.tsx` — replaced by StageRowList
- `frontend/src/features/lab/components/LabStageRow.tsx` — unused legacy, replaced by StageRow
- Remove any imports of these deleted files from other components

---

## 🚫 SCOPE LOCK — DO NOT TOUCH THESE FILES

These files belong to the **Glass-Shell** agent working in parallel. Touching them will cause merge conflicts.

| File | Owner |
|---|---|
| `frontend/src/components/Common/Sidebar.tsx` | Glass-Shell |
| `frontend/src/components/Common/SidebarItems.tsx` | Glass-Shell |
| `frontend/src/routes/_layout.tsx` | Glass-Shell |
| `frontend/src/routes/_layout/lab.tsx` | Glass-Shell |
| `frontend/src/features/lab/components/LabHeader.tsx` | Glass-Shell (will delete) |
| Any `backend/` files | Graph-Stale agent |

The Glass-Shell agent also modifies `LabDashboard.tsx` (session drawer). You MAY need to import `StageRowList` into `LabSessionView.tsx` which Glass-Shell also touches (to remove LabHeader). **This is the ONE expected merge point** — the Supervisor will resolve it during integration. Just make your changes to `LabSessionView.tsx` cleanly.

If you encounter a situation where you MUST modify a locked file, write a `CONTRACT_RFC.md` in this worktree root explaining why, and halt.

---

## ✅ ACCEPTANCE CRITERIA

Rehydrate an existing completed session and verify:

1. Each DSLC stage appears as its own collapsible row with colored left border
2. ACTIVE stage row is expanded with blue border; COMPLETE rows collapsed with green border; PENDING rows gray
3. Expanding a COMPLETE row shows ONLY that stage's dialogue messages, tasks, and outputs
4. Dialogue panel in each row shows only messages where `event.stage` matches the row's stage
5. ActivityTracker in each row shows a flat task list for that stage only (no 7-stage accordion)
6. StageOutputs in each row shows outputs for that stage only
7. ChatInput sends `stage` param in POST body when `stage` prop is provided
8. Page auto-scrolls to bring the active stage row into view
9. Stage row headers show status indicators (spinner, check, gray circle)
10. Expanded rows have max-height 450px with internal column scrolling
11. `npx tsc --noEmit` passes
12. `npx biome check src/` passes (or only pre-existing warnings)

---

## 📋 VERIFICATION COMMANDS

```bash
cd frontend
npx tsc --noEmit
npx biome check src/
npm run build
```

---

## ⛔ CONTRACT BOUNDARY

If any of your tasks are blocked by an API contract issue, write a `CONTRACT_RFC.md` in this worktree root and halt. Do NOT improvise around contract boundaries.
