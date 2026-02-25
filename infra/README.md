# Oh My Coins - Infrastructure Notes

## Overview

This folder contains infrastructure documentation, notes, and configs for local server deployment.
The primary stack is defined in `/docker-compose.yml` at the project root.

---

## Docker Services

| Service | Replicas | Role |
|---|---|---|
| `proxy` | 1 | Traefik v3.6 reverse proxy — routes traffic to backend/frontend |
| `db` | 1 | PostgreSQL 17 — persistent volume `app-db-data` |
| `redis` | 1 | Redis 7 — persistent volume `app-redis-data` |
| `prestart` | 1 (one-shot) | Runs `scripts/prestart.sh` (migrations + seed) before backend starts |
| `backend` | 2 | FastAPI API replicas — `RUN_COLLECTORS=False` |
| `orchestrator` | 1 | FastAPI — single replica with `RUN_COLLECTORS=True`; runs collector scheduler |
| `celery_worker` | 1 | Legacy async task queue |
| `watcher` | 1 | Hard-stop kill switch monitor |
| `frontend` | 2 | React/Nginx replicas |
| `adminer` | 1 | Postgres admin UI (optional, for development) |

---

## Environment Variables and Secrets

### How Secrets Are Loaded

All services use `env_file: - .env` in docker-compose.yml, which loads the entire `.env` file
into every container's environment. The explicit `environment:` blocks in docker-compose.yml
are used only to:
- **Override** specific values (e.g., `POSTGRES_SERVER=db` overrides the `.env` default of `localhost`)
- **Set service-specific flags** (e.g., `RUN_COLLECTORS=True/False`)
- **Ensure required vars cause startup failure** if unset (e.g., `${VAR?Variable not set}`)

### Collector API Keys

The following collector API keys are defined in `.env` and automatically passed to all containers
via `env_file`. They do NOT need explicit `environment:` entries in docker-compose.yml:

| Variable | Purpose | Collector |
|---|---|---|
| `CRYPTOPANIC_API_KEY` | Crypto news sentiment | Human Ledger |
| `NEWSCATCHER_API_KEY` | Premium news (Tier 2) | Human Ledger |
| `NANSEN_API_KEY` | Smart money tracking (Tier 2) | Glass Ledger |
| `COINSPOT_USE_WEB_SCRAPING` | Scraper vs API mode | Exchange Ledger |

**Verification**: `env_file` loads ALL variables from `.env`. Only the orchestrator service
(with `RUN_COLLECTORS=True`) actually uses these keys at runtime — the backend replicas
have collectors disabled.

### Secrets Management

- **Local development**: `.env` file at project root (never commit this!)
- **Multi-track development**: Use `populate_secrets.sh` to copy secrets into a worktree
- **CI/CD (self-hosted runner)**: `populate_secrets.sh` pulls from `~/omc/secrets.safe`
- **Staging/Production (future)**: AWS Secrets Manager via ECS task definition secrets injection

---

## Starting the Stack

```bash
# Requires traefik-public external network
docker network create traefik-public || true

# Start all services (builds if needed)
docker compose up -d --build

# Wait for all healthchecks to pass
docker compose up -d --wait --build

# Live reload with file watching
docker compose watch

# View logs
docker compose logs -f orchestrator
docker compose logs -f backend
```

## Stopping and Resetting

```bash
# Stop all services
docker compose down

# Stop and remove all volumes (WARNING: destroys database!)
docker compose down -v

# Reset just the database (use the helper script)
bash scripts/db-reset.sh
```

---

## GitHub Actions Workflows

| Workflow | Trigger | Runner | Purpose |
|---|---|---|---|
| `deploy-local.yml` | push to main, manual | self-hosted | Deploy to local server at 192.168.0.241 |
| `test-backend.yml` | push/PR | self-hosted (eks, test) | Run pytest suite |
| `lint-backend.yml` | push/PR | ubuntu-latest | mypy + ruff check |
| `test-infrastructure.yml` | manual, infra path changes | self-hosted (eks, test) | Terraform validation |
| `build.yml` | - | - | Docker image builds |
| `generate-client.yml` | - | - | OpenAPI TypeScript client generation |
| `playwright.yml` | - | - | E2E frontend tests |

### Self-Hosted Runner Notes

- The local server at `192.168.0.241` acts as a GitHub Actions self-hosted runner
- Secrets are stored in `~/omc/secrets.safe` on the host machine
- `deploy-local.yml` calls `populate_secrets.sh .` to hydrate `.env` before `docker compose up`
- The `traefik-public` Docker network must exist on the host before stack startup

---

## Network Architecture

```
Internet / LAN
    |
    v
[Traefik proxy :8001] (external network: traefik-public)
    |
    +---> [backend :8000] x2 replicas (RUN_COLLECTORS=False)
    +---> [frontend :80] x2 replicas
    +---> [adminer :8080]
    |
    (internal default network)
    |
    +---> [orchestrator :8000] x1 replica (RUN_COLLECTORS=True)
    +---> [db :5432]
    +---> [redis :6379]
    +---> [celery_worker]
    +---> [watcher]
```

---

## Traefik Routing Rules

| Service | Rule |
|---|---|
| backend | `Host(api.localhost)` OR `Host(192.168.0.241)` AND `PathPrefix(/api)` |
| frontend | `Host(localhost)` OR `Host(dashboard.localhost)` OR `Host(192.168.0.241)` |
| adminer | `Host(adminer.<DOMAIN>)` |

Proxy dashboard: http://192.168.0.241:8090

---

## Critical Constraints

1. **Orchestrator must be a single replica** — Running multiple orchestrator instances causes
   duplicate data collection jobs. Never scale it above 1.

2. **Backend replicas must have `RUN_COLLECTORS=False`** — This is set explicitly in
   docker-compose.yml environment block to override the `.env` default if any.

3. **`traefik-public` network must be external** — The network is declared as `external: true`
   in docker-compose.yml. Create it manually before first run.

4. **`prestart` service must complete before backend/orchestrator** — Handled by
   `depends_on: prestart: condition: service_completed_successfully`.
