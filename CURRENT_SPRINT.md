# Sprint 2.49: Lab 2.0 Integration & Release

**Goal**: Finalize and Stabilize the "Lab 2.0" Architecture for Production Release.

## 🎯 Objectives
1.  **Backend Integrity**: Ensure the Dagger-based execution environment and LangGraph orchestrator are strictly typed and crash-resistant.
2.  **Deployment Reliability**: Fix CI/CD pipeline failures (GitHub Runners) caused by non-idempotent migrations.
3.  **Data Foundation**: Establish the 1-minute aggregation layer (`mv_ohlcv_1m`) for high-frequency analysis in the Lab.
4.  **Frontend Wiring**: Connect the React Flow frontend to the real WebSocket feed (replacing mocks).

## 📋 Status Overview (As of March 14, 2026)

### ✅ Completed
- **Backend Architecture**:
    - Wired `SandboxExecutor` (Dagger) to `lab_nodes.py`.
    - Refactored `lab_nodes.py` to use real tools instead of mocks.
    - Implemented `mv_ohlcv_1m` Materialized View via Alembic migration (`c2a4b6c8d0e2`).
    - Fixed `shap` missing dependency in Dockerfile.
- **Code Quality**:
    - **Linting**: 100% pass on `scripts/lint.sh` (Mypy Strict + Ruff).
    - **Typing**: Resolved complex SQLModel/SQLAlchemy typing issues in `agent.py` and `websockets.py`.
- **Infrastructure**:
    - **Migration Fix**: Made `c2a4b6c8d0e2` idempotent by dropping conflicting views/tables before creation.
    - **Build**: Successfully rebuilt backend container with new dependencies.

### 🚧 In Progress / Next Steps
- **CI/CD Verification**: Monitor the GitHub Action run for the `fix: make alembic migration...` commit.
- **Test Suite**: Investigate and resolve the 21 failures in `test_llm_credentials_integration.py` and `test_llm_credential_isolation.py` (likely fixture/environment issues unrelated to recent changes, but blocking clean green state).
- **Frontend Integration**: Verify the React Flow graph correctly renders updates from the real `lab_nodes.py`.

## 📝 Technical Notes
- **Dagger**: The `SandboxExecutor` now runs in a privileged container mode (implicitly, via the orchestrator setup) to spawn sibling containers.
- **LangGraph**: The graph state is fully typed with `LabState` (TypedDict).
- **Database**: The `mv_ohlcv_1m` view is a materialized view, meaning it needs refreshing. The `RefreshScheduler` (from Sprint 2.48) should be configured to refresh this view.

## 🛑 Blockers
- None at this moment. Waiting on CI/CD feedback.

