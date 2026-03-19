# 🧠 WORKER MISSION: Graph Agent (v1.3.1 Enforcement Sprint)

**Branch:** `fix/graph-enforcement`
**Directory:** `../omc-lab-graph`
**Sprint:** 2.52 — Gap Remediation
**Role:** You are the Graph Agent. You are the sole developer in this worktree.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` (v1.3.1) §0.1 Enforcement Rules as the strict acceptance criteria.

---

## 🔌 YOUR ISOLATED ENVIRONMENT

| Resource | Value |
|---|---|
| Compose Project | `omc-graph` |
| Proxy (Traefik) | `http://localhost:8020` |
| Traefik Dashboard | `http://localhost:8092` |
| PostgreSQL (host access) | `localhost:5434` |
| PostgreSQL (container-internal) | `db:5432` |
| Redis | container-internal only |
| Backend (FastAPI) | `http://localhost:8000` (inside container) |

### How to Build & Run

```bash
# From this worktree root:
docker compose build
docker compose up -d
docker compose logs -f backend
```

### How to Run Tests (INSIDE CONTAINERS)

All test execution MUST happen inside containers.

```bash
# Run backend tests
docker compose exec backend pytest

# Run specific test file
docker compose exec backend pytest tests/services/agent/test_runner.py -v

# Lint checking
docker compose exec backend ruff check app/

# Type checking (if configured)
docker compose exec backend mypy app/ --ignore-missing-imports
```

---

## 🎯 Mission: Fix 6 Backend Enforcement Violations

Sprint 2.51 production testing revealed that the LangGraph workflow has 6 backend gaps. The scope confirmation fails silently, the runner overwrites structured node events with generic ones, status_update events lack task_id, and plan_established isn't emitted on error paths. Your job is to fix all of them.

---

## 📋 Workstream F: Enforcement Fixes (6 Tasks)

### F1. Scope Confirmation Fallback → Circuit Breaker Escalation

**File:** `backend/app/services/agent/nodes/clarification.py`
**Enforcement Rule:** E1 — No Silent Fallbacks

**Problem:** When the LLM call fails in `scope_confirmation_node` (e.g., invalid API key), the except block emits a stub `stream_chat` with "Fallback due to error" and continues silently. This cascades: no scope confirmation → no `plan_established` → empty Activity Tracker → broken HITL.

**Fix:** In the except block of `scope_confirmation_node`:
1. Do NOT emit a stub `stream_chat` with fallback text
2. Instead, emit an `action_request` event with:
   ```python
   {
       "event_type": "action_request",
       "stage": "BUSINESS_UNDERSTANDING",
       "payload": {
           "action_id": "circuit_breaker_v1",
           "description": "I encountered an error while analyzing your request. I need your guidance to proceed.",
           "stage": "BUSINESS_UNDERSTANDING",
           "attempts": 1,
           "last_error": str(e),  # The LLM error message
           "suggestions": [
               "Check your LLM API key in Settings → LLM Credentials",
               "Try a different LLM provider (Google Gemini, Anthropic)",
               "Retry the session after updating credentials"
           ],
           "options": ["CHOOSE_SUGGESTION", "PROVIDE_GUIDANCE", "ABORT_SESSION"]
       }
   }
   ```
3. Also emit a default `plan_established` event (see F4) so the Activity Tracker is not empty
4. Set `awaiting_scope_confirmation: True` so the workflow pauses

### F2. Runner Publishes Node `pending_events` — No Generic Overwrite

**File:** `backend/app/services/agent/runner.py`
**Enforcement Rule:** E2 — Node Events Take Priority

**Problem:** After streaming the workflow, the runner checks `state_snapshot.next` for interrupts. If found, it generates a GENERIC `action_request` with `action_id: "approve_{node_name}"` and description "Workflow paused before step: {node_name}". This overwrites the STRUCTURED events that the node already emitted (e.g., `scope_confirmation_v1` with interpretation details).

**Fix:** In the interrupt detection block (`state_snapshot.next` check):
1. Before emitting the generic action_request, check if **any `action_request` event was already published** during the streaming loop (i.e., from the node's `pending_events`)
2. If yes: SKIP the generic `action_request` emission. The node's structured event is already in the frontend.
3. Still proceed with:
   - Setting session status to `AWAITING_APPROVAL` in the DB
   - Saving the approval state to Redis (with `approval_needed: True`, `pending_approvals`)
   - Emitting the `status_update` with `AWAITING_APPROVAL`
4. If no node-level `action_request` was emitted: proceed with the generic one as fallback

Implementation hint: Track a boolean `node_emitted_action_request = False` in the streaming loop. When processing `pending_events`, if any event has `event_type == "action_request"`, set it to `True`. Then use this flag in the interrupt block.

### F3. Add `task_id` to ALL `status_update` Payloads

**Files:**
- `backend/app/services/agent/nodes/lab_nodes.py` — The `_emit_status_update()` helper and all direct emissions
- `backend/app/services/agent/langgraph_workflow.py` — Any inline status_update emissions
- Any other node files emitting status_update events

**Enforcement Rule:** E3 — task_id Mandatory

**Problem:** Many `status_update` events lack `task_id`, making them un-routable in the Activity Tracker. They create orphan entries like "Starting data retrieval..." that don't match any checklist item.

**Fix:**
1. Every `status_update` emission MUST include `task_id` in the payload
2. Use task IDs that match the `plan_established` task list:

| Stage | task_id Values |
|-------|---------------|
| DATA_ACQUISITION | `fetch_price_data`, `fetch_sentiment`, `fetch_on_chain` |
| PREPARATION | `validate_quality`, `detect_anomalies` |
| EXPLORATION | `compute_technical_indicators`, `analyze_sentiment_trends`, `perform_eda` |
| MODELING | `train_models`, `cross_validate` |
| EVALUATION | `evaluate_metrics`, `compare_models` |
| DEPLOYMENT | `generate_report`, `register_artifacts` |

3. In `_emit_status_update()`, add `task_id` as a required parameter (no default/optional)

### F4. Emit `plan_established` Even on Error/Fallback Paths

**File:** `backend/app/services/agent/nodes/clarification.py`
**Enforcement Rule:** E4 — plan_established Always Emitted

**Problem:** `plan_established` is only emitted on successful scope parsing. If the LLM call fails, no plan is emitted, and the Activity Tracker has nothing to display.

**Fix:** In the except block (after the F1 circuit_breaker event), also emit:
```python
{
    "event_type": "plan_established",
    "stage": "BUSINESS_UNDERSTANDING",
    "payload": {
        "plan": [
            {"stage": "DATA_ACQUISITION", "tasks": [
                {"task_id": "fetch_price_data", "label": "Fetch OHLCV price data"},
                {"task_id": "fetch_sentiment", "label": "Fetch sentiment scores"}
            ]},
            {"stage": "PREPARATION", "tasks": [
                {"task_id": "validate_quality", "label": "Run data quality checks"}
            ]},
            {"stage": "EXPLORATION", "tasks": [
                {"task_id": "compute_technical_indicators", "label": "Calculate technical indicators"},
                {"task_id": "perform_eda", "label": "Exploratory data analysis"}
            ]},
            {"stage": "MODELING", "tasks": [
                {"task_id": "train_models", "label": "Train ML models"}
            ]},
            {"stage": "EVALUATION", "tasks": [
                {"task_id": "evaluate_metrics", "label": "Compute evaluation metrics"},
                {"task_id": "compare_models", "label": "Compare model performance"}
            ]},
            {"stage": "DEPLOYMENT", "tasks": [
                {"task_id": "generate_report", "label": "Generate final report"}
            ]}
        ]
    }
}
```

This ensures the Activity Tracker has a checklist even when the workflow starts in a degraded state.

### F5. Deduplicate Runner Action_Request When Node Already Emitted

**File:** `backend/app/services/agent/runner.py`
**Enforcement Rule:** E2 — Node Events Take Priority

This is the implementation detail for F2. The runner's `pending_approvals` list in the Redis state should use the node's `action_id` (e.g., `scope_confirmation_v1`) not the runner's auto-generated one (e.g., `approve_reason`). When populating the Redis approval state:

```python
# If node emitted an action_request, use its action_id
if node_emitted_action_request:
    action_id = last_node_action_id  # e.g., "scope_confirmation_v1"
    description = last_node_action_description
else:
    action_id = f"approve_{next_node}"
    description = f"Workflow paused before step: {next_node}. Please review and approve."
```

### F6. Fix Status Update Stage Progression

**Files:** All node files emitting `status_update` events
**Enforcement Rule:** E7 (Pipeline Colors depend on correct stage values)

**Problem:** Some `status_update` events may have incorrect `stage` values, causing the pipeline to show wrong colors.

**Fix:** Audit all `status_update` emissions and ensure:
- `stage` matches the DSLC stage the node is actually operating in
- `status: "ACTIVE"` is emitted at the START of each stage's work
- `status: "COMPLETE"` is emitted at the END of each stage's work
- The status progression is: PENDING → ACTIVE → COMPLETE (no skips)

---

## 🚫 Constraints

- **DO NOT** write React/frontend code. That's the Glass Agent's job.
- **DO NOT** change API endpoint signatures. Only fix event payloads and emission logic.
- **DO NOT** add new LangGraph nodes. Fix the existing ones.
- **DO NOT** change the interrupt topology (interrupt_before/interrupt_after lists). Fix what happens during and after interrupts.
- **DO NOT** modify database models or migrations. Fix event emission only.

## ✅ Acceptance Criteria

After all 6 fixes, starting a session with an invalid API key MUST:
1. Show a `circuit_breaker_v1` card (not "Fallback due to error" text)
2. Show a populated Activity Tracker (from default `plan_established`)
3. NOT show a generic "Workflow paused before step: reason" message

Starting a session with a valid API key MUST:
1. Show a structured `scope_confirmation_v1` card with interpretation details
2. Show a populated Activity Tracker (from scope-derived `plan_established`)
3. All `status_update` events include `task_id`
4. No duplicate action_request events (node's + runner's)
5. `ruff check app/` passes with zero errors
