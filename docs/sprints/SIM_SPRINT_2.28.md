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
- [ ] `mkdir -p ../omc-track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../omc-track-a/.vscode/settings.json`
- [ ] `code --user-data-dir ../omc-data/agent-a --new-window ../omc-track-a`
- [ ] `git worktree add ../omc-track-b feat/REQ-COLL-UI`
- [ ] `mkdir -p ../omc-track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#c83737","titleBar.activeForeground":"#ffffff"}}' > ../omc-track-b/.vscode/settings.json`
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
*   **Goal**: robust plugin infrastructure.
*   **Key Files**:
    *   `backend/app/core/collectors/base.py`: Abstract Base Class `ICollector`.
    *   `backend/app/core/collectors/registry.py`: Discovery logic.
    *   `backend/app/collectors/strategies/news_coindesk.py`: Ported scraper.
    *   `backend/app/models/collector.py`: SQLModel for persistent configuration.
*   **Requirements**: `REQ-COLL-ARCH-001` (Interface), `REQ-COLL-EVT-001` (Registration).

#### **Track B: Frontend Dynamic Forms (UI/UX Agent)**
*   **Goal**: Render configuration forms based on plugin schemas.
*   **Key Files**:
    *   `frontend/src/features/admin/CollectorForm.tsx`: Schema-driven form builder.
    *   `frontend/src/features/admin/CollectorDashboard.tsx`: Instance management.
*   **Requirements**: `REQ-COLL-ARCH-002` (Dynamic UI), `REQ-COLL-ST-001` (Health Monitoring).

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
