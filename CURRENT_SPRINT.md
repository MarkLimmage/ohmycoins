# Sprint 2.52: v1.3.1 Enforcement — Gap Remediation

**Status:** COMPLETE — Merged to main at `8efcab0`
**Base Commit:** `a46af81`
**Contract:** API_CONTRACTS.md v1.3.1 (Enforcement Addendum)
**Predecessor:** Sprint 2.51 (Phase 7 initial implementation — merged, production-tested, gaps identified)

## Context

Sprint 2.51 delivered the initial v1.3 Conversational Scientific Grid. Production testing on 2026-03-18 revealed **6 Severity-A contract violations** and **5 Severity-B UX deficits**. Root causes are split between backend (silent fallbacks, missing events, duplicate generic interrupts) and frontend (no dedup, wrong colors, orphan buttons, disabled input). This sprint remediates all gaps.

## Architecture

3-column Conversational Scientific Grid (unchanged). This sprint fixes enforcement, not architecture.

## Worktree Topology

| Agent | Branch | Directory | Proxy Port | DB Port | Traefik Dashboard |
|-------|--------|-----------|------------|---------|-------------------|
| Main (Supervisor) | `main` | `/home/mark/claude/ohmycoins` | 8010 | 5433 | 8091 |
| Graph | `fix/graph-enforcement` | `../omc-lab-graph` | 8020 | 5434 | 8092 |
| Glass | `fix/glass-enforcement` | `../omc-lab-ui` | 8030 | 5435 | 8093 |

## Workstream F (Graph Agent — Backend Enforcement)

| ID | Task | Enforcement Rule | Status |
|----|------|-----------------|--------|
| F1 | Scope confirmation fallback → `circuit_breaker_v1` escalation | E1 (No Silent Fallbacks) | ✅ |
| F2 | Runner publishes node `pending_events` instead of generic interrupt | E2 (Node Events Priority) | ✅ |
| F3 | Add `task_id` to ALL `status_update` payloads | E3 (task_id Mandatory) | ✅ |
| F4 | Emit `plan_established` even on fallback/error paths | E4 (plan_established Always) | ✅ |
| F5 | Deduplicate runner action_request when node already emitted one | E2 (Node Events Priority) | ✅ |
| F6 | Fix `status_update` stage progression (correct stage assignments) | E7 (Pipeline Colors) | ✅ |

### F1 Detail: Scope Confirmation Fallback
**File:** `backend/app/services/agent/nodes/clarification.py`
**Current:** LLM failure caught → emits stub `stream_chat` "Fallback due to error" → continues silently.
**Required:** LLM failure → emit `action_request` with `action_id: "circuit_breaker_v1"`, `stage: "BUSINESS_UNDERSTANDING"`, containing error details, suggestions ("Check API key", "Retry with different provider"), and options `["CHOOSE_SUGGESTION", "PROVIDE_GUIDANCE", "ABORT_SESSION"]`. Also emit a default `plan_established` (E4).

### F2 Detail: Runner Node Event Priority
**File:** `backend/app/services/agent/runner.py`
**Current:** After streaming, runner checks `state_snapshot.next` for interrupts and emits a generic `action_request` with auto-generated `action_id: "approve_{node_name}"`. This OVERWRITES the structured events the node already emitted.
**Required:** After streaming, runner checks if the node's `pending_events` list contains an `action_request`. If yes, the runner MUST NOT emit its own generic action_request. It should still set session status to AWAITING_APPROVAL and save Redis state, but the action_request event is the node's, not the runner's.

### F3 Detail: task_id on status_update
**Files:** All node files emitting `status_update` events.
**Current:** Many `status_update` events lack `task_id`, making them un-routable in the Activity Tracker.
**Required:** Every `status_update` MUST include `task_id` matching the `plan_established` task list. Use the same task IDs defined in the plan: `fetch_price_data`, `validate_quality`, `compute_technical_indicators`, `train_models`, `evaluate_metrics`, `generate_report`, etc.

### F4 Detail: Default plan_established
**File:** `backend/app/services/agent/nodes/clarification.py` (scope_confirmation_node)
**Current:** `plan_established` only emits on successful scope parsing.
**Required:** On LLM failure, emit a default `plan_established` with generic task list:
```json
{"plan": [
  {"stage": "DATA_ACQUISITION", "tasks": [{"task_id": "fetch_data", "label": "Fetch market data"}]},
  {"stage": "PREPARATION", "tasks": [{"task_id": "prepare_data", "label": "Prepare and validate data"}]},
  {"stage": "EXPLORATION", "tasks": [{"task_id": "analyze_data", "label": "Exploratory analysis"}]},
  {"stage": "MODELING", "tasks": [{"task_id": "train_models", "label": "Train ML models"}]},
  {"stage": "EVALUATION", "tasks": [{"task_id": "evaluate_models", "label": "Evaluate model performance"}]},
  {"stage": "DEPLOYMENT", "tasks": [{"task_id": "deploy_model", "label": "Generate report and deploy"}]}
]}
```

## Workstream G (Glass Agent — Frontend Enforcement)

| ID | Task | Enforcement Rule | Status |
|----|------|-----------------|--------|
| G1 | Implement `sequence_id` deduplication in event router | E5 (Dedup Mandatory) | ✅ (already done) |
| G2 | Render `action_request` as inline cards per `action_id` subtype | E6 (Inline HITL Only) | ✅ |
| G3 | Remove legacy "Resume Workflow (HITL)" button | E6 (Inline HITL Only) | ✅ |
| G4 | Fix pipeline node colors (COMPLETE=green, ACTIVE=blue, PENDING=gray) | E7 (Pipeline Colors) | ✅ |
| G5 | Enable ChatInput during RUNNING and AWAITING_APPROVAL sessions | E8 (ChatInput Enabled) | ✅ |
| G6 | Stage Outputs driven by selected stage, not hardcoded | E9 (Stage Selection) | ✅ (already done) |
| G7 | Fix rehydration/WS overlap (pass `after_seq` to WS connect) | E5 (Dedup Mandatory) | ✅ (already done) |
| G8 | Differentiate message senders (agent vs system vs user styling) | Contract §2.1/2.2 | ✅ |

### G1 Detail: Sequence Dedup
**File:** `frontend/src/features/lab/context/LabContext.tsx`
**Current:** Events from rehydration and live WS are both fed into the reducer without dedup, causing duplicate messages.
**Required:** Track `lastSequenceId` in state. In the reducer, discard any event where `sequence_id ≤ lastSequenceId`. On rehydration, set `lastSequenceId` to max of replayed events. On WS reconnect, pass `?after_seq={lastSequenceId}` to prevent overlap.

### G2 Detail: Inline HITL Cards
**File:** `frontend/src/features/lab/components/DialoguePanel.tsx` + new card components
**Current:** `action_request` events are either ignored in the Dialogue or shown as an external `ActionRequestBanner`.
**Required:** Render `action_request` inline in the Dialogue message list, with subtype-specific UI:
- `scope_confirmation_v1`: Show interpretation table + CONFIRM_SCOPE/ADJUST_SCOPE buttons
- `approve_modeling_v1`: Show blueprint details + APPROVE/REJECT/EDIT buttons
- `model_selection_v1`: Show model comparison table + radio select
- `circuit_breaker_v1`: Show error + suggestions list + option buttons

### G4 Detail: Pipeline Colors
**File:** `frontend/src/features/lab/components/LabGrid.tsx` (or the ReactFlow node rendering)
**Current:** COMPLETE stages show yellow (`rgb(254, 252, 191)` / `rgb(214, 158, 46)` border). ACTIVE shows blue. PENDING shows gray.
**Required:** COMPLETE = green background (`#C6F6D5`) with green border (`#38A169`). ACTIVE = blue background with blue border (`#3182CE`) + bold + box-shadow. PENDING = gray (`#EDF2F7`).

## Integration Protocol

Per `END_OF_SPRINT_PROTOCOL.md`:
1. Each agent tests in isolation in its worktree
2. Supervisor verifies: `ruff check app/` (Graph), `tsc --noEmit` + `biome check` (Glass)
3. Merge Glass first (port conflict is less risky), then Graph
4. `docker-compose.override.yml`: Always revert to Main's ports on merge
5. Post-merge: `docker compose down && docker compose up -d --build`
6. Production deploy: push to `origin main` → GitHub Actions runner on `192.168.0.241`

## Acceptance Criteria

A session starting with "Analyze BTC sentiment from news data" MUST produce:
1. Scope confirmation card inline in Dialogue (or circuit_breaker card if LLM fails)
2. `plan_established` populating the Activity Tracker with stage-grouped task checklist
3. All `status_update` events with `task_id` updating checklist items
4. No duplicate messages in Dialogue after page refresh
5. Pipeline: completed stages green, active blue, pending gray
6. ChatInput enabled during RUNNING/AWAITING_APPROVAL
7. Stage Outputs responding to pipeline clicks
8. Zero "Resume Workflow (HITL)" buttons visible

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
