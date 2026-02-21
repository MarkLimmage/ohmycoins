# Sprint 2.28 Initialization Manifest (SIM)

**Sprint Period**: Feb 19, 2026 - Feb 28, 2026
**Focus**: Collector Uplift (Plugin Architecture)
**Team Composition**: The Architect, The Protocol Droid (Backend), The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
Revolutionize data collection management by implementing a **Plugin-Based Architecture**. Refactor the collector system to use standardized modules (`ICollector`), typically auto-discovered by a `CollectorRegistry`. This allows Admins to activate, configure, and monitor powerful Python-based strategies via the UI without exposing raw code execution risks.

### Success Criteria
- [ ] **Architecture**: `ICollector` interface defined and enforced for all plugins.
- [ ] **Registry**: `CollectorRegistry` implemented to scan and register valid plugins at startup.
- [ ] **Data Model**: `Collector` table updated to store plugin configuration (JSON) and state.
- [ ] **Plugins**: Ported 3+ reference scrapers (e.g., CoinDesk, Yahoo, CryptoPanic) to the new plugin format.
- [ ] **Frontend**: Dynamic Admin UI forms generated from plugin JSON schemas.
- [ ] **Backend**: Scheduler refactored to execute plugin instances with stored config.

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
- [ ] **Sprint Documentation Cleanup**: At the end of the sprint, move all sprint artifacts (SIM, reports, logs) to `docs/sprints/archive/sprint-2.28/` to keep the active directory clean.

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

The Dockmaster Agent must execute the following `git worktree` and environment setups before activating Track A and B.

**Container Isolation Policy:**
Ensure that each track's `.env` uses unique ports (as defined below) and that developers are instructed to run tests ONLY within their track's container (e.g., `docker compose -f docker-compose.track-a.yml run backend pytest`).

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-COLL-PLUGIN` | `../omc-track-a` | `../omc-data/agent-a` | `8010` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/REQ-COLL-UI` | `../omc-track-b` | `../omc-data/agent-b` | `8020` | `#c83737` (Red) | `track-b` |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../omc-data`
- [ ] `git worktree add ../omc-track-a feat/REQ-COLL-PLUGIN`
- [ ] `cp .env ../omc-track-a/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-a/' ../omc-track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5433\nREDIS_PORT=6380\n" >> ../omc-track-a/.env`
- [ ] `mkdir -p ../omc-track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../omc-track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8010:80\"\n  backend:\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../omc-track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../omc-data/agent-a --new-window ../omc-track-a`
- [ ] `git worktree add ../omc-track-b feat/REQ-COLL-UI`
- [ ] `cp .env ../omc-track-b/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-b/' ../omc-track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5434\nREDIS_PORT=6381\n" >> ../omc-track-b/.env`
- [ ] `mkdir -p ../omc-track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#c83737","titleBar.activeForeground":"#ffffff"}}' > ../omc-track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8020:80\"\n  backend:\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../omc-track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../omc-data/agent-b --new-window ../omc-track-b`

**Teardown Protocol (CRITICAL):**
At the end of the sprint (or when a track is complete), the Dockmaster MUST:
1.  **Stop Containers**: `docker ps --filter name=track- -q | xargs -r docker stop`
2.  **Remove Containers**: `docker ps -a --filter name=track- -q | xargs -r docker rm`
3.  **Prune Networks**: `docker network prune -f`
4.  **Remove Worktrees**: `git worktree remove ../omc-track-a --force` (Repeat for B)
5.  **Verify Clean Slate**: Run `docker ps` to ensure only the main project containers remain.

### Track Objectives

#### **Track A: Backend & Plugin System (Protocol Droid)**

**Agent**: The Protocol Droid (Backend Specialist)
**Requirements**: REQ-COLL-ARCH-001, REQ-COLL-EVT-001
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.28 - Track A: Collector Plugin System
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Protocol Droid

WORKSPACE ANCHOR:
  ROOT_PATH: ../omc-track-a (Relative to original repo clone)
  INSTANCE_PORT: 8010
  CONTAINER_PREFIX: track-a
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path.

ENVIRONMENT SETUP:
  The Dockmaster has already provisioned your environment:
  1. `docker-compose.override.yml` maps port 8010 to container 80.
  2. `.env` sets `COMPOSE_PROJECT_NAME=track-a` (containers will be `track-a-backend-1` etc).
  3. DB Port: 5433, Redis Port: 6380 (mapped to avoid conflicts).

  **Startup Command**:
  `docker compose up -d --build` -> Access at http://localhost:8010

MISSION:
Create a robust plugin infrastructure for data collection.

SPECIFIC OBJECTIVES:
1. **Interface**: Define `ICollector` abstract base class in `backend/app/core/collectors/base.py`.
2. **Registry**: Implement `CollectorRegistry` in `backend/app/core/collectors/registry.py` to auto-discover plugins.
3. **Migration**: Port `CoinDesk` scraper to `backend/app/collectors/strategies/news_coindesk.py`.
4. **Persistence**: Update `Collector` SQLModel to store plugin configuration.

CONSTRAINTS:
  - **Environment**: NO LOCAL VENVS. Testing must occur within the project's Docker containers (`docker compose run backend pytest`).
  - **Type Safety**: New code must pass `mypy --strict`.
  - **No Conflict**: Do NOT edit `docker-compose.yml` (shared). Only `docker-compose.override.yml` (local).

DELIVERABLES:
  - Working `ICollector` interface and `CollectorRegistry`.
  - One reference plugin (CoinDesk) operational.
  - Unit tests passing inside container.
```

#### **Track B: Frontend Dynamic Forms (UI/UX Agent)**

**Agent**: The UI/UX Agent (Frontend Specialist)
**Requirements**: REQ-COLL-ARCH-002, REQ-COLL-ST-001, REQ-COLL-CFG-001
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.28 - Track B: Collector Admin UI
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The UI/UX Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../omc-track-b (Relative to original repo clone)
  INSTANCE_PORT: 8020
  CONTAINER_PREFIX: track-b
  STRICT_SCOPE: You are locked to this directory.

ENVIRONMENT SETUP:
  The Dockmaster has already provisioned your environment:
  1. `docker-compose.override.yml` maps port 8020 to container 80.
  2. `.env` sets `COMPOSE_PROJECT_NAME=track-b`.
  3. DB Port: 5434, Redis Port: 6381.

  **Startup Command**:
  `docker compose up -d --build` -> Access at http://localhost:8020

MISSION:
Render configuration forms based on plugin schemas.

SPECIFIC OBJECTIVES:
1. **Dynamic Forms**: Create `CollectorForm.tsx` to render inputs from JSON schema.
2. **Dashboard**: Update `CollectorDashboard.tsx` to show instance status.
3. **Edit Instance Workflow**: Implement full CRUD for instance configuration (Edit/Update existing instances).
4. **Dynamic Configuration Options**: Ensure Admin UI exposes all specific settings defined in the plugin schema (e.g., API keys, schedules) similar to a "Valves Config" pattern.
5. **Central Collector Dashboard**: Create a new dashboard view that visualizes data acquisition metrics:
    - Active streams (running plugins)
    - Volume (items collected)
    - Rate (items/minute)
    - Error rates and health status

CONSTRAINTS:
  - **Environment**: Run frontend tests in container or check strictly against API specs.
  - **Design**: Follow existing UI component library (Shadcn/UI).

DELIVERABLES:
  - Admin page capable of configuring AND EDITING the CoinDesk plugin.
  - Status indicators for health monitoring.
```

---

## Testing Strategy
- **Unit**: Mocked plugin execution in `test_registry.py`.
- **Integration**: Verify a new plugin added to the folder appears in the API response.
- **E2E**: `J-COLL-001`: Register & Activate CoinDesk Plugin.

### Validation Requirements (Mandatory)
- [ ] **Unit Coverage**: > 80% (`pytest --cov`)
- [ ] **Container Execution**: Tests MUST pass inside `docker compose run backend pytest`
- [ ] **Type Safety**: `mypy --strict .` passes (no errors)
- [ ] **Security**: `trivy fs .` passes (no vulnerabilities)

---

**generated-by**: GitHub Copilot
**date**: 2026-02-19
