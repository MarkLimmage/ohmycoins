# 🪟 WORKER MISSION: Glass-Shell Agent (Layout Foundations)

**Branch:** `feature/glass-shell`
**Directory:** `../omc-lab-shell`
**Sprint:** 2.53 — Phase 7.2.1 Layout Foundations
**Role:** You are the Glass-Shell Agent. You are the sole developer in this worktree. You handle the **outer layout frame** — sidebar, session drawer, whitespace, and LabHeader removal.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` v1.4 §3.3 (Sidebar & Session Drawer) and §3.4 (ReactFlow Deprecation) as acceptance criteria.

---

## 🔌 YOUR ISOLATED ENVIRONMENT

| Resource | Value |
|---|---|
| Compose Project | `omc-shell` |
| Proxy (Traefik) | `http://localhost:8030` |
| Traefik Dashboard | `http://localhost:8093` |
| PostgreSQL (host access) | `localhost:5435` |
| PostgreSQL (container-internal) | `db:5432` |
| Frontend (Vite) | `http://localhost:5174` |

### How to Build & Run

```bash
# From this worktree root:
docker compose build
docker compose up -d

# Frontend dev (optional, for fast iteration):
cd frontend && npm install && npm run dev -- --port 5174
```

### docker-compose.override.yml (CREATE THIS FIRST)

```yaml
services:
  proxy:
    ports:
      - "8030:80"
      - "8093:8080"
  db:
    ports:
      - "5435:5432"
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

Set `COMPOSE_PROJECT_NAME=omc-shell` in your `.env` or pass via CLI.

---

## 🎯 YOUR TASKS (Workstream H — Layout Shell)

You own **only** the outer layout frame. A parallel `Glass-Grid` agent handles the inner stage-row components. **DO NOT** touch any files listed in the Glass-Grid scope below.

### H1: Collapsible Desktop Sidebar
**Files:** `frontend/src/components/Common/Sidebar.tsx`, `frontend/src/components/Common/SidebarItems.tsx`
- Add collapse/expand toggle (chevron button at bottom of sidebar)
- Collapsed: 48px wide, icon-only rail
- Expanded: 200px wide, icons + text (reduced from current ~320px `minW=xs`)
- Persist preference in `localStorage` key `sidebar-collapsed`
- `SidebarItems.tsx`: conditionally render icon-only when collapsed, icon+text when expanded
- The sidebar must NOT break navigation — icons remain visible when collapsed

### H2: Reduce Whitespace / Maximize Grid Area
**Files:** `frontend/src/routes/_layout.tsx`, `frontend/src/routes/_layout/lab.tsx`, `frontend/src/features/lab/LabDashboard.tsx`
- `lab.tsx`: Change `py={8}` to `py={2}` or `py={0}`
- `_layout.tsx`: Reduce `p={4}` on the Outlet flex container. Either make it route-conditional for the lab route, or set `p={0}` and let each page manage its own padding
- `LabDashboard.tsx`: Remove or reduce `gap={6}` on outer VStack, minimize heading area
- **IMPORTANT**: Other pages (Dashboard, Collectors, Floor) share `_layout.tsx`. Test that they still look acceptable after padding changes. If in doubt, make the padding conditional for the `/lab` route only.

### H3: Session List → Drawer Overlay
**Files:** `frontend/src/features/lab/LabDashboard.tsx`, NEW `frontend/src/features/lab/components/SessionDrawer.tsx`
- Remove inline `<SessionList>` from LabDashboard (currently in a `<Box w="350px">`)
- Create `SessionDrawer.tsx`: Chakra `DrawerRoot` with `placement="start"`, width 350px
- Trigger: A button in the Lab page header area (e.g., FiList icon) with active session count badge
- Drawer contents: `SessionList` + `SessionCreateForm` + "New Session" button at top
- Pass `selectedId`, `onSelect`, `onDelete` props through to SessionList as before
- Drawer overlays content (does NOT push the grid)
- Auto-close on session select

### H4: Remove LabHeader (ReactFlow Pipeline)
**Files:** `frontend/src/features/lab/components/LabHeader.tsx` (DELETE), `frontend/src/features/lab/LabSessionView.tsx`
- Delete `LabHeader.tsx` entirely
- In `LabSessionView.tsx`: remove `<LabHeader />` import and JSX usage
- **BEFORE DELETING**: Verify no other route/component imports `LabHeader`. If others do, only remove the Lab usage.
- Do NOT remove `reactflow` from `package.json` — other pages may use it. Only remove the import from Lab components.
- This recovers 150px of vertical space

### Cleanup
- After H4, verify the build: `npx tsc --noEmit` and `npx biome check src/`

---

## 🚫 SCOPE LOCK — DO NOT TOUCH THESE FILES

These files belong to the **Glass-Grid** agent working in parallel. Touching them will cause merge conflicts.

| File | Owner |
|---|---|
| `frontend/src/features/lab/types.ts` | Glass-Grid |
| `frontend/src/features/lab/context/LabContext.tsx` | Glass-Grid |
| `frontend/src/features/lab/components/DialoguePanel.tsx` | Glass-Grid |
| `frontend/src/features/lab/components/ActivityTracker.tsx` | Glass-Grid |
| `frontend/src/features/lab/components/StageOutputs.tsx` | Glass-Grid |
| `frontend/src/features/lab/components/ChatInput.tsx` | Glass-Grid |
| `frontend/src/features/lab/components/LabGrid.tsx` | Glass-Grid (will delete) |
| `frontend/src/features/lab/components/LabStageRow.tsx` | Glass-Grid (will delete) |
| Any `backend/` files | Graph-Stale agent |

If you encounter a situation where you MUST modify a locked file, write a `CONTRACT_RFC.md` in this worktree root explaining why, and halt.

---

## ✅ ACCEPTANCE CRITERIA

1. Sidebar collapses to 48px icon rail on toggle; expands to 200px with text
2. Sidebar collapse state persists across page refreshes (localStorage)
3. Other pages (Dashboard, Collectors, Floor) still render correctly with sidebar changes
4. Session drawer slides out from left, 350px wide, overlaying content
5. Selecting a session in the drawer loads it and closes the drawer
6. "New Session" button in drawer works
7. No ReactFlow pipeline visible on the Lab page (LabHeader removed)
8. Lab page has minimal whitespace — grid area is maximized
9. `npx tsc --noEmit` passes
10. `npx biome check src/` passes (or only pre-existing warnings)

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
