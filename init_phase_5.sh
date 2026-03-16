#!/bin/bash
set -e

echo "🛑 PHASE I: SCORCHED EARTH WIPE"
# Docker cleanup
if [ -f "docker-compose.yml" ]; then
    docker compose down --remove-orphans || echo "Docker compose down failed, continuing..."
fi
docker stop supervisor-mock mlflow 2>/dev/null || true
docker rm supervisor-mock mlflow 2>/dev/null || true

# Force-remove legacy worktrees
git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2 | tail -n +2 | xargs -I {} -r git worktree remove --force {}

# Delete branches if they exist
git branch -D integration/bridge-safe integration/bridge-msg integration/bridge-hitl integration/bridge-prod integration/bridge-glass 2>/dev/null || true

# Purge ephemeral data
echo "Purging ephemeral data..."
rm -rf /tmp/omc_lab_sessions/* 2>/dev/null || true

echo "🏗️ PHASE II: PROVISIONING 5-STREAM TOPOLOGY (v1.2)"
echo "Dependency order: D → A → B → C → E"

# Helper function to create worktree
create_worktree() {
    local branch=$1
    local path=$2
    if [ -d "$path" ]; then
        echo "Removing existing directory $path"
        rm -rf "$path"
    fi
    git worktree add -b "$branch" "$path"
}

# Stream D/D+: The Safety Bridge (FIRST — no dependencies)
create_worktree integration/bridge-safe ../omc-bridge-safe
cat > ../omc-bridge-safe/WORKER_MISSION.md << 'EOF'
# Worker Mission: Safety Bridge Agent (Workstream D/D+)

**Spec Version:** v1.2
**Dependency:** None (first in merge order)

## Task
Implement Statistical Health Gates and the per-stage circuit breaker.

## Deliverables
1. **Zero-Variance Kill-Switch:** In `_validate_data_node`, detect zero variance in target/features or >90% outliers → emit `TERMINAL_DATA_ERROR` and route to `END`.
2. **3-Cycle Per-Stage Circuit Breaker:** Add `stage_iteration_counts: dict[str, int]` to `AgentState`. On the 4th attempt for any stage, trigger `Human_in_the_Loop` interrupt or `TERMINAL_ERROR`.
3. **Data Insufficiency Routing:** If retrieved data < 50 rows after 1 retry, route to `finalize` with `completed_with_errors`.

## Files to Modify
- `backend/app/services/agent/langgraph_workflow.py` — circuit breaker logic, `stage_iteration_counts` in `AgentState`
- `backend/app/services/agent/nodes/` — validation node changes

## Constraints
- Do NOT write FastAPI routes, React code, or WebSocket logic.
- Follow `API_CONTRACTS.md` v1.2 error schema (§4).
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.

## Testing Protocol
**NEVER test on the host machine. Always test inside Docker containers.**
See `WORKER_TESTING_PROTOCOL.md` for full details.
```bash
# Start containers
docker compose up -d backend db redis

# Run ruff lint
docker compose exec backend python -m ruff check app/

# Run ruff format check
docker compose exec backend python -m ruff format app/ --check

# Run pytest
docker compose exec backend python -m pytest tests/ -v
```
EOF

# Stream A/A+: The Messaging Bridge (depends on D)
create_worktree integration/bridge-msg ../omc-bridge-msg
cat > ../omc-bridge-msg/WORKER_MISSION.md << 'EOF'
# Worker Mission: Messaging Bridge Agent (Workstream A/A+)

**Spec Version:** v1.2
**Dependency:** Workstream D (merge after D)

## Task
Refactor the messaging layer from flat dicts to the typed EventLedger system.

## Deliverables
1. **`emit_event()` helper** on `BaseAgent` — forces all agent output into `API_CONTRACTS.md` §1 envelope.
2. **Update all agents** (`DataRetrievalAgent`, `DataAnalystAgent`, `ModelTrainingAgent`, `ModelEvaluatorAgent`, `ReportingAgent`) to call `emit_event()`.
3. **`pending_events` list** in `AgentState` — runner drains and publishes.
4. **[A+] `BaseEvent` v1.2:** Add `sequence_id` (int, monotonic per session) and `timestamp` (ISO-8601 UTC) to `BaseEvent` in `lab_schema.py`.
5. **[A+] `ActionRequestEvent`** Pydantic model in `lab_schema.py` with `action_id`, `description`, `options`.
6. **Runner assigns `sequence_id`/`timestamp`** before publishing to Redis.

## Files to Modify
- `backend/app/services/agent/agents/base.py` — `emit_event()`
- `backend/app/services/agent/agents/data_retrieval.py`
- `backend/app/services/agent/agents/data_analyst.py`
- `backend/app/services/agent/agents/model_training.py`
- `backend/app/services/agent/agents/model_evaluator.py`
- `backend/app/services/agent/agents/reporting.py`
- `backend/app/services/agent/langgraph_workflow.py` — `pending_events` in `AgentState`
- `backend/app/services/agent/runner.py` — drain events, assign sequence_id/timestamp
- `backend/app/services/agent/lab_schema.py` — `BaseEvent`, `ActionRequestEvent`

## Constraints
- Do NOT write FastAPI routes, React code, or Dagger logic.
- Every event must match `API_CONTRACTS.md` v1.2 §1 envelope exactly.
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.

## Testing Protocol
**NEVER test on the host machine. Always test inside Docker containers.**
See `WORKER_TESTING_PROTOCOL.md` for full details.
```bash
# Start containers
docker compose up -d backend db redis

# Run ruff lint
docker compose exec backend python -m ruff check app/

# Run ruff format check
docker compose exec backend python -m ruff format app/ --check

# Run pytest
docker compose exec backend python -m pytest tests/ -v
```
EOF

# Stream B/B+: The Resilience Bridge (depends on A)
create_worktree integration/bridge-hitl ../omc-bridge-hitl
cat > ../omc-bridge-hitl/WORKER_MISSION.md << 'EOF'
# Worker Mission: Resilience Bridge Agent (Workstream B/B+)

**Spec Version:** v1.2
**Dependency:** Workstream A (merge after A — needs EventLedger + ActionRequestEvent)

## Task
Implement MemorySaver checkpointing, HITL interrupt gates, and state rehydration.

## Deliverables
1. **MemorySaver Checkpointer:** Add `MemorySaver()` to `LangGraphWorkflow.__init__()`. Compile graph with `checkpointer=self._checkpointer`.
2. **Interrupt Gates:** `interrupt_before=["train_model", "finalize"]` per REQUIREMENTS.md §1.2.
3. **HITL Event Flow:** On interrupt, emit `action_request` event (API_CONTRACTS.md §2.3) + `status_update` with `AWAITING_APPROVAL`, then persist and exit.
4. **Resume Logic:** Wire `AgentOrchestrator.resume_session()` to use `thread_id` derived from `session_id`.
5. **[B+] Rehydration Endpoint:** `GET /api/v1/lab/agent/sessions/{id}/rehydrate` returning `{ session_id, last_sequence_id, event_ledger[] }`.
6. **[B+] WebSocket `?after_seq`:** Add query parameter to skip already-seen events on reconnect.
7. **[B+] MemorySaver Limitation:** Document that in-memory checkpointer loses state on process restart. Phase 6 migrates to PostgresSaver.

## Files to Modify
- `backend/app/services/agent/langgraph_workflow.py` — checkpointer, interrupt_before
- `backend/app/services/agent/runner.py` — interrupt handling, HITL event emission
- `backend/app/services/agent/orchestrator.py` — `resume_session()` with thread_id
- `backend/app/api/routes/lab.py` — rehydration GET endpoint
- `backend/app/api/routes/lab.py` — WebSocket `?after_seq` parameter

## Constraints
- Do NOT write React code, Dagger logic, or agent tool implementations.
- Follow `API_CONTRACTS.md` v1.2 §2.3 (action_request) and §3 (rehydration) exactly.
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.

## Testing Protocol
**NEVER test on the host machine. Always test inside Docker containers.**
See `WORKER_TESTING_PROTOCOL.md` for full details.
```bash
# Start containers
docker compose up -d backend db redis

# Run ruff lint
docker compose exec backend python -m ruff check app/

# Run ruff format check
docker compose exec backend python -m ruff format app/ --check

# Run pytest
docker compose exec backend python -m pytest tests/ -v
```
EOF

# Stream C/C+: The Production Bridge (depends on A)
create_worktree integration/bridge-prod ../omc-bridge-prod
cat > ../omc-bridge-prod/WORKER_MISSION.md << 'EOF'
# Worker Mission: Production Bridge Agent (Workstream C/C+)

**Spec Version:** v1.2
**Dependency:** Workstream A (merge after A — needs emit_event for training events)

## Task
Route model training through Dagger sandbox with MLflow lifecycle tagging and Parquet caching.

## Deliverables
1. **Disposable Script Pattern:** `ModelTrainingAgent` generates standalone Python scripts for Dagger execution instead of calling local sklearn tools.
2. **MLflow Lifecycle Tagging:** Models with Accuracy < 0.5 or F1 < 0.3 tagged `lifecycle: discarded`. Models passing tagged `lifecycle: valid`.
3. **Parquet Row-Count Caching:** `PipelineManager` checks MV row-count; if unchanged, reuse existing `/tmp/` Parquet file.
4. **Dagger-MLflow Bridge:** Every Dagger run accompanied by an MLflow `run_id`.

## Files to Modify
- `backend/app/services/agent/agents/model_training.py` — Disposable Script generation
- `backend/app/services/agent/tools/` — Dagger execution tool updates
- `backend/app/services/lab/pipeline_manager.py` — Parquet caching
- `backend/app/services/lab/mlflow_service.py` — lifecycle tagging

## Constraints
- Do NOT write FastAPI routes, React code, or WebSocket logic.
- Follow `API_CONTRACTS.md` v1.2 for event schemas when emitting training events.
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.

## Testing Protocol
**NEVER test on the host machine. Always test inside Docker containers.**
See `WORKER_TESTING_PROTOCOL.md` for full details.
```bash
# Start containers
docker compose up -d backend db redis

# Run ruff lint
docker compose exec backend python -m ruff check app/

# Run ruff format check
docker compose exec backend python -m ruff format app/ --check

# Run pytest
docker compose exec backend python -m pytest tests/ -v
```
EOF

# Stream E: The Glass Bridge (depends on A + B)
create_worktree integration/bridge-glass ../omc-bridge-glass
cat > ../omc-bridge-glass/WORKER_MISSION.md << 'EOF'
# Worker Mission: Glass Bridge Agent (Workstream E)

**Spec Version:** v1.2
**Dependency:** Workstreams A + B (merge last — needs EventLedger, rehydration endpoint, action_request)

## Task
Refactor the React frontend from "Flat Chat" to the "Scientific Grid" architecture.

## Deliverables
1. **E1: Stage-Isolated Grid** — Replace flat `LabCell[]` with `Map<StageID, LabCell[]>`. Each DSLC stage gets a discrete cell.
2. **E2: Sequence-ID Ordering** — Sort events by `sequence_id`. Discard out-of-order events with lower sequence_id than current state.
3. **E3: Mime-Type Dispatcher** — Route `render_output` to the correct renderer based on `mime_type` (Markdown, Plotly, Blueprint card, Tearsheet, PNG).
4. **E4: `useRehydration()` Hook** — REST-first (call rehydration endpoint on mount), then WebSocket-live (connect with `?after_seq`).
5. **E5: HITL Action Request Controls** — Render high-contrast Approve/Reject/Edit buttons when `action_request` events arrive.
6. **E6: Model Discarded UI** — Visual indicator when a model is tagged `lifecycle: discarded`.
7. **E7: Cached Parquet Badge** — Show badge when Parquet data was served from cache.

## Files to Modify
- `frontend/src/features/lab/` — Grid components, stage cells
- `frontend/src/features/lab/hooks/` — `useRehydration`, WebSocket hooks
- `frontend/src/features/lab/components/` — mime-type renderers, HITL buttons

## Constraints
- Connect WebSocket to `ws://localhost:8002` for development (Supervisor mock server).
- Assume all backend data matches `API_CONTRACTS.md` v1.2 exactly.
- Use React + Chakra UI. No other UI frameworks.
- If UI needs data not in `API_CONTRACTS.md` v1.2, write `CONTRACT_RFC.md` and halt.

## Testing Protocol
**NEVER test on the host machine. Always test inside Docker containers.**
See `WORKER_TESTING_PROTOCOL.md` for full details.
```bash
# Install deps and type-check
docker compose run --rm frontend-dev npx tsc --noEmit

# Or build production image (catches all TS errors)
docker compose build frontend

# Run unit tests
docker compose run --rm frontend-dev npm run test:unit
```
EOF

echo "🔗 PHASE III: CONTEXT SEEDING"
for dir in ../omc-bridge-safe ../omc-bridge-msg ../omc-bridge-hitl ../omc-bridge-prod ../omc-bridge-glass; do
    rm -rf "$dir/.claude"
    # Copy v1.2 seed documents
    [ -f API_CONTRACTS.md ] && cp API_CONTRACTS.md "$dir/"
    [ -f REQUIREMENTS.md ] && cp REQUIREMENTS.md "$dir/"
    [ -f ROADMAP_STRATEGY.md ] && cp ROADMAP_STRATEGY.md "$dir/"
    [ -f WORKER_TESTING_PROTOCOL.md ] && cp WORKER_TESTING_PROTOCOL.md "$dir/"

    echo "DEPRECATED. READ WORKER_MISSION.md" > "$dir/CLAUDE.md"
    echo "DEPRECATED. READ WORKER_MISSION.md" > "$dir/CURRENT_SPRINT.md"
    echo "DEPRECATED. READ WORKER_MISSION.md" > "$dir/AGENT_INSTRUCTIONS.md"
done

echo ""
echo "✅ PROVISIONING COMPLETE — 5-STREAM TOPOLOGY (v1.2)"
echo ""
echo "📋 Merge Order: D → A → B → C → E"
echo "   1. ../omc-bridge-safe   (D/D+ Safety Bridge)"
echo "   2. ../omc-bridge-msg    (A/A+ Messaging Bridge)"
echo "   3. ../omc-bridge-hitl   (B/B+ Resilience Bridge)"
echo "   4. ../omc-bridge-prod   (C/C+ Production Bridge)"
echo "   5. ../omc-bridge-glass  (E    Glass Bridge)"
echo ""
echo "🚀 Launch workers with:"
echo "   code ../omc-bridge-safe ../omc-bridge-msg ../omc-bridge-hitl ../omc-bridge-prod ../omc-bridge-glass"
