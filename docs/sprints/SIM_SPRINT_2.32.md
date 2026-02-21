# Sprint 2.32 Initialization Manifest (SIM)

**Sprint Period**: Mar 22, 2026 - Mar 29, 2026
**Focus**: DevOps Remediation & Visualization Release
**Team Composition**: The Architect, The Dockmaster, The UI/UX Agent

---

## 🎯 Strategic Context

**Situation**: Sprint 2.31 delivered the *code* for Collector Stats and Edit functionality, but the *release* is stuck. The frontend container builds a production-optimized `nginx` image that strips away dev tools (`npm`, `tests`), making it impossible to run tests or hot-reload changes in the current Docker setup. Furthermore, the user reports the deployed frontend does not reflect the merged changes, suggesting a build caching or volume mounting issue.

**Objective**: Fix the Docker Development Experience (DX) to unblock testing, and force a clean build of the frontend to deploy the missing UI features.

---

## Sprint Objectives

### Primary Goal
**Fix the Deploy Pipeline**: Ensure the frontend container correctly rebuilds with the new code and that `npm run test` is executable within the container environment.

### Success Criteria
- [ ] **Docker DX**: `docker compose run frontend npm run test` executes successfully (requires multi-stage build adjustment or dev target).
- [ ] **Deployment**: User confirms the "Edit" button and "Sparklines" are visible in the production UI.
- [ ] **API Sync**: `sdk.gen.ts` is auto-generated and committed to Git to prevent client drifts.

---

## Agent Assignments

### Track D: The Dockmaster (Infrastructure)
**Focus**: `Dockerfile` & `docker-compose.yml`
**Tasks**:
1.  **Refactor Dockerfile**: Introduce a `dev` stage in `frontend/Dockerfile` that keeps `node` and `npm` available.
2.  **Update Compose**: Modify `docker-compose.yml` (or override) to target the `dev` stage for local development.
3.  **Cache Busting**: Implement a strategy (e.g., build args or `--no-cache`) to force the frontend to pick up the new source code during build.

### Track B: The UI/UX Agent (Frontend)
**Focus**: Verification & Polish
**Tasks**:
1.  **Verify Visualization**: Once the build is fixed, confirm the Sparklines render correctly with real data.
2.  **Test Coverage**: Write the missing unit tests for `CollectorCard` using the now-working test runner.

---

## Workspace Orchestration

**Legacy Cleanup**:
- The Dockmaster MUST ensure all `sprint-2.31` containers are removed (`docker rm -f`).
- Prune old images: `docker image prune -a --filter "label=com.ohmycoins.sprint=2.31"`.

**New Track**:
| Track | Branch | Worktree | Port | Color |
| :--- | :--- | :--- | :--- | :--- |
| **Track D** | `fix/DOCKER-DX` | `../sprint-2.32/track-d` | `8070` | `#ffbe3d` (Gold) |

**Provisioning**:
- [ ] `mkdir -p ../sprint-2.32/data`
- [ ] `git worktree add ../sprint-2.32/track-d fix/DOCKER-DX`
- [ ] `cp .env ../sprint-2.32/track-d/.env`
- [ ] `echo "COMPOSE_PROJECT_NAME=track-d" >> ../sprint-2.32/track-d/.env`
- [ ] `echo -e "services:\n  frontend:\n    build:\n      target: dev\n    volumes:\n      - ./frontend:/app\n      - /app/node_modules" > ../sprint-2.32/track-d/docker-compose.override.yml`

