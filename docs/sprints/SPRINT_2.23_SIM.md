# Sprint 2.23 Initialization Manifest (SIM)

**Sprint Period**: May 3, 2026 - May 16, 2026
**Focus**: Risk Management ("The Guard")
**Team Composition**: The Architect, The Feature Developer, The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
Implement "The Guard," a non-negotiable safety layer. No trade shall pass to execution without cryptographic signing and risk validation.

### Success Criteria
- [ ] **RiskCheckMiddleware**: Validates every POST to `/trade/execute`.
- [ ] **Circuit Breaker**: Auto-trips if daily loss > N%.
- [ ] **Audit Trail**: Every risk decision (Pass/Fail) logged to DB.
- [ ] **Onboarding**: Users must define risk limits before API Key entry.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)
**Agent**: The Architect
**Responsibilities**:
- [ ] **Governance**: Enforce that "The Guard" code path cannot be bypassed by Agents.
- [ ] **SIM Validation**: Validate SIM structure.
- [ ] **Review**: Ensure 100% test coverage on Risk logic.

### Track D: The Dockmaster (Orchestration)
**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] **Provisioning**: Setup Tracks A, B, C.
- [ ] **Hygiene**: Enforce new "Teardown Protocol" to prevent zombie containers.

## Workspace Orchestration (Dockmaster Only)

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-SAFE-CORE` | `../sprint-2.23/track-a` | `../sprint-2.23/data/agent-a` | `8001` | `track-a` |
| **Track B** | `feat/REQ-SAFE-UI` | `../sprint-2.23/track-b` | `../sprint-2.23/data/agent-b` | `3001` | `track-b` |
| **Track C** | `feat/REQ-SAFE-AUDIT` | `../sprint-2.23/track-c` | `../sprint-2.23/data/agent-c` | `8002` | `track-c` |

### Track A: Risk Engine Core

**Agent**: The Feature Developer
**Requirements**: [REQ-SAFE-001 (Middleware), REQ-SAFE-002 (Limits)]
**Estimated Effort**: 5 days

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.23 - Track A: Risk Engine
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.23/track-a
  INSTANCE_PORT: 8001
  CONTAINER_PREFIX: track-a

OBJECTIVES:
  1. Implement `RiskCheckMiddleware`.
  2. Hard-code limits: Max Drawdown (5%), Max Position Size (10%).
  3. Ensure Agents CANNOT override these limits.

DELIVERABLES:
  - `RiskCheckMiddleware` Python class.
  - Unit tests covering 100% of risk scenarios.
```

### Track B: UI Control & Onboarding

**Agent**: The UI/UX Agent
**Requirements**: [REQ-UX-SAFE-001 (Onboarding), REQ-UX-SAFE-002 (Kill Switch)]
**Estimated Effort**: 5 days

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.23 - Track B: UI Control
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The UI/UX Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.23/track-b
  INSTANCE_PORT: 3001
  CONTAINER_PREFIX: track-b

OBJECTIVES:
  1. Design "Onboarding Wizard" for setting initial Risk Limits.
  2. Implement big Red "Kill Switch" button on Dashboard.
  3. Visual feedback when trades are blocked by The Guard.

DELIVERABLES:
  - `OnboardingWizard.tsx`
  - `KillSwitch.tsx`
```

### Track C: Audit Logging

**Agent**: The Feature Developer
**Requirements**: [REQ-SAFE-AUDIT-001 (Immutable Logs)]
**Estimated Effort**: 3 days

#### Context Injection Prompt
```markdown
CONTEXT: Sprint 2.23 - Track C: Audit Logging
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.23/track-c
  INSTANCE_PORT: 8002
  CONTAINER_PREFIX: track-c

OBJECTIVES:
  1. Create `AuditLog` table in DB.
  2. Service to log every `TradeAttempt` (inputs, risk_result, timestamp).
  3. Ensure logs are append-only.

DELIVERABLES:
  - `AuditLog` Model & Migration.
  - `AuditService`.
```
