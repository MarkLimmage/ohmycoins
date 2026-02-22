## [INITIALIZATION] - Sprint 2.33 Track A
**Intent**: Initialize workspace for Sprint 2.33 - Track A (Scheduler Service).
**Status**: IN_PROGRESS
**Context**: You are working on the Backend Scheduler Service in `track-a`.
**Sprint Goal**: Implement the Database-Driven Scheduler using `apscheduler` or similar, replacing the in-memory solution.
**Key Files**:
- `backend/app/services/scheduler.py` (create/edit this)
- `backend/app/models.py` (add SchedulerJob models)
- `CURRENT_SPRINT.md` (sprint details)
- `ROADMAP.md` (project vision)

## [2026-02-22] - Refactor Orchestrator to Database
**Intent**: Implement database-driven scheduler and API endpoints for manual triggering.
**Status**: COMPLETED
**Monologue**: 
I have refactored the  in  to be . 
It now loads jobs from the  table using .
It supports both legacy  (via ) and new  plugins (via ).

I have updated  to add:
- `POST /{id}/run`: Trigger manual run immediately via scheduler.
- `PATCH /{id}`: Update collector config and refresh scheduler.
- `PUT /{id}` and `POST /{id}/toggle` also refresh the scheduler automatically.

I have verified the scheduler logic with a new test suite: `backend/tests/services/test_scheduler_db.py`.
The tests pass and confirm correct job loading and execution dispatching.

## [2026-02-22] - Refactor Orchestrator to Database
**Intent**: Implement database-driven scheduler and API endpoints for manual triggering.
**Status**: COMPLETED
**Monologue**: 
I have refactored the `CollectorScheduler` in `backend/app/services/scheduler.py` to be `DatabaseScheduler`. 
It now loads jobs from the `Collector` table using `schedule_cron`.
It supports both legacy `CoinspotCollector` (via `run_legacy_collector`) and new `ICollector` plugins (via `CollectorRegistry`).

I have updated `backend/app/api/routes/collectors.py` to add:
- `POST /{id}/run`: Trigger manual run immediately via scheduler.
- `PATCH /{id}`: Update collector config and refresh scheduler.
- `PUT /{id}` and `POST /{id}/toggle` also refresh the scheduler automatically.

I have verified the scheduler logic with a new test suite: `backend/tests/services/test_scheduler_db.py`.
The tests pass and confirm correct job loading and execution dispatching.
