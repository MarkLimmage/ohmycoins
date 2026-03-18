# Sprint 2.51: Conversational Scientific Grid (Phase 7) — IN PROGRESS

**Status:** Parallel Worktree Sprint
**Base Commit:** `7fa56f6`
**Contract:** API_CONTRACTS.md v1.3

## Architecture

3-column Conversational Scientific Grid: Dialogue (Left) | Activity Tracker (Center) | Stage Outputs (Right).
7 event types, 4 interrupts, mandatory scope confirmation, POST /message, circuit breaker escalation.

## Worktree Topology

| Agent | Branch | Directory | Proxy Port | DB Port |
|-------|--------|-----------|------------|---------|
| Graph | `feature/langgraph-orchestrator` | `../omc-lab-graph` | 8020 | 5434 |
| Glass | `feature/react-frontend` | `../omc-lab-ui` | 8030 | 5435 |

## Workstream F (Graph Agent — Backend)

| ID | Task | Status |
|----|------|--------|
| F1 | Wire `scope_confirmation` interrupt (mandatory) | 🔄 |
| F2 | Wire `model_selection` interrupt | 🔄 |
| F3 | Emit reasoning as `stream_chat` from every node | 🔄 |
| F4 | Emit `plan_established` after scope confirmation | 🔄 |
| F5 | Add `task_id` to `status_update` events | 🔄 |
| F6 | POST `/message` endpoint with `sequence_id` guarantee | 🔄 |
| F7 | Circuit breaker → `action_request` escalation | 🔄 |

## Workstream G (Glass Agent — Frontend)

| ID | Task | Status |
|----|------|--------|
| G1 | 3-column CSS Grid (350px | 1fr | 300px) | 🔄 |
| G2 | DialoguePanel (stream_chat + user_message + action_request + error) | 🔄 |
| G3 | ActivityTracker (plan_established + status_update with task_id) | 🔄 |
| G4 | StageOutputs (render_output with mime-type dispatch) | 🔄 |
| G5 | ChatInput (POST /message, optimistic rendering) | 🔄 |
| G6 | Event router refactor (3-cell routing by event_type) | 🔄 |
| G7 | Updated state shape (LabSession with 3 cell arrays) | 🔄 |
| G8 | Rehydration replays all 3 cells | 🔄 |

## Mock Server

`mock_ws_v13.py` on port 8002 — broadcasts full v1.3 event sequence for Glass Agent development.

---

# Phase 5.5: Lab 2.0 Parallel Sprint — COMPLETE

**Status:** Merged & Validated
**Date:** 2025-03-17
**Base Commit:** `2cd7e33` → **Final:** `7acf69b`

## Merged Workstreams (D→A→B→C→E)

| Stream | Branch | Scope | Merge |
|--------|--------|-------|-------|
| D (Safety) | `integration/bridge-safe` | Circuit breaker, zero-variance kill-switch, statistical health gates | Fast-forward |
| A (Messaging) | `integration/bridge-msg` | EventLedger, sequence_id/timestamp, `emit_event()` | Retry (IndentationError fixed) |
| B (HITL) | `integration/bridge-hitl` | `action_request` events, APPROVE/REJECT resume, AWAITING_APPROVAL | Clean merge |
| C (Production) | `integration/bridge-prod` | Dagger-MLflow bridge, disposable script pattern, Parquet caching | Scaffolding only |
| E (Glass) | `integration/bridge-glass` | Scientific Grid refactor, mime-type dispatcher, useRehydration hook | Retry (TS errors fixed) |

## Post-Merge Validation

- **Ruff:** All checks passed (0 errors)
- **TypeScript:** `tsc --noEmit` clean
- **Pytest:** 1023 passed, 17 skipped, 6 failed (pre-existing test isolation bugs)

## Known Pre-existing Test Issues

- `test_llm_key_security.py` (3 tests): Duplicate provider check — tests don't isolate credential creation per-test
- `test_alerting.py` (3 tests): Silent rollback in conftest cleanup leaves AlertLog records across test runs
