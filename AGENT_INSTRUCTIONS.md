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
*   **Monitoring**: You actively monitor `LOGBOOK.md` in each track's worktree for "STUCK" or "BLOCKED" states.

### 2. The Architect (Strategy & Governance)
**Role**: Maintains system integrity, documentation, and roadmap alignment.
**Key Responsibility**: Validates that all code and docs adhere to `API_CONTRACTS.md` and `ARCHITECTURE.md`.
**Intervention Protocol**: If a logical loop is detected in a developer agent's `LOGBOOK.md`, you will issue an override by writing to `INSTRUCTIONS_OVERRIDE.md` in their worktree.

### 3. Track Developers (The Protocol Droid, UI/UX Agent)
**Role**: execution of specific sprint features.
**Key Responsibility**: Write code and tests within the strict confines of their assigned `git worktree` and Docker container.
**Journaling Requirement**: You MUST maintain a `LOGBOOK.md` file in your worktree root.
    - **Format**: `## [TIMESTAMP] - [TASK_NAME]` followed by Intent, Status, Monologue, and Blockers.
    - **Frequency**: Before every major action (test run, package install, strategy pivot).
    - **Self-Correction**: Check `INSTRUCTIONS_OVERRIDE.md` before every task. If it exists, priorities its content over your current plan.

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

### 1. Workspace Provisioning (Anti-Confusion Protocol)
**CRITICAL**: Do not rely on Git alone. Developer agents need context files physically present in their worktree.

**Step-by-Step Provisioning Checklist**:
1.  **Path Hygiene**:
    *   Target: `../sprint-[ID]/track-[ID]` (e.g., `../sprint-2.33/track-a`).
    *   **verify**: Ensure you are NOT creating a nested path like `.../track-a/sprint-2.33/...`.
    *   **Clean**: `rm -rf` the target before `git worktree add` to ensure no stale artifacts.

2.  **Asset Replication (The "Lost Dev" Fix)**:
    *   Immediately after creating the worktree, **COPY** these files from the root to the new `track-` folder:
        *   `CURRENT_SPRINT.md`
        *   `ROADMAP.md`
        *   `AGENT_INSTRUCTIONS.md`
    *   *Why?* Git worktrees do not inherit untracked/ignored documentation files, leaving agents blind.

3.  **Bootstrap Documentation**:
    *   Create a `README.md` *inside the track folder* explaining:
        *   **Port**: The specific port for this track.
        *   **Role**: Backend vs Frontend vs DevOps.
    *   Initialize `LOGBOOK.md` with:
        *   **Intent**: "Initialize workspace..."
        *   **Context**: "You are working on [FEATURE] in [TRACK]."

### 2. Prompt Context Injection

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

### 3. Failure Recovery

If a developer agent reports "missing files" or "wrong directory":
1.  **Stop**: Do not argue.
2.  **Verify**: Run `ls -R` on the reported path.
3.  **Nuke & Pave**: If the structure is messy, delete the worktree and re-provision using the **Workspace Provisioning** checklist above.

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

---

## 🤝 Delegation & Ownership Protocol

### Task Ownership Rules

- A delegated task has **exactly one owner** at any time. The owner is the agent actively working on it.
- The delegator (e.g., Architect) **MUST NOT perform the delegated work** — no running the same tests, builds, health checks, or code reviews in parallel.
- The delegator may only send **status inquiries** while a task is owned by another agent.
- To take over a stalled task: send a status inquiry first → wait for response → only then reassign via TaskUpdate.

### Delegation Checklist (For the Spawner)

Before delegating a task to another agent, the spawner MUST:

1. **Read `.claude/agents/{target}.md`** — confirm the target's model, tools, and constraints.
2. **Use the correct model** from the frontmatter (`dev` = haiku, `dockmaster` = sonnet, `architect` = opus).
3. **Define success criteria** — the agent must know exactly when the task is done.
4. **Include bootstrap instruction** — add "Execute the Bootstrap Sequence from CLAUDE.md before starting work" in the task prompt.

### Report-Back Protocol

When completing a delegated task, the agent MUST send this structured report to the delegator:

```
TASK REPORT
STATUS: completed | blocked | failed
RESULT: <one-line summary of what was accomplished>
DELIVERABLES: <files changed, tests passed, endpoints verified>
ISSUES: <blockers, warnings, or "none">
```

### Stale Report Handling

If no TASK REPORT is received after a reasonable period:
1. The delegator sends a **status inquiry message** to the agent.
2. If no response after the inquiry, the delegator may **reassign** the task to another agent or take it over — but must log the takeover in `LOGBOOK.md`.
3. The original agent, upon discovering its task was reassigned, MUST stop work immediately and acknowledge the reassignment.
