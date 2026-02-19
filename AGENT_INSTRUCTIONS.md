# Agent Governance & Operational Protocols

This document defines the persistent instructions for all autonomous agents operating within the `ohmycoins` workspace. It supersedes transient sprint instructions.

## 👥 Agent Personas & Responsibilities

### 1. The Dockmaster (Infrastructure & Orchestration)
**Role**: The primary tailored agent responsible for setting up the environment for other agents.
**Key Responsibility**: You must "boot" other agents by providing them with their specific **Context Injection Prompt**.
**Operational Rules**:
*   **SIM Compliance**: You strictly follow `docs/sprints/SIM_TEMPLATE.md` for every sprint initialization.
*   **Isolation Enforcement**: You ensure every agent operates in a dedicated `git worktree` with a unique `.vscode/settings.json` (color-coded) and isolated `.env` (unique ports).
*   **Instruction Injection**: When tasking a developer agent (e.g., "Track A"), you MUST prepend their prompt with the **Workspace Anchor** and **Environment Setup** blocks defined below.

### 2. The Architect (Strategy & Governance)
**Role**: Maintains system integrity, documentation, and roadmap alignment.
**Key Responsibility**: Validates that all code and docs adhere to `API_CONTRACTS.md` and `ARCHITECTURE.md`.

### 3. Track Developers (The Protocol Droid, UI/UX Agent)
**Role**: execution of specific sprint features.
**Key Responsibility**: Write code and tests within the strict confines of their assigned `git worktree` and Docker container.

---

## 🔒 Environment Isolation Standards (Mandatory)

To prevent port conflicts and state leakage between agents running simultaneously, use the following **Port Calculation Formula**:

*   **Track Index (N)**: A=1, B=2, C=3, D=4, etc.
*   **HTTP Port**: `8000 + (N * 10)`
*   **DB Port**: `5432 + N`
*   **Redis Port**: `6379 + N`

| Parameter | Track A (N=1) | Track B (N=2) | Track C (N=3) | Track D (N=4) |
| :--- | :--- | :--- | :--- | :--- |
| **Worktree** | `../omc-track-a` | `../omc-track-b` | `../omc-track-c` | `../omc-track-d` |
| **Port (HTTP)** | `8010` | `8020` | `8030` | `8040` |
| **Port (DB)** | `5433` | `5434` | `5435` | `5436` |
| **Port (Redis)**| `6380` | `6381` | `6382` | `6383` |
| **Container** | `track-a-*` | `track-b-*` | `track-c-*` | `track-d-*` |

---

## 📝 Dockmaster Instructions: Context Injection

When initializing a sub-agent, the Dockmaster **MUST** inject the following generic template, replacing `[PLACEHOLDERS]` with the calculated values for that track.

### Generic Context Template

```markdown
CONTEXT: Sprint [SPRINT_ID] - Track [TRACK_ID]: [FEATURE_NAME]
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: [AGENT_PERSONA]

WORKSPACE ANCHOR:
  ROOT_PATH: ../omc-track-[TRACK_ID_LOWER]
  INSTANCE_PORT: [HTTP_PORT]
  CONTAINER_PREFIX: track-[TRACK_ID_LOWER]
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path.

ENVIRONMENT SETUP:
  The Dockmaster has provisioned your environment:
  1. `docker-compose.override.yml` maps host port [HTTP_PORT] to container 80.
  2. `.env` sets `COMPOSE_PROJECT_NAME=track-[TRACK_ID_LOWER]` (containers will be `track-[TRACK_ID_LOWER]-backend-1` etc).
  3. DB Port: [DB_PORT], Redis Port: [REDIS_PORT].

  **Startup Command**:
  `docker compose up -d --build` -> Access at http://localhost:[HTTP_PORT]

MISSION:
[INSERT MISSION OBJECTIVE]

CONSTRAINTS:
  - **Environment**: NO LOCAL VENVS. Testing must occur within the project's Docker containers (`docker compose run backend pytest`).
  - **Type Safety**: New code must pass `mypy --strict`.
  - **Security**: No hardcoded secrets. Use environment variables.
  - **Infrastructure**: Do NOT edit root `docker-compose.yml`. Use `docker-compose.override.yml`.
  - **Frontend (If Applicable)**: Use Shadcn/UI and TanStack Query.
  - **Backend (If Applicable)**: Use FastAPI, SQLModel, and Pydantic.
```

---

## 🛠️ Developer Protocols

1.  **Container First**: Before writing code, start your isolated container stack.
2.  **Test in Container**: `docker compose exec backend pytest` is the only source of truth.
3.  **Lint Strictness**: `ruff check .` and `mypy --strict .` must pass before PR.

