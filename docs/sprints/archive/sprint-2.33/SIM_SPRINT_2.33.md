# Sprint 2.33 Initialization Manifest (SIM)

**Sprint Period**: Feb 22, 2026 - Mar 01, 2026
**Focus**: Collector Orchestration Engine (Database-Driven Scheduling)
**Team Composition**: Architect, Dockmaster, Backend (Track A), Frontend (Track B)

---

## Sprint Objectives

### Primary Goal
Transition the Data Collection Engine from hardcoded configuration to a dynamic, database-driven system where schedules and collector states are managed via the UI.

### Success Criteria
- [ ] **Dynamic Scheduling**: `CollectionOrchestrator` loads and reloads schedules from the `Collector` database table.
- [ ] **Manual Trigger**: API endpoint `POST /collectors/{id}/run` executes a collector immediately, regardless of schedule.
- [ ] **UI Control**: Frontend allows users to edit Cron schedules and trigger manual runs.
- [ ] **Visibility**: Dashboard displays real-time status (Idle/Running/Error) and Last Run timestamps.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.
- [ ] **Test Alignment**: Run the full test suite (`bash scripts/test.sh`) at the end of the sprint to maintain alignment between the test suite and delivered work.
- [ ] **Merge Safety**: Verify that all transient environment changes (e.g., port mappings in `docker-compose.override.yml`) have been reverted in PRs before merging.
- [ ] **Next Sprint Planning**: Create the next SIM using `docs/sprints/SIM_TEMPLATE.md`, ensuring **zero drift** from the template structure.
- [ ] **Template Evolution**: Review `RETROSPECTIVE.md`.

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] Provisioning: Execute `git worktree` setup for Tracks A and B.
- [ ] Initialization: Launch VS Code instances with unique `--user-data-dir`.
- [ ] **Instruction Injection**: Inject track-specific settings (ports, container names) into Agent Instructions to ensure isolation.
- [ ] Synchronization: Periodically rebase Track branches with `main` to prevent drift.
- [ ] Teardown: Clean up worktrees and archive logs upon Track completion.
- [ ] **Container Hygiene**: Ensure all track-specific containers (e.g., `track-a-db-1`) are stopped and removed before closing the sprint.
- [ ] **Environment Isolation**: Verify that `.env` configurations from tracks do not leak into the main branch or other tracks.

## Workspace Orchestration (Dockmaster Only)

**Container Isolation Policy:**
Ensure that each track's `.env` uses unique ports and that developers are instructed to run tests ONLY within their track's container.

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/SCHEDULER-DB` | `../sprint-2.33/track-a` | `../sprint-2.33/data/agent-a` | `8001` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/UI-SCHEDULER` | `../sprint-2.33/track-b` | `../sprint-2.33/data/agent-b` | `3001` | `#2b9e3e` (Green) | `track-b` |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.33/data`
- [ ] `git worktree add ../sprint-2.33/track-a -b feat/SCHEDULER-DB`
- [ ] `cp .env ../sprint-2.33/track-a/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-a/' ../sprint-2.33/track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5433\nREDIS_PORT=6380\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.33/track-a/.env`
- [ ] `mkdir -p ../sprint-2.33/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.33/track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8001:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.33/track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.33/data/agent-a --new-window ../sprint-2.33/track-a`
- [ ] `git worktree add ../sprint-2.33/track-b -b feat/UI-SCHEDULER`
- [ ] `cp .env ../sprint-2.33/track-b/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-b/' ../sprint-2.33/track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5434\nREDIS_PORT=6381\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.33/track-b/.env`
- [ ] `mkdir -p ../sprint-2.33/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.33/track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"3001:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.33/track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.33/data/agent-b --new-window ../sprint-2.33/track-b`

**Teardown Protocol (CRITICAL):**
At the end of the sprint, the Dockmaster MUST:
1.  **Stop Containers**: `docker ps --filter name=track- -q | xargs -r docker stop`
2.  **Remove Containers**: `docker ps -a --filter name=track- -q | xargs -r docker rm`
3.  **Remove Worktrees**: `git worktree remove ../sprint-2.33/track-a --force` (Repeat for B)

## Execution Strategy

**Parallelism & Dependencies:**
*   **Sequential**: Track B requires the API Contract from Track A to finalize the "Run Now" button implementation.
*   **Concurrent**: Track B can mock the API response (`POST /api/v1/collectors/{id}/run -> 200 OK`) and implement the UI shell immediately.

| Dependent Track | Blocking Track | Dependency Artifact | Convergence Strategy |
| :--- | :--- | :--- | :--- |
| **Track B (Frontend)** | **Track A (Backend)** | API Schema for Run/Schedule | **Contract-First**: Track A defines endpoints in `models.py` (Pydantic) and `api.py` first. Track B uses OpenAPI generator. |

**Critical Path:**
1.  [Day 1] Track A: Define `POST /collectors/{id}/run` and `PATCH /collectors/{id}` (schedule_cron) schema.
2.  [Day 1] Track B: Mock the UI for Schedule Editor (Cron input).
3.  [Day 2] Track A: Implement DB-to-Orchestrator sync logic.
4.  [Day 3] Integration: Verify "Run Now" button actually triggers backend job.

### Track A: Backend Scheduler

**Agent**: The Backend Developer
**Requirements**: IR-SCH-001 (Collection Scheduling), IR-SCH-003 (Manual Trigger)
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.33 - Track A: Backend Scheduler
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: Backend Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.33/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path.

MISSION:
Refactor `CollectionOrchestrator` to be database-driven. It must read `Collector` records from the DB and schedule jobs accordingly. Implement a manual trigger endpoint.

SPECIFIC OBJECTIVES:
1. **Model Binding**: Modify `orchestrator.py` to fetch enabled collectors from DB on startup.
2. **Dynamic Updates**: Implement a method `refresh_collectors()` that reloads jobs when config changes.
3. **Manual Trigger**: Implement `POST /api/v1/collectors/{id}/run` which calls `orchestrator.run_collector_now(id)`.
4. **Cron Support**: Ensure `schedule_cron` field in `Collector` model is respected by APScheduler.

CONSTRAINTS:
  - **Environment**: Use `docker compose run --rm backend pytest` for testing.
  - **Database**: Use the tracked Postgres instance (Port 5433).
  - **No Hardcoding**: Remove hardcoded collector setup from `config.py`.

SUCCESS CRITERIA:
  - [ ] `orchestrator.py` has no hardcoded collectors.
  - [ ] Changing `schedule_cron` in DB updates the running job.
  - [ ] API endpoint `POST /.../run` returns 200 and starts the job.
```

### Track B: Frontend Management

**Agent**: The Frontend Developer
**Requirements**: IR-UI-004 (Collector Management)
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.33 - Track B: Frontend Management
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: Frontend Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.33/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory.

MISSION:
Enhance the Collector Configuration UI to support scheduling and manual execution.

SPECIFIC OBJECTIVES:
1. **Schedule Editor**: Add a field to the "Edit Collector" form for `schedule_cron`. (Bonus: Simple Cron UI builder).
2. **Manual Run**: Add a "Run Now" button to the Collector Card. Handle loading state (spinner).
3. **Status Indicators**: Show "Last Run: [Time]" and Status (Idle/Running/Error) based on API data.

CONSTRAINTS:
  - **Mock First**: If API is not ready, mock the `POST` request to `return Promise.resolve()`.
  - **Style**: Use existing Chakra UI components.

SUCCESS CRITERIA:
  - [ ] User can edit Cron schedule for a collector.
  - [ ] "Run Now" button sends correct API request.
  - [ ] Loading state is shown while "Running".
```
