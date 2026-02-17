# Sprint 2.27: MyPy Technical Debt Remediation

**Goal**: Eliminate 100% of the `# mypy: ignore-errors` directives from the codebase to enforce strict typing across the entire application.

## 📅 Timeline
*   **Start Date**: Feb 17, 2026
*   **Duration**: 1 Week (Technical Debt Focus)

## 🎯 Objectives
1.  **Strict Mode Compliance**: Ensure `mypy --strict` passes without any file-level ignores.
2.  **Type Safety**: Replace `Any` with specific types (`TypedDict`, `Pydantic Models`, `Optional`, etc.).
3.  **Runtime Safety**: Verify that type changes do not break runtime behavior (tests must pass).

## 🛤️ Execution Tracks (Parallelized)

### 🟢 Track A: Scripts & Utilities (Agent A)
*Status: Ready*
*   **Focus**: Standalone scripts (`backend/scripts/`) and utility modules (`backend/app/utils/`).
*   **Complexity**: Low. Mostly missing return annotations (`-> None`) and simple argument types.
*   **Port Range**: 8010-8019

### 🟡 Track B: Data Collectors (Agent B)
*Status: Ready*
*   **Focus**: The Data Ingestion Layer (`backend/app/services/collectors/`).
*   **Complexity**: Medium. Involves class inheritance (`BaseCollector` -> `APICollector`) and external API schemas.
*   **Strategy**: Fix `base.py` first, then `api_collector.py` then specific collectors.
*   **Port Range**: 8020-8029

### 🔴 Track C: Core Agents & Trading (Agent C)
*Status: Ready*
*   **Focus**: The Service Layer (`backend/app/services/agent/`, `backend/app/services/trading/`).
*   **Complexity**: High. Involves LangChain/LangGraph state, SQLAlchemy models, and financial calculations.
*   **Strategy**: Start with leaf nodes (`tools/`), then `nodes/`, then `agents/` and `orchestrator.py`.
*   **Port Range**: 8030-8039

## 📝 Success Criteria
*   `backend/MYPY_DEBT.md` is empty or deleted.
*   `mypy .` runs successfully without any `ignore-errors` directives.
*   All tests pass.
