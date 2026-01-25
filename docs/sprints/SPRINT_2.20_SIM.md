# Sprint 2.20 Initialization Manifest (SIM) - The Tactician

**Sprint Period**: March 22, 2026 - April 4, 2026
**Focus**: Execution Algorithms & Paper Trading Simulation
**Team Composition**: The Dockmaster, The Feature Developer (x2), The Quality Agent

---

## Sprint Objectives

### Primary Goal
Build "The Tactician" - the execution arm of the system. Implement a realistic "Paper Trading" environment and standard execution algorithms (TWAP, VWAP) to optimize trade entry and exit without risking real capital.

### Success Criteria
- [ ] **Paper Exchange**: A mock exchange adapter running in memory/Redis that duplicates the live exchange interface.
- [ ] **TWAP/VWAP**: Functional execution algorithms capable of splitting parent orders into child orders.
- [ ] **Slippage Implementation**: Simulated latency and slippage in the Paper Trading environment.
- [ ] **Execution Reports**: Post-trade analysis showing "Implementation Shortfall" (Decision Price vs. Avg Fill Price).

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.
- [ ] **Next Sprint Planning**: Create the next SIM using `docs/sprints/SIM_TEMPLATE.md`, ensuring **zero drift** from the template structure.

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] Provisioning: Execute `git worktree` setup for Tracks A, B, and C.
- [ ] Initialization: Launch VS Code instances with unique `--user-data-dir`.
- [ ] Synchronization: Periodically rebase Track branches with `main` to prevent drift.
- [ ] Teardown: Clean up worktrees and archive logs upon Track completion.

## Workspace Orchestration (Dockmaster Only)

The Dockmaster Agent must execute the following `git worktree` and environment setups before activating Track A, B, and C.

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-FL-021-paper-trading` | `../sprint-2.20/track-a` | `../sprint-2.20/data/agent-a` | `8001` | `#3771c8` (Blue) |
| **Track B** | `feat/REQ-FL-022-execution-algos` | `../sprint-2.20/track-b` | `../sprint-2.20/data/agent-b` | `3001` | `#2b9e3e` (Green) |
| **Track C** | `feat/REQ-FL-023-metrics` | `../sprint-2.20/track-c` | `../sprint-2.20/data/agent-c` | `8002` | `#d15715` (Orange) |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.20/data`
- [ ] `git worktree add ../sprint-2.20/track-a feat/REQ-FL-021-paper-trading`
- [ ] `mkdir -p ../sprint-2.20/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.20/track-a/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.20/data/agent-a --new-window ../sprint-2.20/track-a`
- [ ] `git worktree add ../sprint-2.20/track-b feat/REQ-FL-022-execution-algos`
- [ ] `mkdir -p ../sprint-2.20/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.20/track-b/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.20/data/agent-b --new-window ../sprint-2.20/track-b`
- [ ] `git worktree add ../sprint-2.20/track-c feat/REQ-FL-023-metrics`
- [ ] `mkdir -p ../sprint-2.20/track-c/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#d15715","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.20/track-c/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.20/data/agent-c --new-window ../sprint-2.20/track-c`

---

### Track A: The Engine Room (Paper Trading)

**Agent**: The Feature Developer (Backend Specialist)
**Requirements**: [REQ-FL-021]
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.20 - Track A: Paper Trading Engine
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.20/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: SYSTEM_REQUIREMENTS.md (Section 8.4)
    - Tier 1: API_CONTRACTS.md (Trading Interfaces)
  
  WRITE/UPDATE:
    - Tier 2: backend/app/services/trading/paper_exchange.py
    - Tier 2: backend/app/services/trading/README.md

MISSION:
Implement `PaperExchange`, a class that mimics the `CCXTExchange` interface but stores all orders and balances in Redis/Memory. It must support `create_order`, `fetch_balance`, and `fetch_order` with 0ms network latency but simulated execution logic.

SPECIFIC OBJECTIVES:
1. Create `PaperExchange` class inheriting from `BaseExchange`.
2. Implement an in-memory `OrderBook` simulation to match Market orders against simulated liquidity.
3. Ensure no real API keys are ever accessed in Paper Mode.

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update `backend/app/services/trading/README.md` with Paper Trading architecture.
    - [ ] Define the "Paper Mode" configuration flag in `config.py`.
```

---

### Track B: The Algo Lab (Execution Algorithms)

**Agent**: The Feature Developer (Quant Specialist)
**Requirements**: [REQ-FL-022]
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.20 - Track B: Execution Algorithms
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.20/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: API_CONTRACTS.md
    - Tier 2: backend/app/services/trading/README.md
  
  WRITE/UPDATE:
    - Tier 2: backend/app/services/execution/twap.py
    - Tier 2: backend/app/services/execution/vwap.py

MISSION:
Implement standard execution algorithms that break large "Parent Orders" into smaller "Child Orders" over time.

SPECIFIC OBJECTIVES:
1. Implement `TWAPStrategy`: Splits order size S into N chunks over time T.
2. Implement `VWAPStrategy`: Splits order based on historical volume profile (from `PriceData5Min`).
3. Create `AlgoOrderManager` to track the state of active parent orders.

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Create `backend/app/services/execution/README.md` explaining TWAP/VWAP logic.
    - [ ] Define `AlgoOrder` Pydantic models.
```

---

### Track C: The Oversight (Metrics & Quality)

**Agent**: The Quality Agent
**Requirements**: [REQ-FL-023]
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.20 - Track C: Execution Metrics & Governance
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Quality Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.20/track-c
  INSTANCE_PORT: 8002
  STRICT_SCOPE: You are locked to this directory.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: SYSTEM_REQUIREMENTS.md
  
  WRITE/UPDATE:
    - Tier 2: backend/app/services/compliance/reporting.py
    - Tier 1: API_CONTRACTS.md (add Execution Report endpoints)

MISSION:
Ensure that "The Tactician" is accountable. Implement metrics to measure execution quality and slippage against the market mid-price at arrival time.

SPECIFIC OBJECTIVES:
1. Implement `SlippageCalculator`: (Avg Fill Price - Arrival Mid Price) / Arrival Mid Price.
2. Create `ExecutionReport` JSON schema for post-trade analysis.
3. Update `API_CONTRACTS.md` to expose these metrics to the frontend.

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update `API_CONTRACTS.md` with new `GET /execution/reports/{id}` endpoint.
    - [ ] Define slippage tolerance thresholds in `SYSTEM_REQUIREMENTS.md` (if missing).
```
