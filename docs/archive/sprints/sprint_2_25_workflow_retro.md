# Sprint 2.25 Retrospective: Development Workflow & Tooling

**Date:** February 14, 2026
**Focus:** Track C (Frontend/Audit) & Cross-Cutting Config
**Participants:** The Architect, The Frontend Lead

## 📊 Overview
While the feature goals for Track C (Audit Logs & Kill Switch History) were met, the development session was characterized by significant friction related to the **local development environment** and **Docker containerization**.

This retrospective specifically targets the "Developer Experience" (DX) issues encountered to prevent recurrence in future sprints.

## 🛑 Critical Friction Points

### 1. Docker Internal Networking Mismatch
*   **Issue**: The backend container initially failed to connect to the database with `psycopg.OperationalError`.
*   **Root Cause**: The `.env` configuration specified `POSTGRES_SERVER=postgresserver` (likely a legacy or cloud-template value), but the Docker Compose service is named `db`.
*   **Resolution**: Manually updated `.env` to `POSTGRES_SERVER=db`.
*   **Impact**: 15-30 minutes of debugging connectivity.
*   **Action Logic**: Ensure `.env.example` aligns strictly with `docker-compose.yml` service names.

### 2. Alembic Migration Complexity ("The Immutable Index")
*   **Issue**: Applying the migration for `TradeAudit` failed with `psycopg.errors.InvalidObjectDefinition`.
*   **Root Cause**: SQLModel/Alembic auto-generated a Unique Index on the `TradeAudit` model that involved a type cast (Datetime -> Date). Postgres requires functions in indexes to be marked `IMMUTABLE`, but the cast was not.
*   **Resolution**: Manually patched the migration file (`versions/1d0434380682_...`) to remove the problematic index.
*   **Lesson**: "Auto-generate" is not "Auto-correct". Complex constraints involving dates need manual review.

### 3. "Host vs. Container" Context Switching
*   **Issue**: Repeated failures when trying to run utility scripts or generators from the host terminal.
    *   `npm run generate-client`: Failed (missing dependencies on host).
    *   `python tests/populate_trade_audits.py`: Failed (`ModuleNotFoundError: No module named 'app'`).
*   **Root Cause**: The project relies on containerized dependencies, but dev habits/scripts often assume a local environment.
*   **Resolution**: Shifted exclusively to `docker compose exec [frontend|backend] [command]`.
*   **Action Logic**: All scripts in `scripts/` should automatically detect if they are running on host and wrap the command in `docker compose exec` if necessary.

## 🛠 Action Items for Sprint 2.26

| Category | Action | Owner | Priority |
| :--- | :--- | :--- | :--- |
| **DevOps** | Update `scripts/` to force execution inside containers (e.g., `run_in_backend.sh`). | The Architect | High |
| **Config** | Audit `.env` vs `docker-compose.yml` consistency. | DevOps | Medium |
| **Docs** | Update `README.md` "Getting Started" to emphasize `docker compose exec`. | Tech Writer | Medium |
| **DB** | Add a pre-commit check or linter warning for functional indexes in Alembic. | Backend Lead | Low |

## 📉 Velocity Impact
*   **Estimated Drag**: ~20% of sprint time lost to environment debugging.
*   **Effective Velocity**: High (Features delivered), but **Efficiency** was Low.

## ✅ Conclusion
The "Local Linux Server" transition is functionally complete, but the developer tooling has not yet fully adapted to a "Container-First" mindset. We must stop trying to run code on the host OS.
