# Current Sprint: 2.44

**Status**: IN PROGRESS
**Objective**: The Lab — Live Session Experience
**Previous Sprint**: 2.43 (Signal Data Model — COMPLETED)

## Context

Sprint 2.43 built the signal data model and query API for Lab agents. This sprint makes the Lab usable from the UI: background session execution, WebSocket streaming, and a full Lab page with session management.

## Tasks

1. [x] **Track A — Backend: Background Execution + WebSocket Streaming**
   - A1: Added `llm_credential_id` to `AgentSessionCreate` schema
   - A2: Created `AgentRunner` — background session execution via `asyncio.create_task`, Redis pub/sub streaming
   - A3: WebSocket endpoint `/ws/agent/{session_id}/stream` — historical replay + live pub/sub relay
   - A4: Updated session creation route to use runner (non-blocking)
   - A5: Wired runner shutdown into app lifespan
   - A6: 24 new tests (runner unit tests, WS auth/replay/streaming, session API)
   - mypy --strict + ruff clean

2. [x] **Track B — Frontend: Lab Page + Session Management**
   - B1: Lab route at `/lab` following enrichment pattern
   - B2: Added "The Lab" to sidebar with FiTerminal icon
   - B3: TanStack Query hooks for sessions, credentials
   - B4: `useLabWebSocket` hook with dedup and finite lifecycle
   - B5: LabDashboard — two-panel layout (session list + AgentTerminal)
   - B6: SessionCreateForm modal with goal + LLM provider selector
   - B7: SessionList with status badges, timestamps, selection
   - B8: Regenerated OpenAPI client with `llm_credential_id` field
   - TypeScript type-check + Biome lint clean

## Verification

- [x] Full test suite: 925 passed (23 new), 9 failed (pre-existing), 4 errors (pre-existing)
- [x] mypy --strict clean
- [x] ruff check + ruff format clean
- [x] npm run type-check clean
- [x] npm run lint clean (1 pre-existing error in eventBus.ts)
