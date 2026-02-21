# Sprint 2.22 Initialization Manifest (SIM)

**Sprint Period**: April 19, 2026 - May 2, 2026
**Focus**: Infrastructure & Deployment ("Operation Green Light")
**Team Composition**: The Architect, The DevOps Agent, The Feature Developer

---

## Sprint Objectives

### Primary Goal
Validate critical infrastructure to establish a functional Staging environment accessible via URL, enabling the "Closed Beta" phase.

### Success Criteria
- [ ] **Infrastructure Validated**: Terraform `apply` succeeds for Staging environment (ECS, RDS, Redis).
- [ ] **Deployment Automated**: GitHub Actions pipeline deploys to Staging on merge to `main`.
- [ ] **Access Secured**: Frontend/Backend accessible only to whitelisted IPs or Users (Basic Auth or App Level).
- [ ] **DNS/SSL Live**: `staging.ohmycoins.io` resolves with valid SSL certificate.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase 6 objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.
- [ ] **Test Alignment**: Run the full test suite (`bash scripts/test.sh`) at the end of the sprint.
- [ ] **Merge Safety**: Verify that all transient environment changes have been reverted in PRs before merging.
- [ ] **Next Sprint Planning**: Create the SIM for Sprint 2.23 (The Guard).

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] Provisioning: Execute `git worktree` setup for Tracks A, B, and C.
- [ ] Initialization: Launch VS Code instances.
- [ ] Synchronization: Periodically rebase Track branches.
- [ ] Teardown: Clean up worktrees and archive logs.

## Workspace Orchestration (Dockmaster Only)

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/INFRA-AWS-STAGING` | `../sprint-2.22/track-a` | `../sprint-2.22/data/agent-a` | `8001` | `#3771c8` (Blue) |
| **Track B** | `feat/CICD-PIPELINE` | `../sprint-2.22/track-b` | `../sprint-2.22/data/agent-b` | `3001` | `#2b9e3e` (Green) |
| **Track C** | `feat/REQ-SEC-WHITELIST` | `../sprint-2.22/track-c` | `../sprint-2.22/data/agent-c` | `8002` | `#d15715` (Orange) |

**Provisioning Script Commands:**
- [ ] `mkdir -p ../sprint-2.22/data`
- [ ] `git worktree add ../sprint-2.22/track-a feat/INFRA-AWS-STAGING`
- [ ] `mkdir -p ../sprint-2.22/track-a/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#3771c8","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.22/track-a/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.22/data/agent-a --new-window ../sprint-2.22/track-a`
- [ ] `git worktree add ../sprint-2.22/track-b feat/CICD-PIPELINE`
- [ ] `mkdir -p ../sprint-2.22/track-b/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#2b9e3e","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.22/track-b/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.22/data/agent-b --new-window ../sprint-2.22/track-b`
- [ ] `git worktree add ../sprint-2.22/track-c feat/REQ-SEC-WHITELIST`
- [ ] `mkdir -p ../sprint-2.22/track-c/.vscode && echo '{"workbench.colorCustomizations":{"titleBar.activeBackground":"#d15715","titleBar.activeForeground":"#ffffff"}}' > ../sprint-2.22/track-c/.vscode/settings.json`
- [ ] `code --user-data-dir ../sprint-2.22/data/agent-c --new-window ../sprint-2.22/track-c`

### Track A: Infrastructure Validation

**Agent**: The DevOps Agent
**Requirements**: [INFRA-001 (Terraform Validation), INFRA-002 (RDS Connectivity)]
**Estimated Effort**: 5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.22 - Track A: Infrastructure Validation
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The DevOps Agent

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.22/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Focus on `infrastructure/terraform` and `docs/DEPLOYMENT_STATUS.md`.

OBJECTIVES:
  1. Audit `infrastructure/terraform` modules for Staging configuration.
  2. Create a "Dry Run" report for `terraform plan`.
  3. Validate AWS Secrets Manager integration for Staging.
  4. Update `docs/DEPLOYMENT_STATUS.md` with real-time status.

DELIVERABLES:
  - Validated Terraform configuration.
  - Successful `terraform plan` output log.
  - Updated Deployment Status doc.
```

### Track B: CI/CD Pipeline

**Agent**: The Feature Developer
**Requirements**: [CICD-001 (Build/Push), CICD-002 (Deploy to ECS)]
**Estimated Effort**: 4 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.22 - Track B: CI/CD Pipeline
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.22/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory. Focus on `.github/workflows` and `scripts/deploy.sh`.

OBJECTIVES:
  1. Refine `build-push.sh` and `deploy.sh` for reliability.
  2. Implement GitHub Action `deploy-staging.yml`.
  3. Ensure zero-downtime deployment Config (Rolling Update).

DELIVERABLES:
  - `.github/workflows/deploy-staging.yml`
  - Verified `scripts/deploy.sh`
```

### Track C: Access Control (Whitelist)

**Agent**: The Feature Developer
**Requirements**: [REQ-SEC-001 (Closed Beta Whitelist)]
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.22 - Track C: Access Control
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The Feature Developer

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.22/track-c
  INSTANCE_PORT: 8002
  STRICT_SCOPE: You are locked to this directory. Focus on `backend/app/core/security.py` and `middleware`.

OBJECTIVES:
  1. Implement a Middleware or Dependency to check User Email against a Whitelist.
  2. Define the Whitelist format (Env Var or DB Table).
  3. Ensure "Access Denied" page is shown to non-whitelisted users.

DELIVERABLES:
  - `WhitelistMiddleware` or Dependency.
  - Tests ensuring unauthorized users are blocked.
```
