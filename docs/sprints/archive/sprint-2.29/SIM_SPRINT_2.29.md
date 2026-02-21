# Sprint 2.29 Initialization Manifest (SIM)

**Sprint Period**: Mar 01, 2026 - Mar 08, 2026
**Focus**: Collector UI & Signal Standardization
**Team Composition**: The Architect, The Protocol Droid (Backend), The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
Complete the **Collector Management System** by finalizing the Admin UI (Dynamic Forms & Dashboard) and standardizing all collector outputs into a unified **Signal Pipeline**. This bridge connects raw data acquisition (plugins) to actionable intelligence (trading signals).

### Success Criteria
- [ ] **Admin UI**: Full CRUD capability for Collector instances via Dynamic Forms (JSON Schema).
- [ ] **Dashboard**: "Central Command" view active, showing real-time volume, rate, and health metrics.
- [ ] **Signal Pipeline**: `Signal` and `NewsItem` models populated by `IngestionService`.
- [ ] **End-to-End**: Verified flow from *Configure Plugin (UI)* -> *Execute (Backend)* -> *Normalize (Signal)* -> *Query (DB)*.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.
- [ ] **Test Alignment**: Run the full test suite (`bash scripts/test.sh`) at the end of the sprint to maintain alignment between the test suite and delivered work.
- [ ] **Next Sprint Planning**: Create the next SIM using `docs/sprints/SIM_TEMPLATE.md`, ensuring **zero drift** from the template structure.
- [ ] **Sprint Documentation Cleanup**: At the end of the sprint, move all sprint artifacts (SIM, reports, logs) to `docs/sprints/archive/sprint-2.29/` to keep the active directory clean.

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
Ensure that each track's `.env` uses unique ports (as defined below) and that developers are instructed to run tests ONLY within their track's container.

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-SIG-PIPE` | `../sprint-2.29/track-a` | `../sprint-2.29/data/agent-a` | `8010` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/REQ-COLL-DASH` | `../sprint-2.29/track-b` | `../sprint-2.29/data/agent-b` | `8020` | `#c83737` (Red) | `track-b` |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.29/data`
- [ ] `git worktree add ../sprint-2.29/track-a feat/REQ-SIG-PIPE`
- [ ] `cp .env ../sprint-2.29/track-a/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-a/' ../sprint-2.29/track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5433\nREDIS_PORT=6380\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.29/track-a/.env`
- [ ] `mkdir -p ../sprint-2.29/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.29/track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8010:80\"\n  backend:\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.29/track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.29/data/agent-a --new-window ../sprint-2.29/track-a`
- [ ] `git worktree add ../sprint-2.29/track-b feat/REQ-COLL-DASH`
- [ ] `cp .env ../sprint-2.29/track-b/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-b/' ../sprint-2.29/track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5434\nREDIS_PORT=6381\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.29/track-b/.env`
- [ ] `mkdir -p ../sprint-2.29/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#c83737","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.29/track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8020:80\"\n  backend:\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.29/track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.29/data/agent-b --new-window ../sprint-2.29/track-b`

**Teardown Protocol (CRITICAL):**
At the end of the sprint (or when a track is complete), the Dockmaster MUST:
1.  **Stop Containers**: `docker ps --filter name=track- -q | xargs -r docker stop`
2.  **Remove Containers**: `docker ps -a --filter name=track- -q | xargs -r docker rm`
3.  **Prune Networks**: `docker network prune -f`
4.  **Remove Worktrees**: `git worktree remove ../sprint-2.29/track-a --force` (Repeat for B)
5.  **Verify Clean Slate**: Run `docker ps` to ensure only the main project containers remain.

## Execution Strategy

**Parallelism & Dependencies:**
*   **Decoupled**: Track A (Backend Signal Models) and Track B (Frontend Dashboard) can run concurrently.
*   **Convergence**: Track A must enable "Test Execution" endpoints by Day 3 so Track B can visualize real activity.

| Dependent Track | Blocking Track | Dependency Artifact | Convergence Strategy |
| :--- | :--- | :--- | :--- |
| **Track B (Frontend)** | **Track A (Backend)** | `GET /collectors/stats` | **Mock-First**: Track B mocks the stats endpoint response (Volume, Rate) until Track A implements the aggregator service. |

### Track A: Backend Signal Pipeline

**Agent**: The Protocol Droid (Backend Specialist)  
**Requirements**: REQ-SIG-001 (Signal Models), REQ-SIG-002 (Ingestion Service)  
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.29 - Track A: Signal Processing Pipeline
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Protocol Droid

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.29/track-a
  INSTANCE_PORT: 8010
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path. All relative paths in documentation refer to this worktree root.

ENVIRONMENT SETUP (MANAGED):
  Your environment has been pre-configured by the Dockmaster.
  - **Review Only**: `docker-compose.override.yml` is already set to map ports for your track (e.g., 8010:80).
  - **Do Not Modify**: Do not change port mappings or project names in `.env`.
  - **Verify**: Run `grep COMPOSE_PROJECT_NAME .env` to confirm you are in "track-a".

MISSION:
Build the bridge between raw collector plugins and actionable trading signals.

SPECIFIC OBJECTIVES:
1. **Domain Models**: Create `Signal` (generic event), `NewsItem` (textual data), and `SentimentScore` in `backend/app/models/`.
2. **Ingestion Service**: Implement `IngestionService` to accept raw dicts from plugins and normalize them into these models.
3. **Aggregator**: Create `CollectorStatsService` to aggregate throughput metrics (Items/Minute, Error Count) for the Dashboard.

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update `backend/app/services/ingestion/README.md` with data flow diagram.
  
  AFTER IMPLEMENTATION:
    - [ ] Write unit tests for `IngestionService.normalize()`.
    - [ ] Verify database schema migrations (`alembic`).

CONSTRAINTS:
  - **Environment**: NO LOCAL VENVS. Use `docker compose run --rm backend pytest`.
  - **Type Safety**: New code must pass `mypy --strict`.
```

### Track B: Collector Dashboard & Dynamic Forms

**Agent**: The UI/UX Agent (Frontend Specialist)  
**Requirements**: REQ-UX-COLL-002 (Dashboard), REQ-UX-COLL-003 (Dynamic Forms)  
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.29 - Track B: Collector Dashboard
PROJECT: Oh My Coins - Trading Platform Frontend
ROLE: The UI/UX Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.29/track-b
  INSTANCE_PORT: 8020
  STRICT_SCOPE: You are locked to this directory.

ENVIRONMENT SETUP (MANAGED):
  Your environment has been pre-configured by the Dockmaster.
  - **Review Only**: `docker-compose.override.yml` is already set to map ports for your track (e.g., 8020:80).
  - **Do Not Modify**: Do not change port mappings.
  - **Verify**: Run `grep COMPOSE_PROJECT_NAME .env` to confirm you are in "track-b".

MISSION:
Create the "Mission Control" for data acquisition.

SPECIFIC OBJECTIVES:
1. **Dynamic Forms**: Finalize `CollectorForm.tsx` to render JSON Schema inputs (Text, Select, Number, Boolean) into Shadcn UI components.
2. **Dashboard**: Implement `CollectorDashboard.tsx` visualizing:
   - **Active Streams**: List of running plugins.
   - **Throughput**: Sparkline of "Items Collected / Minute".
   - **Health**: Status indicators (Green/Red) based on last successful run.
3. **Actions**: Wire up "Run Now", "Edit", and "Delete" buttons to API.

CONSTRAINTS:
  - **Environment**: Execute tests in container.
  - **Mock Data**: Use Mock Service Worker (MSW) or hardcoded mocks for stats until Backend Track A is ready.

SUCCESS CRITERIA:
  - [ ] Admin can add a new "CoinDesk" instance using only the UI form.
  - [ ] Dashboard updates status in near real-time (polling).
```

---

**generated-by**: GitHub Copilot
**date**: 2026-02-21

---

## 🛑 Friction Log (Sprint Initialization)

**Date**: Feb 21, 2026
**Reporter**: Dockmaster Agent

### 1. Docker Compose Service Inheritance Failure
*   **Issue**: The `celery_worker` service was referenced in the `docker-compose.override.yml` generated by the SIM instructions, but was **missing from the base `docker-compose.yml`**.
*   **Impact**: Track environments failed to build (`docker compose up -d --build`) because the service had no build context or image definition to inherit.
*   **Resolution**: Patched base `docker-compose.yml` to include the `celery_worker` definition.
*   **SIM Template Action Item**: 
    - Ensure the `docker-compose.override.yml` generation commands in the **Workspace Orchestration** section only reference services that strictly exist in the validated `docker-compose.yml`.
    - Add a pre-flight check: `docker compose config` to validate the combined configuration before handing over to agents.

### 2. Environment Variable Template Drift
*   **Issue**: The SIM instructions relied on `sed` to replace `COMPOSE_PROJECT_NAME` in `.env`. However, the source `.env` (copied from template) **did not contain this variable**.
*   **Impact**: `sed` failed silently. The agents' verification step (`grep COMPOSE_PROJECT_NAME`) failed, causing confusion and manual intervention.
*   **Resolution**: Updated `.env.template` in `main` to include `COMPOSE_PROJECT_NAME`.
*   **SIM Template Action Item**:
    - Update the **Provisioning Script Commands** to use `echo "COMPOSE_PROJECT_NAME=track-a" >> .env` instead of `sed`, making it robust against missing update targets.
    - Add a mandatory check in **Dockmaster Responsibilities**: "Verify `.env.template` contains all variables required for sed substitution."

### 3. VS Code Isolation Limits
*   **Issue**: The `--user-data-dir` flag is not supported in the remote VS Code environment used by the agents.
*   **Impact**: Full extension isolation between Track A and B cannot be enforced via CLI flags.
*   **Resolution**: Proceeded with standard window isolation.
*   **SIM Template Action Item**:
    - Update **Workspace Orchestration** to remove the `--user-data-dir` requirement if running in a remote container environment, or specify it as "Local Only".

### 4. Malformed YAML Injection
*   **Issue**: The fix for the missing `celery_worker` service was applied by appending the block to the end of `docker-compose.yml`. This placed the service definition **inside or after** the `networks` block, rather than correctly indented under `services`.
*   **Impact**: Docker Compose validation failed with "additional properties not allowed" or nesting errors. Agents were forced to manually move the block.
*   **Resolution**: Manually corrected the indentation in `main` (Requires follow-up action: `docker-compose.yml` in `main` must be verified for correct nesting).
*   **SIM Template Action Item**:
    - Avoid using `cat >>` for complex YAML injections. Use a proper Python script or `yq` if available to merge YAML structures safely.
    - If using pure shell, explicitly direct injections to a temporary file and construct the final YAML by concatenating parts: `head -n X base.yml > new.yml && echo "  service:" >> new.yml && tail -n Y base.yml >> new.yml`.
