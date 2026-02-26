# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Oh My Coins (OMC)** is an autonomous multi-agent cryptocurrency trading platform with a "Lab-to-Floor" pipeline: collect data → analyze with AI agents → deploy strategies → execute trades. It targets a local Linux server deployment (not cloud).

---

## Commands

### Running the Stack

```bash
# Start full development stack (includes live reload via bind mounts)
docker compose up -d --build

# Live reload with file watching
docker compose watch

# View logs
docker compose logs -f backend
```

### Backend (Python / FastAPI)

All testing and linting must be done inside the Docker container, not in local venvs.

```bash
# Run all tests with coverage
docker compose exec backend bash scripts/test.sh

# Run specific tests or a single test file
docker compose exec backend bash scripts/tests-start.sh tests/api/routes/test_collectors.py

# Run with a marker filter
docker compose exec backend bash scripts/tests-start.sh -m "not integration"

# Run a single test function
docker compose exec backend bash scripts/tests-start.sh tests/api/routes/test_collectors.py::test_list_collectors

# Lint (mypy + ruff check)
docker compose exec backend bash scripts/lint.sh

# Format (ruff format)
docker compose exec backend bash scripts/format.sh

# Run database migrations manually
docker compose exec backend alembic upgrade head

# Reset database
bash scripts/db-reset.sh

# Generate OpenAPI client (after API changes)
bash scripts/generate-client.sh
```

### Frontend (React / TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Dev server (local, not Docker) — http://localhost:5173
npm run dev

# Type check
npm run type-check

# Lint/format via Biome
npm run lint

# Build for production
npm run build

# Storybook — http://localhost:6006
npm run storybook

# E2E tests (requires backend running)
npx playwright test
npx playwright test --ui
```

### Pre-commit Hooks

```bash
pre-commit run --all-files
```

---

## Code Quality Constraints

- **Backend**: `mypy --strict` must pass. Ruff enforces code style. No hardcoded secrets — use env vars.
- **Frontend**: Biome is the formatter/linter (replaces ESLint + Prettier).
- **SQLModel limitation**: Avoid bidirectional relationships with collections. Use unidirectional queries only.
- **AsyncMock**: Use `MagicMock` (not `AsyncMock`) for context managers in tests — AsyncMock wraps return values in coroutines.
- **Agent code**: Always runs in a RestrictedPython sandbox — no network access from generated code.

---

## Architecture

### High-Level: Lab-to-Floor Pipeline

```
4 Ledgers (Data Collection) → The Lab (AI Analysis) → The Floor (Trading Execution)
```

1. **Collectors** continuously gather data from external sources into PostgreSQL.
2. **The Lab** (LangGraph agent workflow) queries that data, generates ML models, and produces trading algorithms.
3. **The Floor** deploys and executes those algorithms via CoinSpot's private API, with real-time risk management.

### Docker Services

| Service | Role |
|---|---|
| `proxy` | Traefik v3.6 reverse proxy — routes traffic to backend/frontend |
| `db` | PostgreSQL 17 |
| `redis` | Redis 7 — cache, rate limiting, session state |
| `backend` | FastAPI API — 2 replicas, stateless, `RUN_COLLECTORS=False` |
| `orchestrator` | FastAPI — single replica with `RUN_COLLECTORS=True`; runs the data collection scheduler |
| `frontend` | React/Nginx — 2 replicas |
| `celery_worker` | Legacy async task queue |
| `watcher` | Hard-stop kill switch monitor process |

**Critical**: The orchestrator must run as a single instance. Backend replicas set `RUN_COLLECTORS=False` to prevent duplicate data collection jobs.

### Backend Structure (`backend/app/`)

- **`main.py`** — FastAPI lifespan: starts collectors, order queue, execution scheduler
- **`models.py`** — All SQLModel table definitions (~62K). Single source of truth for DB schema.
- **`crud.py`** — Database read/write operations
- **`core/config.py`** — `Settings` via pydantic-settings; reads from `../.env` (root-level)
- **`core/db.py`** — SQLAlchemy engine and session factory
- **`api/routes/`** — FastAPI route modules (collectors, trading, floor, pnl, risk, users, agent, credentials, websockets)
- **`services/collectors/`** — Phase 2.5 data collection engine
- **`services/trading/`** — Order execution, scheduling, CoinSpot client, paper trading
- **`services/agent/`** — LangGraph-based AI agent system (The Lab)
- **`alembic/`** — Database migrations

### The 4 Ledgers (Data Collection)

Implemented in `services/collectors/`. All collectors implement `BaseCollector` from `services/collectors/base.py`:

| Ledger | Directory | Sources |
|---|---|---|
| **Glass** | `collectors/glass/` | DeFiLlama, On-chain metrics, Nansen SmartMoney |
| **Human** | `collectors/human/` | CryptoPanic, Newscatcher, Reddit |
| **Catalyst** | `collectors/catalyst/` | SEC filings, Exchange listings |
| **Exchange** | `collectors/exchange/` | CoinSpot public API/scraper |

Collectors register via `services/collectors/config.py` → `setup_collectors()`. Each run is tracked in `CollectorRuns`.

### The Lab (AI Agent System)

Implemented in `services/agent/`. LangGraph state machine with these agent nodes:

`Initialization → Data Retrieval → Analysis → Training → Evaluation → Reporting`

- **`orchestrator.py`** — Entry point: `AgentOrchestrator.execute_step()`
- **`langgraph_workflow.py`** — State machine definition
- **`agents/`** — Individual agent implementations (Data Retrieval, Analyst, Trainer, Evaluator, Reporting)
- **`nodes/`** — LangGraph node wrappers
- **`tools/`** — Agent tools for querying ledger data

LLM providers are configurable (OpenAI, Anthropic, Google Gemini) — selected per session.

### The Floor (Trading Execution)

Implemented in `services/trading/`:

- **`executor.py`** — `OrderExecutor`: queue-based execution with retry
- **`scheduler.py`** — `ExecutionScheduler`: APScheduler for strategy lifecycle
- **`safety.py`** — `TradingSafetyManager`: hard-coded pre-trade risk validation
- **`client.py`** — `CoinSpotTradingClient`: private API wrapper
- **`paper_exchange.py`** — Paper trading simulation with slippage

Modes: **Ghost** (paper, no real orders), **Live** (real orders), **Backtest** (historical simulation).

### Frontend Structure (`frontend/src/`)

- **`routes/`** — TanStack Router page components
- **`components/`** — Reusable UI; key subdirs: `Floor/`, `Ledgers/`, `Lab/`
- **`features/`** — Feature modules (`floor/`, `performance/`, etc.)
- **`client/`** — Auto-generated OpenAPI TypeScript client (do not edit manually)
- **`hooks/`** — Custom React hooks
- **`theme/`** — Chakra UI v3 theming

State management: TanStack Query for server state. Routing: TanStack Router (file-based, `routeTree.gen.ts` is generated).

---

## Multi-Track Development (Agent Worktrees)

When running parallel development tracks, each track gets an isolated git worktree with unique ports (from `AGENT_INSTRUCTIONS.md`):

| Track | HTTP | DB | Redis |
|---|---|---|---|
| A | 8010 | 5433 | 6380 |
| B | 8020 | 5434 | 6381 |
| C | 8030 | 5435 | 6382 |

- Never edit root `docker-compose.yml` from a track — use `docker-compose.override.yml`
- Check `INSTRUCTIONS_OVERRIDE.md` in the worktree before each task (written by the Architect agent to break loops)
- Maintain `LOGBOOK.md` in the worktree root with format: `## [TIMESTAMP] - [TASK_NAME]`

---

## Key Environment Variables

Set in root `.env` (see `.env.template`):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | JWT signing (`openssl rand -hex 32`) |
| `POSTGRES_*` | Database credentials |
| `REDIS_HOST`, `REDIS_PORT` | Cache |
| `OPENAI_API_KEY` | Required for Lab agents |
| `ANTHROPIC_API_KEY` | Optional alternative LLM |
| `RUN_COLLECTORS` | `True` on orchestrator only, `False` on backend replicas |
| `AUTO_SEED_DB` | Seed default data on startup (default: `true`) |
| `COINSPOT_USE_WEB_SCRAPING` | Scraper vs API for exchange data |

---

## Key Docs

- `docs/ARCHITECTURE.md` — System design and microservice contracts
- `docs/API_CONTRACTS.md` — API response formats and error codes
- `docs/TESTING.md` — Test strategy (target: >97% coverage)
- `ROADMAP.md` — Strategic phases
- `CURRENT_SPRINT.md` — Active sprint tasks
- `LOGBOOK.md` — Development history
- `AGENT_INSTRUCTIONS.md` — Agent governance and persona definitions

---

## Agent Bootstrap & Delegation Protocol

These rules apply to ALL agents (Architect, Dockmaster, Dev) and to any process that spawns them.

### Bootstrap Sequence (Mandatory First Actions)

Every agent MUST execute these 5 steps before any other work:

1. **Read own role file**: `.claude/agents/{your-name}.md` — confirms your model, tools, and constraints.
2. **Read `AGENT_INSTRUCTIONS.md`** — contains governance rules, the `!reset []` YAML template, port formulas, and context injection protocols.
3. **Read `CURRENT_SPRINT.md`** — identifies active tasks and priorities.
4. **Check `INSTRUCTIONS_OVERRIDE.md`** — if present in the worktree, its contents override your current plan.
5. **Log to `LOGBOOK.md`** — record your start timestamp, assigned task, and bootstrap confirmation.

### Spawner Protocol (For Any Agent Creating Another)

Before calling the Task tool to spawn an agent, the spawner MUST:

1. **Read `.claude/agents/{target}.md`** to obtain the correct `model` and `tools` from the frontmatter.
2. **Use the model from the frontmatter** in the Task tool call. The canonical models are:
   - `architect` → `model: opus`
   - `dockmaster` → `model: sonnet`
   - `dev` → `model: haiku`
3. **Include a bootstrap instruction** in the Task prompt: "Before starting work, execute the Bootstrap Sequence from CLAUDE.md."
4. **Define clear success criteria** in the Task prompt so the agent knows when it is done.

### Delegation Boundary Protocol

Once a task is delegated to another agent:

- **The delegator MUST NOT perform the delegated work** — no running the same tests, builds, or health checks in parallel.
- **Status inquiries only** — the delegator may send a message asking for status, but must not duplicate effort.
- **No silent takeover** — if a delegated agent appears stalled, send a status inquiry first. Only escalate (reassign or take over) after receiving no response.
- **One owner per task** — a task has exactly one responsible agent at any time. Transfer ownership explicitly via TaskUpdate before intervening.

### Report-Back Protocol

When an agent completes a delegated task, it MUST send a structured report:

```
TASK REPORT
STATUS: completed | blocked | failed
RESULT: <one-line summary>
DELIVERABLES: <files changed, tests passed, endpoints verified>
ISSUES: <blockers, warnings, or "none">
```

If no report is received within a reasonable time, the delegator should send a status inquiry — not take over the work.
