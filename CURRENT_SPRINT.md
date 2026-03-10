# Current Sprint: 2.46

**Status**: IN PROGRESS
**Objective**: Model Playground + Sprint 2.45 Integration Fixes
**Previous Sprint**: 2.45 (Agentic Data Science Pipeline — COMPLETED)

## Context

Sprint 2.45 shipped all backend + frontend code (946 tests, clean lints) but has 3 integration gaps making the new Lab UI components invisible: (1) Traefik missing `/ws/` route — fixed pre-sprint, (2) ArtifactViewer never receives data — artifacts not registered in DB, frontend never fetches, (3) PromoteModal is a no-op — no algorithm creation endpoint. Sprint 2.46 fixes these gaps and adds the Model Playground feature per the roadmap.

## Tasks

### Track H — Hotfixes (Sprint 2.45 Integration Gaps)

1. [x] **H0 — Traefik WebSocket routing** (fixed pre-sprint)
   - File: `docker-compose.yml:181`
   - Bug: PathPrefix rule only had `/api`, `/docs`, `/openapi.json` — missing `/ws/`
   - Fix: Added `|| PathPrefix(\`/ws\`)` to backend router rule

2. [ ] **H1 — Register serialized models as DB artifacts**
   - File: `backend/app/services/agent/runner.py`
   - Bug: `serialize_model_to_disk()` writes to `/data/agent_artifacts/` but never calls `ArtifactManager.save_artifact()` → DB empty
   - Fix: After workflow completion in runner.py, scan artifact dir and register files via ArtifactManager

3. [ ] **H2 — Wire ArtifactViewer to backend API**
   - Files: `frontend/src/features/lab/hooks.ts`, `frontend/src/features/lab/LabDashboard.tsx`
   - Bug: `useState<Artifact[]>([])` with no setter, no API call
   - Fix: Add `useSessionArtifacts()` hook using existing `AgentService.getSessionArtifacts()`, map to Artifact type

4. [ ] **H3 — Wire PromoteModal to real API**
   - Files: `backend/app/api/routes/agent.py`, `backend/app/services/agent/schemas.py`, `frontend/src/features/lab/hooks.ts`, `frontend/src/features/lab/LabDashboard.tsx`
   - Bug: No `POST /algorithms/` endpoint, PromoteModal only console.logs
   - Fix: Add `POST /artifacts/{id}/promote` convenience endpoint (creates Algorithm + StrategyPromotion), wire frontend

5. [ ] **H4 — Update ROADMAP.md**
   - Sprint 2.45 → COMPLETED, Sprint 2.46 → IN PROGRESS

### Track A — Backend: Model Playground

6. [ ] **A1 — Model Playground Service + Endpoints**
   - New: `backend/app/services/agent/playground.py` — `ModelPlaygroundService`
   - Endpoints: `GET /artifacts/{id}/info` (model metadata), `POST /artifacts/{id}/predict` (run prediction)
   - Schemas: `PredictionRequest`, `PredictionResponse`, `ModelInfo` in `schemas.py`

7. [ ] **A2 — Playground Tests**
   - New: `backend/tests/services/agent/test_playground.py`, `backend/tests/api/routes/test_agent_playground.py`
   - Unit + API tests for load/predict/info, classification + regression, error cases
   - Target: ~10 new tests

### Track B — Frontend: Model Playground UI

8. [ ] **B1 — ModelPlaygroundPanel component**
   - New: `frontend/src/features/lab/components/ModelPlaygroundPanel.tsx`
   - Fetches model info, renders feature inputs, runs predictions, shows results

9. [ ] **B2 — Dashboard integration**
   - Files: `ArtifactViewer.tsx` (add Test button), `LabDashboard.tsx` (playground state)
   - Add `useModelInfo()` and `useModelPredict()` hooks

10. [ ] **B3 — Regenerate OpenAPI client**
    - Run after all backend endpoints land and merge
    - `bash scripts/generate-client.sh`

## Key Files

| File | Change |
|------|--------|
| `docker-compose.yml` | H0: `/ws/` PathPrefix (done) |
| `backend/app/services/agent/runner.py` | H1: artifact registration |
| `backend/app/api/routes/agent.py` | H3: promote endpoint; A1: predict + info |
| `backend/app/services/agent/playground.py` | A1: new — ModelPlaygroundService |
| `backend/app/services/agent/schemas.py` | H3 + A1: new schemas |
| `frontend/src/features/lab/hooks.ts` | H2 + H3 + B2: new hooks |
| `frontend/src/features/lab/LabDashboard.tsx` | H2 + H3 + B2: wiring |
| `frontend/src/features/lab/components/ModelPlaygroundPanel.tsx` | B1: new |
| `frontend/src/features/lab/components/ArtifactViewer.tsx` | B2: Test button |

## Verification

- [ ] Full test suite passing (946 + ~10 new)
- [ ] mypy --strict clean
- [ ] ruff check + ruff format clean
- [ ] npm run type-check clean
- [ ] npm run lint clean
- [ ] Manual: ArtifactViewer shows model files after session
- [ ] Manual: Promote creates Algorithm + StrategyPromotion
- [ ] Manual: Model Playground predicts with custom inputs
- [ ] WebSocket connects (Traefik fix verified)
