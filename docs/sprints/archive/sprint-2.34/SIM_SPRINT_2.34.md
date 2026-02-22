# Sprint 2.34 Initialization Manifest (SIM)

**Sprint Period**: Mar 01, 2026 - Mar 08, 2026
**Focus**: The 4 Ledgers (Collector Expansion)
**Team Composition**: Architect, Dockmaster, Backend (Track A), Backend (Track B), Frontend (Track C)

---

## Sprint Objectives

### Primary Goal
Expand the data collection capability by implementing concrete `ICollector` plugins for all four ledgers (Glass, Human, Catalyst, Exchange), moving beyond the initial prototypes to functional, scheduled collectors running on the new Orchestrator.

### Success Criteria
- [ ] **Glass Ledger**: "Chain-Walker" collector running (tracking block heights/gas on Ethereum/Solana).
- [ ] **Human Ledger**: "RSS Scraper" collector ingest news from at least 2 sources (e.g., CoinDesk, Cointelegraph).
- [ ] **Exchange Ledger**: "CCXT Plugin" integrated, fetching OHLCV data for top 10 assets from Binance/Kraken.
- [ ] **Catalyst Ledger**: "Event Fetcher" running (ingesting economic/crypto calendar events).
- [ ] **Visualization**: Dashboard displays "Events Ingested" stats per ledger.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.
- [ ] **Test Alignment**: Run the full test suite (`bash scripts/test.sh`) at the end of the sprint.
- [ ] **Merge Safety**: Verify that all transient environment changes have been reverted in PRs.
- [ ] **Next Sprint Planning**: Create the next SIM (Sprint 2.35 - Dashboard & Production).

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] Provisioning: Execute `git worktree` setup for Tracks A, B, and C.
- [ ] Initialization: Launch VS Code instances.
- [ ] **Instruction Injection**: Inject track-specific settings.
- [ ] Synchronization: Periodically rebase Track branches.
- [ ] Teardown: Clean up and archive.

## Workspace Orchestration (Dockmaster Only)

**Container Isolation Policy:**

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/COLLECTORS-GH` | `../sprint-2.34/track-a` | `../sprint-2.34/data/agent-a` | `8001` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/COLLECTORS-CE` | `../sprint-2.34/track-b` | `../sprint-2.34/data/agent-b` | `3001` | `#2b9e3e` (Green) | `track-b` |
| **Track C** | `feat/DASHBOARD-HEALTH` | `../sprint-2.34/track-c` | `../sprint-2.34/data/agent-c` | `8002` | `#d15715` (Orange) | `track-c` |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.34/data`
# Track A Setup
- [ ] `git worktree add ../sprint-2.34/track-a -b feat/COLLECTORS-GH`
- [ ] `cp .env ../sprint-2.34/track-a/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-a/' ../sprint-2.34/track-a/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5433\nREDIS_PORT=6380\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.34/track-a/.env`
- [ ] `mkdir -p ../sprint-2.34/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.34/track-a/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8001:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.34/track-a/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.34/data/agent-a --new-window ../sprint-2.34/track-a`

# Track B Setup
- [ ] `git worktree add ../sprint-2.34/track-b -b feat/COLLECTORS-CE`
- [ ] `cp .env ../sprint-2.34/track-b/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-b/' ../sprint-2.34/track-b/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5434\nREDIS_PORT=6381\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.34/track-b/.env`
- [ ] `mkdir -p ../sprint-2.34/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.34/track-b/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"3001:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.34/track-b/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.34/data/agent-b --new-window ../sprint-2.34/track-b`

# Track C Setup
- [ ] `git worktree add ../sprint-2.34/track-c -b feat/DASHBOARD-HEALTH`
- [ ] `cp .env ../sprint-2.34/track-c/.env`
- [ ] `sed -i 's/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=track-c/' ../sprint-2.34/track-c/.env`
- [ ] `echo -e "\nPOSTGRES_PORT=5435\nREDIS_PORT=6382\nDOCKER_IMAGE_BACKEND=backend\nTAG=latest\n" >> ../sprint-2.34/track-c/.env`
- [ ] `mkdir -p ../sprint-2.34/track-c/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#d15715","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.34/track-c/.vscode/settings.json`
- [ ] `echo -e "services:\n  proxy:\n    ports:\n      - \"8002:80\"\n  backend:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  celery_worker:\n    volumes:\n      - /home/mark/omc/logs/hub:/var/log/omc-agents\n    environment:\n      - POSTGRES_PORT=5432\n  prestart:\n    environment:\n      - POSTGRES_PORT=5432" > ../sprint-2.34/track-c/docker-compose.override.yml`
- [ ] `code --user-data-dir ../sprint-2.34/data/agent-c --new-window ../sprint-2.34/track-c`

## Execution Strategy

**Parallelism:**
*   **Track A & B** are independent backend tasks, running in parallel.
*   **Track C** depends on the data produced by A & B but can start by mocking the `CollectorRuns` data to build the charts.

### Track A: Glass & Human Collectors (Backend)

**Agent**: Backend Developer
**Focus**: Glass (Archive/Chain) & Human (Social/News)
**Port**: 8001

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.34 - Track A: Glass & Human Collectors
ROLE: Backend Developer
WORKSPACE ANCHOR: ../sprint-2.34/track-a (Port 8001)

MISSION:
Implement two new `ICollector` plugins.
1. **GlassCollector ("Chain-Walker")**: Connect to a public RPC (e.g., Ethereum/Solana) and fetch the current block height and gas price.
   - *Mock Mode*: If RPC fails or is rate-limited, simulate plausible block data.
2. **HumanCollector ("RSS Scraper")**: Use `feedparser` to ingest news headlines from CoinDesk or Cointelegraph RSS feeds.

OBJECTIVES:
- Create `backend/app/collectors/strategies/glass_chain_walker.py`
- Create `backend/app/collectors/strategies/human_rss.py`
- Register them in `config.py` (or database seed).
- Ensure they are runnable via the Orchestrator.

CONSTRAINTS:
- Use `feedparser` library (add to pyproject.toml if missing).
- Handle network timeouts gracefully.
```

### Track B: Catalyst & Exchange Collectors (Backend)

**Agent**: Backend Developer
**Focus**: Catalyst (Events) & Exchange (Price)
**Port**: 3001

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.34 - Track B: Catalyst & Exchange Collectors
ROLE: Backend Developer
WORKSPACE ANCHOR: ../sprint-2.34/track-b (Port 3001)

MISSION:
Implement two new `ICollector` plugins.
1. **ExchangeCollector ("CCXT Plugin")**: Wrapper around `ccxt` library to fetch OHLCV data.
   - Config: `exchange_id` (e.g., 'binance'), `symbol` (e.g., 'BTC/USDT').
2. **CatalystCollector ("Event Fetcher")**: Simple scraper/fetcher for economic events.
   - *Strategy*: Use a lightweight source or simulate "Upcoming Fed Meeting" events for testing purposes to prove the data pipeline.

OBJECTIVES:
- Create `backend/app/collectors/strategies/exchange_ccxt.py`
- Create `backend/app/collectors/strategies/catalyst_events.py`
- Register them in `config.py` (or database seed).

CONSTRAINTS:
- Use `ccxt` library.
```

### Track C: Dashboard Visualization (Frontend)

**Agent**: Frontend Developer
**Focus**: System Health Dashboard
**Port**: 8002

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.34 - Track C: Dashboard Visualization
ROLE: Frontend Developer
WORKSPACE ANCHOR: ../sprint-2.34/track-c (Port 8002)

MISSION:
Create the "Collector Health Dashboard".
1. **Status Grid**: A visual grid of all collectors status (Red/Green/Gray).
2. **Activity Stream**: A list/table of recent `CollectorRuns` entries (logs).
3. **Volume Chart**: A stacked bar chart showing "Items Collected" per Ledger over time.

OBJECTIVES:
- Create `frontend/src/features/dashboard/CollectorHealth.tsx`
- Utilize `recharts` for visualization.
- Connect to existing `useCollectorStats` hooks (enhance if needed).
```
