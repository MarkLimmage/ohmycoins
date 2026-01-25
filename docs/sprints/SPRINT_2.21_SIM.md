# Sprint 2.21 Initialization Manifest (SIM) - The Optimizer

**Sprint Period**: April 5, 2026 - April 18, 2026
**Focus**: Performance Analytics & Strategy Optimization
**Team Composition**: The Architect, The Dockmaster, The Feature Developer (x2), The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
Empower "The Optimizer" to refine strategies through hyperparameter tuning and advanced backtesting with transaction costs. Visualize these insights in a dedicated Performance Dashboard.

### Success Criteria
- [ ] **Optimization Engine**: A service capable of running grid/random search on strategy parameters to maximize Sharpe Ratio.
- [ ] **Realistic Backtesting**: Backtests now account for Trading Fees (0.1%) and Estimated Slippage.
- [ ] **Performance Dashboard**: A new UI view displaying equity curves, drawdown charts, and "Strategy Cards" with performance metrics.
- [ ] **Mobile Monitor**: A responsive, read-only view of the P&L and active positions for mobile devices.

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
| **Track A** | `feat/REQ-OPT-001` | `../sprint-2.21/track-a` | `../sprint-2.21/data/agent-a` | `8001` | `#3771c8` (Blue) |
| **Track B** | `feat/REQ-UX-OPT` | `../sprint-2.21/track-b` | `../sprint-2.21/data/agent-b` | `3001` | `#2b9e3e` (Green) |
| **Track C** | `feat/REQ-OPT-002` | `../sprint-2.21/track-c` | `../sprint-2.21/data/agent-c` | `8002` | `#d15715` (Orange) |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.21/data`
- [ ] `git worktree add ../sprint-2.21/track-a feat/REQ-OPT-001`
- [ ] `mkdir -p ../sprint-2.21/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.21/track-a/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.21/data/agent-a --new-window ../sprint-2.21/track-a`
- [ ] `git worktree add ../sprint-2.21/track-b feat/REQ-UX-OPT`
- [ ] `mkdir -p ../sprint-2.21/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.21/track-b/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.21/data/agent-b --new-window ../sprint-2.21/track-b`
- [ ] `git worktree add ../sprint-2.21/track-c feat/REQ-OPT-002`
- [ ] `mkdir -p ../sprint-2.21/track-c/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#d15715","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.21/track-c/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.21/data/agent-c --new-window ../sprint-2.21/track-c`

### Track A: The Turbo (Optimization Engine)

**Agent**: The Feature Developer (Backend)
**Requirements**: [REQ-OPT-001]
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.21 - Track A: Optimization Engine
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.21/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path. All relative paths in documentation refer to this worktree root.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: SYSTEM_REQUIREMENTS.md
    - Tier 2: backend/app/services/backtesting/README.md
  
  WRITE/UPDATE:
    - Tier 2: backend/app/services/optimization/README.md
    - Tier 4: Pydantic models (OptimizationSchema)

MISSION:
Implement `OptimizationService` that performs grid search or random search over a Strategy's parameters to maximize a target metric (default: Sharpe Ratio).

SPECIFIC OBJECTIVES:
1. Create `OptimizationJob` model to track tuning sessions.
2. Implement `GridSearch` strategy.
3. Integrate with `BacktestService` to run simulations for each parameter set.

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update optimization README.md with class diagram.
    - [ ] Define API endpoints for starting/stopping optimization jobs.
  
  DURING IMPLEMENTATION:
    - [ ] Add Pydantic Field descriptions.

  AFTER IMPLEMENTATION:
    - [ ] Write unit tests.

CONSTRAINTS:
  - **Environment**: NO LOCAL VENVS. Testing must occur within the project's Docker containers (`docker compose run backend pytest`).
  - Use celery for long-running optimization tasks.
  - No direct database access (use CRUD).

SUCCESS CRITERIA:
  - [ ] Can submit a job with { "rsi_period": [10, 14, 20] } and get 3 backtest results.
  - [ ] Optimization results stored in DB.
```

### Track B: The Dashboard (Performance UI)

**Agent**: The UI/UX Agent
**Requirements**: [REQ-UX-OPT]
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.21 - Track B: Performance Dashboard
PROJECT: Oh My Coins - Trading Platform Frontend
ROLE: The UI/UX Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.21/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory.

TIERED ACCESS:
  READ ONLY:
    - Tier 3: DESIGN_SYSTEM.md
  
  WRITE/UPDATE:
    - Tier 2: frontend/src/features/performance/README.md

MISSION:
Implement the Performance Dashboard and ensure the entire platform is mobile-responsive for "On the Go" monitoring.

SPECIFIC OBJECTIVES:
1. Create `EquityCurve` chart using Recharts.
2. Build `StrategyCard` component showing Sharpe, Win Rate, and Drawdown.
3. Implement Responsive Design for Mobile (collapsible sidebar, stacked grids).

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update feature README with component hierarchy.
  
  DURING IMPLEMENTATION:
    - [ ] Follow Tailwind utility classes only.

  AFTER IMPLEMENTATION:
    - [ ] Storybook stories for all new components.

CONSTRAINTS:
  - **Environment**: NO LOCAL INSTALLS. Testing/Building must occur within the project's Docker containers.
  - Use Tailwind utility classes ONLY.
  - Mobile First design approach.

SUCCESS CRITERIA:
  - [ ] Dashboard looks good on 375px width (Mobile).
  - [ ] Charts are responsive.
```

### Track C: The Reality Check (Advanced Backtesting)

**Agent**: The Feature Developer (Data Science)
**Requirements**: [REQ-OPT-002]
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.21 - Track C: Advanced Backtesting
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.21/track-c
  INSTANCE_PORT: 8002
  STRICT_SCOPE: You are locked to this directory.

TIERED ACCESS:
  READ ONLY:
    - Tier 2: backend/app/services/backtesting/README.md
    - Tier 1: SYSTEM_REQUIREMENTS.md
  
  WRITE/UPDATE:
    - Tier 2: backend/app/services/backtesting/engine.py

MISSION:
Upgrade the `BacktestService` to include realistic market friction: Trading Fees and Slippage.

SPECIFIC OBJECTIVES:
1. Update `run_backtest` to accept `fee_rate` (default 0.1%) and `slippage` (default 0.05%).
2. Update P&L calculations to deduct fees per trade.
3. Verify impact on Sharpe Ratio calculations.

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update backtesting README with new formula details.
  
  DURING IMPLEMENTATION:
    - [ ] Ensure vectorized operations are maintained for speed.

  AFTER IMPLEMENTATION:
    - [ ] Verify calculation against a manual Excel/Sheets check.

CONSTRAINTS:
  - **Environment**: NO LOCAL VENVS. Testing must occur within the project's Docker containers.
  - Performance: Backtest must still run < 1s for < 1000 candles.

SUCCESS CRITERIA:
  - [ ] A winning strategy becomes a losing strategy when 1% fees are applied (sanity check).
```
