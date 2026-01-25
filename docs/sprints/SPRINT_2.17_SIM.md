# Sprint 2.17 Initialization Manifest (SIM)

**Sprint Period**: February 8, 2026 - February 21, 2026
**Focus**: The Floor - Trading Execution & Risk Management
**Team Composition**: The Dockmaster, The Feature Developer, The UI/UX Agent, The Architect

---

## Sprint Objectives

### Primary Goal
Implement the core Trading Engine with risk management (Stop-loss, Position Sizing) and the "Floor" UI for live execution control, utilizing parallel development worktrees.

### Success Criteria
- [x] Trading Engine Core implemented (Order execution, Position tracking)
- [x] The Floor UI implemented (Real-time P&L, Kill Switch, Trade Confirmation)
- [x] Risk Management system active (Stop-loss monitoring)
- [x] Lab-to-Floor algorithm promotion workflow established
- [ ] Parallel worktrees successfully provisioned and merged

---

## Agent Assignments

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [x] Provisioning: Execute `git worktree` setup for Tracks A, B, and C.
- [x] Initialization: Launch VS Code instances with unique `--user-data-dir`.
- [ ] Synchronization: Periodically rebase Track branches with `main` to prevent drift.
- [ ] Teardown: Clean up worktrees and archive logs upon Track completion.

## Workspace Orchestration (Dockmaster Only)

The Dockmaster Agent must execute the following `git worktree` and environment setups before activating Track A, B, and C.

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-FL-001` | `../sprint-2.17/track-a` | `../sprint-2.17/data/agent-a` | `8001` | `#3771c8` (Blue) |
| **Track B** | `feat/REQ-FL-003` | `../sprint-2.17/track-b` | `../sprint-2.17/data/agent-b` | `3001` | `#2b9e3e` (Green) |
| **Track C** | `feat/IR-FL-001`  | `../sprint-2.17/track-c` | `../sprint-2.17/data/agent-c` | `8002` | `#d15715` (Orange) |

**Provisioning Script Commands:**
- [x] `mkdir -p ../sprint-2.17/data`
- [x] `git worktree add ../sprint-2.17/track-a feat/REQ-FL-001`
- [x] `mkdir -p ../sprint-2.17/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.17/track-a/.vscode/settings.json`
- [x] `code --user-data-dir ../sprint-2.17/data/agent-a --new-window ../sprint-2.17/track-a`
- [x] `git worktree add ../sprint-2.17/track-b feat/REQ-FL-003`
- [x] `mkdir -p ../sprint-2.17/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.17/track-b/.vscode/settings.json`
- [x] `code --user-data-dir ../sprint-2.17/data/agent-b --new-window ../sprint-2.17/track-b`
- [x] `git worktree add ../sprint-2.17/track-c feat/IR-FL-001`
- [x] `mkdir -p ../sprint-2.17/track-c/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#d15715","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.17/track-c/.vscode/settings.json`
- [x] `code --user-data-dir ../sprint-2.17/data/agent-c --new-window ../sprint-2.17/track-c`

### Track A: Trading Engine Core (Frontend Agnostic)

**Agent**: The Feature Developer (Backend Specialist)
**Requirements**: REQ-FL-001, REQ-FL-002
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.17 - Track A: Trading Engine Core
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer (Backend Specialist)

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.17/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path. All relative paths in documentation refer to this worktree root.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: SYSTEM_REQUIREMENTS.md (Section 8: Trading Execution)
    - Tier 1: API_CONTRACTS.md (Trading API Patterns)

  WRITE/UPDATE:
    - Tier 2: backend/app/services/trading/README.md
    - Tier 4: Pydantic models (Order, Position, Trade)

MISSION:
Implement the core Trading Engine service required for placing orders and managing positions.

SPECIFIC OBJECTIVES:
1. Implement Order Execution Service (Market/Limit orders)
2. Implement Position Management (Tracking open trades, P&L calculation)
3. Implement Risk Management (Stop-loss monitoring, Position sizing checks)

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [x] Update backend/app/services/trading/README.md with mermaid class diagram
    - [x] Define Pydantic models for OrderRequest, OrderResponse, Position

  DURING IMPLEMENTATION:
    - [x] Add Field(description="...") for all models
    - [x] Implement checks for "Ghost Mode" (paper trading vs live)

  AFTER IMPLEMENTATION:
    - [x] Write unit tests for Order Execution logic
    - [x] Write integration tests for position updates

SUCCESS CRITERIA:
  - [x] Trading Engine enables opening and closing positions via API
  - [x] Risk Management blocks orders exceeding position limits
  - [x] Unit test coverage > 80%
```

### Track B: The Floor UI (Frontend)

**Agent**: The UI/UX Agent (Frontend Specialist)
**Requirements**: REQ-FL-003, REQ-UX-007 (Real-time)
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.17 - Track B: The Floor UI
PROJECT: Oh My Coins - Trading Platform Frontend
ROLE: The UI/UX Agent (Frontend Specialist)

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.17/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path. All relative paths in documentation refer to this worktree root.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: USER_JOURNEYS.md (Journey 5: Floor Risk Management)
    - Tier 3: TRADING_UI_SPEC.md (The Floor Layout)
    - Tier 3: DESIGN_SYSTEM.md (SafetyButton, LedgerCard)

  WRITE/UPDATE:
    - Tier 2: frontend/src/features/floor/README.md
    - Tier 3: Storybook stories (*.stories.tsx)

MISSION:
Implement "The Floor" dashboard component, integrating SafetyButtons and real-time P&L tickers.

SPECIFIC OBJECTIVES:
1. Build The Floor layout (Grid system for active positions)
2. Integrate SafetyButton for Emergency Stop (Kill Switch)
3. Integrate WebSocket feeds for real-time P&L updates

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update frontend/src/features/floor/README.md with component hierarchy
    - [ ] Review TRADING_UI_SPEC.md

  DURING IMPLEMENTATION:
    - [ ] Use Tailwind utility classes ONLY
    - [ ] Implement "Disconnected" state handling (REQ-FL-DISC-001)

  AFTER IMPLEMENTATION:
    - [ ] Create Storybook stories for Active/Paused/Emergency states
    - [ ] Run accessibility audit (axe-core)

SUCCESS CRITERIA:
  - [x] The Floor renders active positions with real-time updates
  - [x] Kill Switch successfully halts simulated trading
  - [x] Accessibility audit passes (0 violations)
```

### Track C: Lab-to-Floor Promotion (Integration)

**Agent**: The Architect (Orchestrator)
**Requirements**: REQ-INT-004
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.17 - Track C: Lab-to-Floor Promotion
PROJECT: Oh My Coins - System Integration
ROLE: The Architect (Orchestrator)

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.17/track-c
  INSTANCE_PORT: 8002
  STRICT_SCOPE: You are locked to this directory. Do not modify files outside this path.

MISSION:
Define and implement the workflow for promoting a strategy from "The Lab" (Backtesting) to "The Floor" (Live Trading).

SPECIFIC OBJECTIVES:
1. Define the "Strategy Promotion" JSON schema
2. Implement the approval workflow API (requires Architect signature)
3. Update API_CONTRACTS.md with promotion endpoints

SUCCESS CRITERIA:
  - [x] Strategy Promotion schema defined and documented
  - [x] API endpoint for promotion implemented
  - [x] Integration tests verify promotion flow
```

---

## Documentation Gates (Quality Checklist)

All tracks MUST pass these gates before PR approval:

### Gate 1: Requirement Traceability ✅
- [ ] PR title or description references REQ-FL-XXX
- [ ] Worktree Integrity: verified `git branch --show-current` matches assigned track branch within worktree folder

### Gate 2: Tier 2 Documentation ✅
- [ ] Service/Feature README.md updated with architecture diagram

### Gate 3: Tier 4 Auto-Documentation ✅
- [ ] OpenAPI /docs renders correctly

### Gate 4: Test Coverage ✅
- [ ] Unit tests added/updated (>80% coverage)

### Gate 5: Accessibility (Frontend only) ✅
- [ ] axe-core audit passes (0 violations)

---

## Sprint Retrospective Checklist

At sprint end, The Architect validates:

### Environment Cleanup (Dockmaster) ✅
- [ ] All worktrees merged into main
- [ ] `git worktree remove` executed for all sprint tracks
- [ ] user-data-dir caches cleared/archived
