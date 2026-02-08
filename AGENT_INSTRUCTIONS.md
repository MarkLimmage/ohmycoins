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

---

## 🧪 The Tester (Worktree Manager)

**Role**: Quality Assurance, Integration Testing, and Worktree Management.
**Responsibilities**:
*   **Worktree Orchestration**:
    *   Create worktrees for developers: `git worktree add -b <feature-branch> ../<track-folder> origin/main`.
    *   Initialize each worktree with a `.env` file specific to that track (see "Worktree Configuration" below).
    *   Ensure no port conflicts exist in the worktree configurations.
*   **Validation**:
    *   When a Developer finishes, go to their worktree/URL.
    *   Run verification tests.
    *   If passed, squash and merge their branch into `main`.
    *   `git worktree remove` the directory after successful merge.
*   **Integration**: Maintain the master `pytest` suite and Playwright tests on the main branch.

---

## 💻 The Developer Team

**Role**: Implementation within an isolated Worktree.
**General Instructions**:
1.  **Isolation**: Work ONLY in your assigned worktree directory (e.g., `../omc-track-a/`). DO NOT modify the root `ohmycoins` folder directly unless instructed.
2.  **Containerized Development**:
    *   ALL code execution/testing must happen inside containers.
    *   ❌ DO NOT run `poetry install` or `pytest` on the host machine.
    *   ✅ Run `docker exec -it <track-container-monitor> pytest`.
3.  **Output Reporting**: When a task is complete, stop your containers, commit your changes to your feature branch, and notify The Tester.

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

1.  **Worktree Initialization**:
    *   **Tester**: Runs `git worktree add ...` and `cp .env.example .env`.
    *   **Tester**: Edits `.env` to set `COMPOSE_PROJECT_NAME`, `POSTGRES_PORT`, and host-mapped API ports according to the Track specs above.
2.  **Development Cycle**:
    *   **Developer**: `cd ../omc-track-x`
    *   **Developer**: `docker compose up -d --build`
    *   **Developer**: `docker exec -it track-x-backend pytest tests/my_new_feature_test.py`
    *   **Developer**: Git Commit & Push.
3.  **Merge & Cleanup**:
    *   **Tester**: Verifies functionality.
    *   **Tester**: Merges to `main`.
    *   **Tester**: `docker compose down` (in worktree) -> `git worktree remove ../omc-track-x`.

---
**Note**: The Main `ohmycoins` folder is strictly for "The Architect" (Documentation/Planning) and "The Tester" (Final Integration/Release).
