# Sprint 2.35 Initialization Manifest (SIM)

**Sprint Period**: Mar 08, 2026 - Mar 15, 2026
**Focus**: Data Integrity & Dashboard Polish
**Team Composition**: Architect, Dockmaster, Backend (Track A), Frontend (Track B), Backend (Track C)

---

## Sprint Objectives

### Primary Goal
Transition from "functional collectors" to "verified data pipelines". Ensure that the data being collected is accurate, consistent, and visible on the dashboard with actionable error reporting. 
**Crucially**, migrate the legacy Coinspot collector to the new Orchestrator to ensure visibility of the Target Variable.

### Success Criteria
- [ ] **Data Validation**: Automated checks confirm that `ExchangeOHLCV` records have no gaps and plausible prices.
- [ ] **Coinspot Migration**: Legacy `scheduler.py` is deprecated; Coinspot runs as an `ICollector` plugin.
- [ ] **Error Visibility**: Dashboard displays detailed error logs (from `CollectorRuns.error_message`) in a modal.
- [ ] **Resilience**: Collectors auto-retry on transient failures (e.g., network timeout).
- [ ] **Visual Polish**: "Events Ingested" chart correctly parses `json` data from `Catalyst` events.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate SIM structure.
- [ ] **Roadmap Alignment**: Ensure alignment with "Autonomous Beta".
- [ ] **Merge Safety**: Verify migrations are strictly additive.

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] Provisioning: Execute `git worktree` setup.
- [ ] Environment Isolation: unique ports for Track A/B/C.
- [ ] Teardown: Clean artifacts.

## Workspace Orchestration

**Container Isolation Policy:**

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/DATA-INTEGRITY` | `../sprint-2.35/track-a` | `../sprint-2.35/data/agent-a` | `8001` | `#3771c8` (Blue) |
| **Track B** | `feat/DASHBOARD-POLISH` | `../sprint-2.35/track-b` | `../sprint-2.35/data/agent-b` | `3001` | `#2b9e3e` (Green) |
| **Track C** | `feat/LEGACY-MIGRATION` | `../sprint-2.35/track-c` | `../sprint-2.35/data/agent-c` | `8002` | `#d15715` (Orange) |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.35/data`
# Track A Setup
- [ ] `git worktree add ../sprint-2.35/track-a -b feat/DATA-INTEGRITY`
- [ ] `cp .env ../sprint-2.35/track-a/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-a/' ../sprint-2.35/track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5433\nREDIS_PORT=6380\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.35/track-a/.env`
- [ ] `mkdir -p ../sprint-2.35/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.35/track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8001:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.35/track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.35/data/agent-a --new-window ../sprint-2.35/track-a`

# Track B Setup
- [ ] `git worktree add ../sprint-2.35/track-b -b feat/DASHBOARD-POLISH`
- [ ] `cp .env ../sprint-2.35/track-b/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-b/' ../sprint-2.35/track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5434\nREDIS_PORT=6381\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.35/track-b/.env`
- [ ] `mkdir -p ../sprint-2.35/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.35/track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"3001:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.35/track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.35/data/agent-b --new-window ../sprint-2.35/track-b`

# Track C Setup
- [ ] `git worktree add ../sprint-2.35/track-c -b feat/LEGACY-MIGRATION`
- [ ] `cp .env ../sprint-2.35/track-c/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-c/' ../sprint-2.35/track-c/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5435\nREDIS_PORT=6382\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.35/track-c/.env`
- [ ] `mkdir -p ../sprint-2.35/track-c/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#d15715","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.35/track-c/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8002:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.35/track-c/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.35/data/agent-c --new-window ../sprint-2.35/track-c`

## Execution Strategy

**Parallelism:**
Tracks A and B are largely independent but converge on the "Error Handling" interface (Backend produces errors, Frontend displays them).

### Track A: Backend Verification

**Agent**: Backend Developer
**Focus**: Data Integrity & Validation
**Port**: 8001

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.35 - Track A: Data Integrity
ROLE: Backend Developer
WORKSPACE ANCHOR: ../sprint-2.35/track-a (Port 8001)

MISSION:
Ensure the data collected by our new plugins (Glass, Human, etc.) is valid.
1. **Data Validation**: Implement `validate_collected_data()` in `BaseCollector`.
   - Check for: Negative prices, future timestamps, empty strings.
2. **Error Logging**: Improve `CollectorRuns` logging. If a collector fails, store the full stack trace in `error_message`.
3. **Resilience**: Add `tenacity` retry decorator to `collect()` methods for network errors.

OBJECTIVES:
- Modify `backend/app/services/collectors/base.py`
- Add validation logic to `ExchangeCollector` (OHLCV checks).
- Add retry logic.
```

### Track B: Dashboard Polish

**Agent**: Frontend Developer
**Focus**: Visual Polish & Error Modals
**Port**: 3001

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.35 - Track B: Dashboard Polish
ROLE: Frontend Developer
WORKSPACE ANCHOR: ../sprint-2.35/track-b (Port 3001)

MISSION:
Enhance the Collector Dashboard to be production-ready.
1. **Error Modal**: When a collector status is "Error", clicking it should open a modal showing the `error_message` from `CollectorRuns`.
2. **Relative Times**: Change "Last Run" to "5 minutes ago" (using `date-fns`).
3. **Auto-Refresh**: Use `react-query` to poll status every 30 seconds.

OBJECTIVES:
- Update `frontend/src/features/dashboard/CollectorHealth.tsx`.
- Create `frontend/src/components/ErrorModal.tsx`.
```

### Track C: Legacy Migration

**Agent**: Backend Developer
**Focus**: Coinspot Collector Migration and Deprecation
**Port**: 8002

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.35 - Track C: Legacy Migration
ROLE: Backend Developer
WORKSPACE ANCHOR: ../sprint-2.35/track-c (Port 8002)

MISSION:
Migrate the legacy `Coinspot` collector to the new `ICollector` plugin system.
1. **Refactor**: Move logic from `backend/app/services/collector.py` to `backend/app/collectors/strategies/exchange_coinspot.py`.
2. **Implement Interface**: Ensure it implements `collect()`, `test_connection()`, etc.
3. **Connect to DB**: Ensure it saves data to `CoinPrice` table (Target Variable) but logs execution to `CollectorRuns`.
4. **Deprecate**: Remove `backend/app/services/scheduler.py` startup call in `main.py`.

OBJECTIVES:
- Create `backend/app/collectors/strategies/exchange_coinspot.py`.
- Update `backend/app/main.py` (remove old scheduler).
- Register new collector in `config.py` (or DB seed).
```
