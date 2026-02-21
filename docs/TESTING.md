# Testing Guide

**Last Updated:** 2026-02-21
**Environment:** **STRICT CONTAINER ISOLATION**
**Protocol:** All tests MUST be executed within Docker containers. Host-side testing (venvs) is strictly forbidden.

---

## 🛑 Critical Protocol: Container Isolation

This project uses a multi-agent, single-machine architecture where multiple development tracks run in parallel using `git worktree`.

- **DO NOT** create a local virtual environment (`venv`) on the host machine.
- **DO NOT** run `pytest` or `npm test` directly on the host.
- **ALWAYS** use `docker compose run` to execute tests within your track's isolated container.

### Why?
1.  **Database Isolation**: Each track (A, B, C) has its own dedicated PostgreSQL and Redis containers (e.g., `track-a-db`, `track-b-redis`). Running locally would attempt to connect to localhost ports which may conflict or be managing a different track's state.
2.  **Environment Consistency**: The CI/CD pipeline runs in Docker. Your dev environment must match it exactly.
3.  **Dependency Management**: Python and Node flavors are pinned in the Docker images.

---

## Quick Start: Running Tests

### 1. Identify Your Track
Confirm which track you are working in. The `docker-compose.override.yml` and `.env` in your current directory define your context.

```bash
# Verify where you are
pwd 
# Output: /home/mark/omc/ohmycoins/sprint-2.28/track-a
```

### 2. Verify Environment (.env)
Your track MUST have a `.env` file configured with your unique project name.

```bash
grep COMPOSE_PROJECT_NAME .env
# Output: COMPOSE_PROJECT_NAME=track-a
```
*If this is missing or wrong, STOP. Request the Dockmaster to re-provision your workspace logic.*

### 3. Run Backend Tests (Pytest)
Execute the test suite inside the `backend` service container.

```bash
# Run all tests (Auto-discovers and runs pytest)
docker compose run --rm backend pytest

# Run specific test file
docker compose run --rm backend pytest tests/api/test_users.py

# Run with verbose output
docker compose run --rm backend pytest -v

# Run only tests matching a keyword
docker compose run --rm backend pytest -k "trade_execution"
```

### 4. Run Frontend Tests (Vitest/Playwright)
Execute frontend unit tests inside the `frontend` container.

```bash
# Run unit tests
docker compose run --rm frontend npm run test

# Run specific test file
docker compose run --rm frontend npm run test src/components/Button.test.tsx
```

---

## Startup Scripts & Database Readiness

The test suite relies on `tests_pre_start.py` to ensure the database is ready before running tests.

- When you run `docker compose run --rm backend pytest`, Docker starts the `db` container (if defined in `depends_on`).
- But the Postgres service inside might not be ready for connections immediately.
- **Best Practice**: If you encounter connection errors, ensure your stack is up first:

```bash
docker compose up -d db redis
docker compose run --rm backend pytest
```

---

## Full Suite Execution (CI Simulation)

To run the exact command used in CI (which includes linting, full teardown/setup), use the provided script:

```bash
# Runs from the host, but executes everything in Docker
bash scripts/test.sh
```

**Note:** This script performs a `docker compose down` at the end, so it will stop your dev containers. Use specific `pytest` commands for iterative development.

---

## Updates to Models or DB Schema

If you change `models.py`, you must generate migrations inside the container:

```bash
docker compose run --rm backend alembic revision --autogenerate -m "Add new field"
docker compose run --rm backend alembic upgrade head
```

Then run tests to ensure no regressions.

---

## Troubleshooting

### "Connection Refused" to Database
**Cause**: The database container for your track isn't running or `COMPOSE_PROJECT_NAME` is mismatched.
**Fix**:
1. Check `.env` for `COMPOSE_PROJECT_NAME`.
2. `docker compose up -d db`
3. Check logs: `docker compose logs db`

### "Table Not Found"
**Cause**: The test database hasn't been initialized or Alembic migrations haven't run.
**Fix**:
```bash
docker compose run --rm backend alembic upgrade head
```
