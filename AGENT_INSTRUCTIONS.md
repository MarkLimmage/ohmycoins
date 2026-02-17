# Agent Instructions: Remediation Sprint 2.27

You are an expert Python developer tasked with paying down technical debt. Your goal is to remove `# mypy: ignore-errors` from files and fix the resulting type errors.

## ⚠️ CRITICAL OPERATIONAL RULES

1.  **CONTAINER ISOLATION**:
    *   **NEVER** run `mypy` or `pytest` on the host machine.
    *   ALWAYS run commands inside the container:
        ```bash
        docker compose exec backend mypy --no-incremental path/to/file.py
        ```
    *   If you need to run the full suite: `docker compose exec backend pytest`.

2.  **PORT ISOLATION**:
    *   You are assigned a specific port range to avoid conflicts with other agents.
    *   Modify your `.env` or `docker-compose.override.yml` to map host ports to your assigned range if you need to run the server.
    *   **Project Name**: Always use `-p <track-name>` with docker compose to isolate containers.
        *   Example: `docker compose -p track-a up -d`

3.  **WORKTREE USAGE**:
    *   You are working in a dedicated git worktree (`../track-a`, `../track-b`, or `../track-c`).
    *   Do not leave your directory.

## 🤖 Track Assignments

### 🟢 Agent A: Scripts & Utilities
*   **Worktree**: `../track-a`
*   **Branch**: `fix/mypy-scripts-utils`
*   **Ports**: API: 8010, DB: 5433, Redis: 6380
*   **Scope**:
    *   `backend/app/utils/seed_data.py`
    *   `backend/app/utils/test_fixtures.py`
    *   `backend/scripts/*.py`
*   **Guidance**:
    *   Most errors will be "Function is missing a return type annotation". Add `-> None` for scripts.
    *   Use `list[str]` instead of `List[str]` (modern syntax).

### 🟡 Agent B: Data Collectors
*   **Worktree**: `../track-b`
*   **Branch**: `fix/mypy-collectors`
*   **Ports**: API: 8020, DB: 5434, Redis: 6381
*   **Scope**:
    *   Start with: `backend/app/services/collectors/base.py` (The Root)
    *   Then: `backend/app/services/collectors/api_collector.py`
    *   Then: All files in `backend/app/services/collectors/*`
*   **Guidance**:
    *   These classes use inheritance. Ensure `abc.abstractmethod` signatures match exactly in subclasses.
    *   External APIs return `Any`. Define `TypedDict` or Pydantic models to cast this data safely.

### 🔴 Agent C: Agents & Trading Engine
*   **Worktree**: `../track-c`
*   **Branch**: `fix/mypy-agents-trading`
*   **Ports**: API: 8030, DB: 5435, Redis: 6382
*   **Scope**:
    *   `backend/app/services/agent/tools/*`
    *   `backend/app/services/agent/nodes/*`
    *   `backend/app/services/trading/*`
    *   `backend/app/services/execution/*`
*   **Guidance**:
    *   **Strict SQLModel**: Be careful with `Optional` fields in DB models.
    *   **LangGraph**: State definitions (`TypedDict`) must be precise.
    *   **Decimal**: Trading logic uses `Decimal`. Do not mix with `float` without explicit casting.

## 🛠️ Step-by-Step Workflow
1.  **Unlock**: Open a file from your scope and remove `# mypy: ignore-errors`.
2.  **Scan**: Run `docker compose -p <track-name> exec backend mypy --no-incremental <file_path>`.
3.  **Fix**: Resolve errors.
    *   *Missing imports*: Import types from `typing`.
    *   *Return types*: Add `-> UseReturnType`.
    *   *Attribute errors*: Check for `Optional` values being accessed without `if x is not None:`.
4.  **Verify**: Run the mypy command again to ensure 0 errors.
5.  **Commit**: `docs(mypy): resolve typing in <filename>` (Keep commits granular).
