# Sprint 2.30 Initialization Manifest (SIM)

**Sprint Period**: Mar 08, 2026 - Mar 15, 2026
**Focus**: Signal Pipeline & Collector UI Integration
**Team Composition**: The Architect, The Protocol Droid (Backend), The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
Achieve **End-to-End Signal Flow**: Configure a collector in the UI (Track B), have it run in the backend (Track A), and visualize the resulting signals back in the UI Dashboard.

### Success Criteria
- [ ] **Track A (Backend)**: `Signal` and `NewsItem` models populated via `IngestionService`.
- [ ] **Track B (Frontend)**: "Active Signals" component on Dashboard displaying real-time data.
- [ ] **Integration**: `CollectorStatsService` explicitly feeding the Dashboard's "Items/Minute" sparkline.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **Governance Check**: Run `python3 scripts/governance/supervisor.py` daily to detect drift.
- [ ] **Log Review**: Run `python3 scripts/governance/watchdog.py` to identify hidden errors.
- [ ] **Registry Management**: Keep `scripts/governance/registry.json` updated with active tasks.

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] **Strict Adherence**: Follow "Workspace Orchestration" below exactly.
- [ ] **Logging Infrastructure**: Ensure `volumes: - /home/mark/omc/logs/hub:/var/log/omc-agents` is mounted for all backend services.
- [ ] **Status Reporting**: Update `status.json` in the root during initialization.

## Workspace Orchestration (Dockmaster Only)

**Container Isolation Policy:**
Ensure that each track's `.env` uses unique ports (as defined below) and that developers are instructed to run tests ONLY within their track's container.

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-SIG-FLOW` | `../sprint-2.30/track-a` | `../sprint-2.30/data/agent-a` | `8030` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/REQ-UI-INTEG` | `../sprint-2.30/track-b` | `../sprint-2.30/data/agent-b` | `8040` | `#c83737` (Red) | `track-b` |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.30/data`
- [ ] `git worktree add ../sprint-2.30/track-a feat/REQ-SIG-FLOW`
- [ ] `cp .env ../sprint-2.30/track-a/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-a/' ../sprint-2.30/track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5435\nREDIS_PORT=6382\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.30/track-a/.env`
- [ ] `mkdir -p ../sprint-2.30/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.30/track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8030:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.30/track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.30/data/agent-a --new-window ../sprint-2.30/track-a`
- [ ] `git worktree add ../sprint-2.30/track-b feat/REQ-UI-INTEG`
- [ ] `cp .env ../sprint-2.30/track-b/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-b/' ../sprint-2.30/track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5436\nREDIS_PORT=6383\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.30/track-b/.env`
- [ ] `mkdir -p ../sprint-2.30/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#c83737","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.30/track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8040:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.30/track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.30/data/agent-b --new-window ../sprint-2.30/track-b`

**Teardown Protocol (CRITICAL):**
At the end of the sprint (or when a track is complete), the Dockmaster MUST:
1.  **Stop Containers**: `docker ps --filter name=track- -q | xargs -r docker stop`
2.  **Remove Containers**: `docker ps -a --filter name=track- -q | xargs -r docker rm`
3.  **Prune Networks**: `docker network prune -f`
4.  **Remove Worktrees**: `git worktree remove ../sprint-2.30/track-a --force` (Repeat for B)

---

## Governance Protocol (Heartbeat Requirement)

All active agents (Tracks A, B) MUST maintain a `status.json` file in the root of their worktree.
**Update Frequency**: At the start of every major task or at least once per 10 minutes.

---

**generated-by**: GitHub Copilot (Architect Mode)
**date**: 2026-02-21
