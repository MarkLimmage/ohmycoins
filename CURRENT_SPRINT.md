# Current Sprint: 2.45

**Status**: COMPLETED
**Objective**: Agentic Data Science — Blueprint + Promotion Pipeline
**Previous Sprint**: 2.44 (Lab Live Session Experience — COMPLETED)

## Context

Sprint 2.44 shipped the Lab live session experience: background execution via AgentRunner, WebSocket streaming, and a full Lab page with session management. Sprint 2.45 focuses on the "Goal-First" agentic data science UX: user types a natural language ML goal → agent produces a Blueprint Card for approval → training runs with visual progress → model artefact is promoted to the Floor with safety rules.

Includes critical hotfixes for Sprint 2.44 production bugs (WebSocket token, LangGraph recursion).

## Tasks

### Track H — Hotfixes (CRITICAL)

1. [x] **H1 — WebSocket token stringification**
   - File: `frontend/src/features/lab/hooks/useLabWebSocket.ts:31`
   - Bug: `OpenAPI.TOKEN` is `async () => string` — template literal stringifies the function reference
   - Fix: Await token resolution with `typeof` check

2. [x] **H2 — LangGraph recursion limit**
   - File: `backend/app/services/agent/langgraph_workflow.py`
   - Bug: `graph.astream()`/`graph.ainvoke()` have no `recursion_limit` — non-ML goals loop indefinitely
   - Fix: Add `config={"recursion_limit": 50}` to both methods

### Track A — Backend: Blueprint + Serialization + Optuna

3. [x] **A1 — Model serialization**
   - Add `serialize_model_to_disk()` function using `joblib.dump()` in `model_training_tools.py`
   - Move artifact storage from `/tmp/` to `/data/agent_artifacts/` (add volume mount to docker-compose.yml)

4. [x] **A2 — ModelBlueprint schema**
   - New Pydantic model `ModelBlueprint` in `services/agent/schemas.py`
   - Emit `blueprint` message type to WS stream when agent detects ML intent
   - Wire to `awaiting_choice` approval gate in AgentState

5. [x] **A3 — Optuna hyperparameter tool**
   - Add `optuna` to requirements
   - New tool `hyperparameter_search()` in `services/agent/tools/hyperparameter_search.py`
   - Supports `random_forest` and `gradient_boosting` for classification/regression

6. [x] **A4 — Structured metric events**
   - Emit `"metric"` messages with `training_metrics` and `feature_importance` types from LangGraph nodes

7. [x] **A5 — Tests**
   - `test_model_serialization.py` — joblib roundtrip
   - `test_blueprint.py` — schema validation + message emission
   - `test_optuna_tool.py` — Optuna study runs, returns best_params

### Track B — Frontend: Blueprint Card + Artifact Viewer + Promotion UI

8. [x] **B1 — BlueprintCard component**
   - Renders blueprint message: target, features, model_type, params
   - "Approve Blueprint" button resolves `awaiting_choice`

9. [x] **B2 — TrainingProgressChart component**
   - Live training metrics from `metric` messages
   - Feature importance visualization

10. [x] **B3 — ArtifactViewer component**
    - Lists session artifacts via `GET /sessions/{id}/artifacts`
    - "Promote to Floor" button per model artifact

11. [x] **B4 — PromoteModal component**
    - Form: algorithm name, description, execution rules (position_limit, daily_loss_limit, execution_frequency)
    - Tear Sheet: renders `performance_metrics_json`
    - Submits `POST /algorithms/` then `POST /strategy-promotions/`

12. [ ] **B5 — Regenerate OpenAPI client** (deferred — no new API endpoints this sprint)

## Key Files

| File | Change |
|------|--------|
| `frontend/src/features/lab/hooks/useLabWebSocket.ts` | H1: await token |
| `backend/app/services/agent/langgraph_workflow.py` | H2: recursion_limit; A4: metric events |
| `backend/app/services/agent/tools/model_training_tools.py` | A1: joblib serialization |
| `docker-compose.yml` | A1: agent-artifacts volume mount |
| `backend/app/services/agent/schemas.py` | A2: ModelBlueprint schema (new) |
| `backend/app/services/agent/tools/hyperparameter_search.py` | A3: Optuna tool (new) |
| `frontend/src/features/lab/components/BlueprintCard.tsx` | B1: new |
| `frontend/src/features/lab/components/TrainingProgressChart.tsx` | B2: new |
| `frontend/src/features/lab/components/ArtifactViewer.tsx` | B3: new |
| `frontend/src/features/lab/components/PromoteModal.tsx` | B4: new |
| `frontend/src/features/lab/LabDashboard.tsx` | Integrate B1-B4 |

## Verification

- [x] Full test suite: 946 tests passing (21 new)
- [x] mypy --strict clean
- [x] ruff check + ruff format clean
- [x] npm run type-check clean
- [x] npm run lint clean (1 pre-existing error in eventBus.ts)
- [x] H1: WS connects with valid JWT token
- [x] H2: Non-ML session completes within recursion limit
