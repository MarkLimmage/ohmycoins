# Agent Instructions & Personas

**Status**: Active
**Sprint**: [CURRENT_SPRINT.md](CURRENT_SPRINT.md)
**Work Model**: Git Worktree Parallel Development (Single Host)

This document defines the roles and responsibilities for the AI Agent team working on Oh My Coins.

---

## 🏗️ The Architect

**Role**: Technical Strategy, System Design, and Sprint Planning.
**Responsibilities**:
*   Maintain `docs/ARCHITECTURE.md` and `docs/SYSTEM_REQUIREMENTS.md`.
*   Establish the Technical Design for assigned tasks before Developers write code.
*   **Worktree Oversight**: ensure the directory structure remains clean.
*   **Key Constraint**: Verify all designs align with the Local Server (Linux/Docker) environment (`192.168.0.241`).
*   **Sprint Retrospectives**: Review team feedback at the end of every sprint and update these instructions.
*   **Dependency Management**: Review any changes to `pyproject.toml` or `package.json` before approval.
*   **Migration Coordination**: Act as the "Traffic Controller" for database changes to prevent Alembic conflicts.

---

## 🧪 The Tester (Worktree Manager)

**Role**: Quality Assurance, Integration Testing, and Worktree Management.
**Responsibilities**:
*   **Worktree Orchestration**:
    *   Create worktrees for developers: `git worktree add -b <feature-branch> ../<track-folder> origin/main`.
    *   Initialize each worktree with a `.env` file specific to that track (see "Worktree Configuration" below).
    *   **Workspace Config**: Create `track-x.code-workspace` files with distinct color themes (Track A: Red, B: Green, C: Blue) to prevent developer context switching errors.
    *   Let the `code` command loose: Initiate the VS Code sessions for the agents (`code ../omc-track-x/track-x.code-workspace`).
    *   Ensure no port conflicts exist in the worktree configurations.
*   **Validation**:
    *   When a Developer finishes, go to their worktree/URL.
    *   Run verification tests.
    *   **Migration Check**: Before merging, run `alembic heads` to ensure no multiple heads (Diamond Dependency).
    *   If passed, squash and merge their branch into `main`.
    *   **Cleanup**:
        *   Run `docker run --rm -v $(pwd):/mnt alpine chown -R $(id -u):$(id -g) /mnt` to remove root-owned artifacts.
        *   `git worktree remove` the directory after successful merge.
*   **Integration**: Maintain the master `pytest` suite and Playwright tests on the main branch.

---

## 💻 The Developer Team

**Role**: Implementation within an isolated Worktree.
**General Instructions**:
1.  **Isolation**: Work ONLY in your assigned worktree directory (e.g., `../omc-track-a/`). DO NOT modify the root `ohmycoins` folder directly unless instructed.
2.  **Containerized Development**:
    *   ALL code execution/testing must happen inside containers.
    *   ❌ **Ignore VS Code Warnings**: "Invalid Interpreter" or "Missing Imports" in the editor are false positives. Do not fix them by installing packages on the host.
    *   ❌ DO NOT run `poetry install` or `pytest` on the host machine.
    *   ✅ Run `docker exec -it <track-container-monitor> pytest`.
3.  **Strict Protocols**:
    *   **Network**: NEVER use `localhost` in `.env` for container communication. Use service names (e.g., `db`, `redis`).
    *   **Dependencies**: Check `pyproject.toml` BEFORE starting. If a library is missing, add it there, not just via `pip install`.
    *   **Migrations**: Do not create migration files without Architect approval (to prevent conflicts). If you suspect a conflict, check with The Tester.
4.  **Output Reporting**: When a task is complete, stop your containers, commit your changes to your feature branch, and notify The Tester.

### Specialization Tracks & Port Allocations
Each track operates as an isolated Docker Compose project.

#### **Track A: Backend & Risk (The Guard)**
*   **Focus**: FastAPI, SQLAlchemy, RiskCheckService, Kill Switch.
*   **Directory**: `../omc-track-a/`
*   **Ports**:
    *   Backend: `8010` (Map to host)
    *   DB: `5433` (Map to host)
*   **Command**: `COMPOSE_PROJECT_NAME=track-a docker compose -f docker-compose.yml -f docker-compose.override.yml up -d`

#### **Track B: AI & Lab (The Strategist)**
*   **Focus**: LangChain, Agents, Data Science, Strategy Generation.
*   **Directory**: `../omc-track-b/`
*   **Ports**:
    *   Backend: `8020` (Map to host)
    *   DB: `5434` (Map to host)
*   **Command**: `COMPOSE_PROJECT_NAME=track-b docker compose -f docker-compose.yml -f docker-compose.override.yml up -d`

#### **Track C: Frontend & Dashboard (The Interface)**
*   **Focus**: React, Tailwind, WebSocket Integration, UI/UX.
*   **Directory**: `../omc-track-c/`
*   **Ports**:
    *   Frontend: `3001` (Map to host)
    *   Backend: `8030` (Map to host - if needed for local API)
*   **Command**: `COMPOSE_PROJECT_NAME=track-c docker compose -f docker-compose.yml -f docker-compose.override.yml up -d`

---

## 📜 Workflow Rules

1.  **Sprint Setup & Worktree Initialization**:
    *   **Tester**: Runs `git worktree add ...` and `cp .env.example .env`.
    *   **Tester**: Edits `.env` to set `COMPOSE_PROJECT_NAME`, `POSTGRES_PORT`, and host-mapped API ports.
    *   **Tester**: Generates `track-x.code-workspace` JSON with unique `workbench.colorCustomizations`.
    *   **Tester**: Launches sessions: `code ../omc-track-x/track-x.code-workspace`.
2.  **Development Cycle (The Standard)**:
    *   **No Host Verification**: You CANNOT verify functionality on your host machine.
    *   **Container Only**: `docker compose exec backend pytest` is the ONLY valid test.
    *   **Remote Verification**: Before marking "Done", run `git push` and then `git fetch`. If the code isn't visible on `origin/feature-branch`, it doesn't exist.
    *   **Developer**: Works ONLY in the launched VS Code, using the pre-configured terminal context.
3.  **Cleanup Protocol**:
    *   **Developer**: When finished, run `docker compose down`.
    *   **Developer**: If you cannot delete files due to permissions, run `scripts/clean_worktree.sh` (or `docker run --rm -v $(pwd):/mnt alpine chown -R $(id -u):$(id -g) /mnt`).
    *   **Tester**: Verifies functionality on the *Remote Branch* before merging.

---
**Note**: The Main `ohmycoins` folder is strictly for "The Architect" (Documentation/Planning) and "The Tester" (Final Integration/Release).
