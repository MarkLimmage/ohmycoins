# Sprint 2.31 Initialization Manifest (SIM)

**Sprint Period**: Mar 15, 2026 - Mar 22, 2026
**Focus**: Remediation & Dashboard Visualization
**Team Composition**: The Architect, The Protocol Droid (Backend), The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
**Remediate gaps from Sprint 2.29/2.30**: Deliver the missing "Edit Collector" functionality and implement the "Mission Control" visualization layer (Sparklines, Health Stats) that was promised but not delivered.

### Success Criteria
- [ ] **Admin UI**: "Edit" button functional in `CollectorDashboard`. Users can modify `config` of existing collectors.
- [ ] **Visualization**: `CollectorDashboard` displays a Sparkline chart showing "Items Collected/Hour" for each collector.
- [ ] **Backend Stats**: New endpoint `GET /collectors/{id}/stats` returning time-series data for the frontend charts.
- [ ] **UX Polish**: Form handles JSON schema validation errors gracefully during Edit.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **Code Review**: Enforce strict adherence to the "Remediation" scope. No new features until gaps are closed.
- [ ] **Regression Testing**: Ensure the "Edit" function does not break existing "Create" flows.

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] **Clean Slate**: Ensure previous track containers are fully removed before starting.
- [ ] **Monitoring**: Verify `logs/hub` is receiving telemetry from the new stats endpoint.

## Workspace Orchestration (Dockmaster Only)

**Container Isolation Policy:**

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `fix/COLL-STATS-API` | `../sprint-2.31/track-a` | `../sprint-2.31/data/agent-a` | `8050` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `fix/COLL-UI-EDIT` | `../sprint-2.31/track-b` | `../sprint-2.31/data/agent-b` | `8060` | `#c83737` (Red) | `track-b` |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.31/data`
- [ ] `git worktree add ../sprint-2.31/track-a fix/COLL-STATS-API`
- [ ] `cp .env ../sprint-2.31/track-a/.env`
- [ ] `echo "COMPOSE_PROJECT_NAME=track-a" >> ../sprint-2.31/track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5437\nREDIS_PORT=6384\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.31/track-a/.env`
- [ ] `mkdir -p ../sprint-2.31/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.31/track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8050:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.31/track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.31/data/agent-a --new-window ../sprint-2.31/track-a`
- [ ] `git worktree add ../sprint-2.31/track-b fix/COLL-UI-EDIT`
- [ ] `cp .env ../sprint-2.31/track-b/.env`
- [ ] `echo "COMPOSE_PROJECT_NAME=track-b" >> ../sprint-2.31/track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5438\nREDIS_PORT=6385\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.31/track-b/.env`
- [ ] `mkdir -p ../sprint-2.31/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#c83737","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.31/track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8060:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.31/track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.31/data/agent-b --new-window ../sprint-2.31/track-b`

## Execution Strategy

### Track A: Backend Stats & History

**Agent**: The Protocol Droid
**Scope**:
1.  **Metric Persistence**: Ensure `CollectorMetrics` are persisted to a time-series friendly store (or simple SQL table `CollectorRunHistory` for now). Currently, `metrics.py` is in-memory or transient.
2.  **API Endpoint**: Implement `GET /collectors/{id}/stats?range=1h` returning `[{timestamp: "...", count: 10}, ...]`.
3.  **Mock Data**: Provide a script `scripts/mock_metrics.py` to generate fake 24h history for testing the UI.

### Track B: Frontend Remediation

**Agent**: The UI/UX Agent
**Scope**:
1.  **Refactor Form**: Update `CollectorPluginForm.tsx` to accept `initialValues` prop.
2.  **Edit Flow**: In `CollectorDashboard.tsx`, add `FiEdit` button. On click, open the Dialog with the instance data pre-filled.
3.  **Visualization**: Integrate `Recharts` or similar to render the Sparkline using data from the new Track A endpoint.
4.  **Dashboard Layout**: Move from a simple Table to a "Card Grid" or "Table + Expansion" view to accommodate the charts.

