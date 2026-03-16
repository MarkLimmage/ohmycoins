# Worker Testing Protocol (v1.2)

**Purpose:** Prevent port conflicts and dependency errors during parallel worktree development.
Workers MUST test inside Docker containers, never on the host machine.

---

## 1. Golden Rule

> **Never run `pytest`, `ruff`, `mypy`, `npm test`, or `tsc` directly on the host.**
> Always use `docker compose exec` or `docker compose run` to execute inside containers.

---

## 2. Port Isolation

Each service uses fixed internal ports. The `docker-compose.override.yml` maps them to host ports
that avoid conflicts with other worktrees or host services.

| Service       | Internal Port | Host Port (override) | Notes                   |
|--------------|---------------|---------------------|-------------------------|
| Traefik HTTP | 80            | 8010                | API gateway             |
| Traefik dash | 8080          | 8091                | Dashboard               |
| PostgreSQL   | 5432          | 5433                | Dev DB                  |
| Backend      | 8000          | (via Traefik)       | Not directly exposed    |
| MLflow       | 5000          | 5000                | Tracking UI             |
| Mock WS      | 8001          | 8003                | Supervisor mock server  |
| Frontend     | 5173          | 5173                | Vite dev server (local) |

**Workers must NOT expose additional ports or modify docker-compose.override.yml** without filing
a `CONTRACT_RFC.md` explaining the need.

---

## 3. Backend Testing Commands

All backend tests run inside the `backend` container which has all Python dependencies installed.

### 3.1 Run pytest (Unit Tests)
```bash
# Run all tests
docker compose exec backend python -m pytest tests/ -v

# Run a specific test file
docker compose exec backend python -m pytest tests/services/agent/test_hitl.py -v

# Run with coverage
docker compose exec backend python -m pytest tests/ --cov=app --cov-report=term-missing
```

### 3.2 Run ruff (Linting)
```bash
# Check for lint errors
docker compose exec backend python -m ruff check app/

# Auto-fix lint errors
docker compose exec backend python -m ruff check app/ --fix

# Format check
docker compose exec backend python -m ruff format app/ --check
```

### 3.3 Run mypy (Type Checking)
```bash
docker compose exec backend python -m mypy app/ --ignore-missing-imports
```

### 3.4 Full Lint Suite (one command)
```bash
docker compose exec backend bash -c "
  python -m ruff check app/ && \
  python -m ruff format app/ --check && \
  python -m mypy app/ --ignore-missing-imports
"
```

---

## 4. Frontend Testing Commands

Frontend tests run inside the `frontend-dev` container or via `npm` inside the container.

### 4.1 TypeScript Check
```bash
# If using the frontend-dev service from docker-compose.override.yml:
docker compose run --rm frontend-dev npx tsc --noEmit

# Or build the production image (catches all TS errors):
docker compose build frontend
```

### 4.2 Unit Tests
```bash
docker compose run --rm frontend-dev npm run test:unit
```

### 4.3 Lint (Biome)
```bash
docker compose run --rm frontend-dev npx biome check src/
```

---

## 5. Pre-Commit Checklist (Before Reporting Completion)

Workers must complete ALL of these before reporting to the Supervisor:

1. **Syntax check passes** — `ruff check` or `tsc --noEmit` (inside container)
2. **Tests pass** — `pytest` or `npm run test:unit` (inside container)
3. **No uncommitted files** — `git status` shows `nothing to commit, working tree clean`
4. **Commit message follows convention** — `feat(scope):`, `fix(scope):`, `docs:` prefix

---

## 6. Troubleshooting

### "Port already in use"
Don't kill host processes. Instead:
```bash
docker compose down --remove-orphans
```

### "Module not found" errors
You're running on the host. Use the container:
```bash
docker compose exec backend python -m pytest  # NOT: pytest
```

### Container not running
```bash
docker compose up -d backend  # Start just the backend
docker compose logs backend   # Check for startup errors
```
