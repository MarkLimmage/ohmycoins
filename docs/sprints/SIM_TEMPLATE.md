# Sprint X.XX Initialization Manifest (SIM)

**Sprint Period**: [Start Date] - [End Date]  
**Focus**: [Primary Goal - e.g., "BYOM Agent Integration" or "4 Ledgers UI Implementation"]  
**Team Composition**: [List of Agent Personas involved]

---

## Sprint Objectives

### Primary Goal
[1-2 sentence description of the sprint's main objective]

### Success Criteria
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [Measurable outcome 3]

---

## Agent Assignments

### Track D: The Dockmaster (Orchestration)

**Agent**: The Infrastructure/DevOps Agent
**Responsibilities**:
- [ ] Provisioning: Execute `git worktree` setup for Tracks A, B, and C.
- [ ] Initialization: Launch VS Code instances with unique `--user-data-dir`.
- [ ] Synchronization: Periodically rebase Track branches with `main` to prevent drift.
- [ ] Teardown: Clean up worktrees and archive logs upon Track completion.

## Workspace Orchestration (Dockmaster Only)

The Dockmaster Agent must execute the following `git worktree` and environment setups before activating Track A, B, and C.

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port |
| :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-XX-001` | `./worktrees/track-a` | `./.vscode/agent-a-data` | `8001` |
| **Track B** | `feat/REQ-UX-XXX` | `./worktrees/track-b` | `./.vscode/agent-b-data` | `3001` |
| **Track C** | `feat/IR-XX-YYY`  | `./worktrees/track-c` | `./.vscode/agent-c-data` | `8002` |

**Provisioning Script Commands:**
- [ ] `git worktree add ./worktrees/track-a feat/REQ-XX-001`
- [ ] `code --user-data-dir ./.vscode/agent-a-data ./worktrees/track-a`
- [ ] `git worktree add ./worktrees/track-b feat/REQ-UX-XXX`
- [ ] `code --user-data-dir ./.vscode/agent-b-data ./worktrees/track-b`

### Track A: [Feature Name]

**Agent**: The [Architect | Feature Developer | UI/UX Agent | Quality Agent]  
**Requirements**: [REQ-XX-001, REQ-XX-002, ...]  
**Estimated Effort**: [X days]

#### Context Injection Prompt

```markdown
CONTEXT: Sprint X.XX - Track A: [Feature Name]
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: The [Agent Persona Name]

WORKSPACE ANCHOR:
  ROOT_PATH: ./worktrees/track-a
  INSTANCE_PORT: 8001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path. All relative paths in documentation refer to this worktree root.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: SYSTEM_REQUIREMENTS.md (Section X)
    - Tier 1: USER_JOURNEYS.md (Journey X)
    - Tier 1: API_CONTRACTS.md (Global Patterns, Feature Patterns)
    - [Additional docs as needed]
  
  WRITE/UPDATE:
    - Tier 2: backend/app/services/[service]/README.md
    - Tier 4: Pydantic models (OpenAPI schemas)
    - [Additional docs as authorized]

MISSION:
Implement [Feature Name] per requirement REQ-XX-001.

SPECIFIC OBJECTIVES:
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update service/feature README.md with architecture diagram (Mermaid)
    - [ ] Document data flow and integration points
    - [ ] Link to USER_JOURNEYS.md (if applicable)
  
  DURING IMPLEMENTATION:
    - [ ] Add Pydantic Field(description="...") for all new models
    - [ ] Follow API_CONTRACTS.md error handling patterns
    - [ ] Maintain EARS syntax for any requirement additions
  
  AFTER IMPLEMENTATION:
    - [ ] Write unit tests (pytest/vitest)
    - [ ] Write integration tests (if API changes)
    - [ ] Update OpenAPI docs (/docs endpoint)

CONSTRAINTS:
  - Use EARS syntax for any new requirements (Ubiquitous, Event-driven, State-driven, Optional, Unwanted)
  - Follow API_CONTRACTS.md patterns for:
    - Authentication (JWT token handling)
    - Error handling (4xx/5xx → user messages)
    - Loading states (skeleton screens, spinners)
    - WebSocket lifecycle (if applicable)
  - Performance targets:
    - NFR-P-XXX: [specific performance requirement]
  - Security requirements:
    - NFR-S-XXX: [specific security requirement]
  - No direct database access (use SQLAlchemy ORM only)
  - No hardcoded secrets (use EncryptionService)

SUCCESS CRITERIA:
  - [ ] All unit tests pass (pytest -v)
  - [ ] OpenAPI docs auto-generated (http://localhost:8000/docs)
  - [ ] README.md documents implementation logic with Mermaid diagram
  - [ ] Code follows project style guide (black, ruff)
  - [ ] No new security vulnerabilities (safety audit passes)

BRANCH: feat/REQ-XX-YYY-[short-description]
COMMIT PATTERN:
  1. docs: Add architecture for REQ-XX-YYY
  2. feat([module]): Implement REQ-XX-YYY [feature name]
  3. test([module]): Add tests for REQ-XX-YYY
```

#### Deliverables

1. **Documentation** (Tier 2)
   - `backend/app/services/[service]/README.md` with:
     - Architecture overview
     - Data flow diagram (Mermaid)
     - Integration points
     - API endpoints summary
   
2. **Implementation** (Code)
   - `backend/app/services/[service]/[module].py`
   - Pydantic models with Field descriptions
   - Unit tests: `tests/unit/services/[service]/test_[module].py`
   - Integration tests: `tests/integration/[service]/test_[module].py`

3. **Validation** (Tests)
   - Unit test coverage: > 80%
   - All tests passing
   - OpenAPI schema validated

---

### Track B: [UI Feature Name]

**Agent**: The UI/UX Agent (Frontend Specialist)  
**Requirements**: [REQ-UX-XXX, REQ-XX-YYY]  
**Estimated Effort**: [X days]

#### Context Injection Prompt

```markdown
CONTEXT: Sprint X.XX - Track B: [UI Feature Name]
PROJECT: Oh My Coins - Trading Platform Frontend
ROLE: The UI/UX Agent (Frontend Specialist)

WORKSPACE ANCHOR:
  ROOT_PATH: ./worktrees/track-b
  INSTANCE_PORT: 3001
  STRICT_SCOPE: You are locked to this directory. Do not attempt to modify files outside of this path. All relative paths in documentation refer to this worktree root.

TIERED ACCESS:
  READ ONLY:
    - Tier 1: USER_JOURNEYS.md (Journey X: [relevant journey])
    - Tier 1: API_CONTRACTS.md (Feature Patterns, Error Handling)
    - Tier 3: DESIGN_SYSTEM.md (Component Library)
    - Tier 3: DATA_VISUALIZATION_SPEC.md (Chart specs)
    - Tier 3: TRADING_UI_SPEC.md (Floor controls)
  
  WRITE/UPDATE:
    - Tier 2: frontend/src/features/[feature]/README.md
    - Tier 3: Storybook stories (.stories.tsx files)

MISSION:
Implement [Component Name] per DESIGN_SYSTEM.md Section X and REQ-UX-XXX.

SPECIFIC OBJECTIVES:
1. [Objective 1 - e.g., Build LedgerCard component with 4 variants]
2. [Objective 2 - e.g., Implement loading/error/success states]
3. [Objective 3 - e.g., Add accessibility features per REQ-UX-001]

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Update feature README.md with component architecture
    - [ ] Document props, states, and variants
    - [ ] Link to DESIGN_SYSTEM.md specification
  
  DURING IMPLEMENTATION:
    - [ ] Follow Tailwind utility classes only (no custom CSS)
    - [ ] Implement all states per DESIGN_SYSTEM.md (Loading, Error, Empty, Success)
    - [ ] Follow API_CONTRACTS.md for API integration patterns
  
  AFTER IMPLEMENTATION:
    - [ ] Create Storybook story with all component states
    - [ ] Write Playwright E2E test
    - [ ] Run accessibility audit (axe-core)

CONSTRAINTS:
  - Use Tailwind utility classes ONLY (no custom CSS unless approved)
  - Implement REQ-UX-001: Chart table view toggle for accessibility
  - WCAG 2.1 AA compliance:
    - ARIA labels on all interactive elements
    - Keyboard navigation (Tab, Enter, Esc)
    - Focus indicators visible (2px outline, 3:1 contrast)
  - Follow API_CONTRACTS.md patterns:
    - Loading states: Skeleton screens for data-heavy components
    - Error states: Inline error messages with retry button
    - Success states: Auto-update with last-update timestamp
  - Follow DESIGN_SYSTEM.md color palette:
    - Glass: Blue (#3b82f6)
    - Human: Green (#10b981)
    - Catalyst: Amber (#f59e0b)
    - Exchange: Purple (#a855f7)
  - Performance targets:
    - Chart render time: < 100ms (NFR-UX-P-003)
    - UI update latency: < 500ms (NFR-UX-P-001)

SUCCESS CRITERIA:
  - [ ] Storybook story renders all states (Loading, Error, Empty, Success, Interactive)
  - [ ] Playwright E2E test passes (USER_JOURNEYS.md Journey X validated)
  - [ ] Accessibility audit passes (axe-core, 0 violations)
  - [ ] Component matches DESIGN_SYSTEM.md specification exactly
  - [ ] Code follows style guide (prettier, biome)

BRANCH: feat/REQ-UX-XXX-[component-name]
COMMIT PATTERN:
  1. docs: Add component spec for [Component Name]
  2. feat(ui): Implement [Component Name] per DESIGN_SYSTEM
  3. test(ui): Add E2E tests for [Component Name]
  4. docs(storybook): Add [Component Name] stories
```

#### Deliverables

1. **Documentation** (Tier 2)
   - `frontend/src/features/[feature]/README.md` with:
     - Component architecture
     - Props interface documentation
     - Usage examples
     - Integration with API

2. **Implementation** (Code)
   - `frontend/src/features/[feature]/components/[Component].tsx`
   - Component tests: `frontend/src/features/[feature]/components/[Component].test.tsx`
   - E2E tests: `frontend/tests/e2e/[feature]/[component].spec.ts`

3. **Validation** (Tests & Storybook)
   - Storybook story: `[Component].stories.tsx`
   - Accessibility audit report
   - Playwright E2E test passing

---

### Track C: [Integration/Infrastructure Task]

**Agent**: The Architect (Orchestrator)  
**Requirements**: [IR-XX-YYY, NFR-XX-YYY]  
**Estimated Effort**: [X days]

#### Context Injection Prompt

```markdown
CONTEXT: Sprint X.XX - Track C: [Integration Task]
PROJECT: Oh My Coins - System Integration
ROLE: The Architect (System Orchestrator)

TIERED ACCESS:
  READ ONLY:
    - Tier 1: All (SYSTEM_REQUIREMENTS.md, USER_JOURNEYS.md, API_CONTRACTS.md, ARCHITECTURE.md)
  
  WRITE/UPDATE:
    - Tier 1: SYSTEM_REQUIREMENTS.md (Section additions, cross-module requirements)
    - Tier 1: API_CONTRACTS.md (new patterns)
    - Tier 2: Service README.md files (integration points)

MISSION:
[Integration task description]

SPECIFIC OBJECTIVES:
1. [Cross-module integration objective]
2. [Documentation consolidation objective]
3. [Validation objective]

DOC-GATE REQUIREMENTS:
  - [ ] Update SYSTEM_REQUIREMENTS.md Section 10 (Cross-Module Integration)
  - [ ] Update API_CONTRACTS.md with new integration patterns
  - [ ] Update service README.md files with integration diagrams
  - [ ] Validate no documentation drift between Tier 1 and Tier 2

CONSTRAINTS:
  - Maintain 4-tier documentation model
  - Use EARS syntax for new requirements
  - Validate all cross-references between documents
  - Ensure backward compatibility

SUCCESS CRITERIA:
  - [ ] Integration requirements documented in SYSTEM_REQUIREMENTS.md
  - [ ] API patterns documented in API_CONTRACTS.md
  - [ ] All service README.md files updated
  - [ ] No broken links in documentation
  - [ ] validate_requirement_ids.py passes

BRANCH: feat/IR-XX-YYY-[integration-task]
```

---

## Documentation Gates (Quality Checklist)

All tracks MUST pass these gates before PR approval:

### Gate 1: Requirement Traceability ✅
- [ ] PR title or description references REQ-XX-YYY
- [ ] Requirement exists in SYSTEM_REQUIREMENTS.md
- [ ] Requirement linked to USER_JOURNEYS.md (if workflow-related)
- [ ] Worktree Integrity: verified `git branch --show-current` matches assigned track branch within worktree folder

### Gate 2: Tier 2 Documentation ✅
- [ ] Service/Feature README.md updated (if code changed in that folder)
- [ ] Architecture diagram added/updated (Mermaid.js)
- [ ] Integration points documented

### Gate 3: Tier 4 Auto-Documentation ✅
- [ ] Pydantic models have Field(description="...") for new fields
- [ ] OpenAPI /docs renders correctly (http://localhost:8000/docs)

### Gate 4: Test Coverage ✅
- [ ] Unit tests added/updated (pytest or vitest)
- [ ] Integration tests added (if API changes)
- [ ] E2E tests added (if USER_JOURNEYS.md workflow changed)

### Gate 5: Accessibility (Frontend only) ✅
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation tested (Tab, Enter, Esc)
- [ ] REQ-UX-001 table view toggle implemented (if chart component)
- [ ] axe-core audit passes (0 violations)

---

## Sprint Retrospective Checklist

At sprint end, The Architect validates:

### Documentation Sync ✅
- [ ] All Tier 1 docs (SRS, USER_JOURNEYS, API_CONTRACTS) reflect implemented features
- [ ] All Tier 2 README.md files are up-to-date
- [ ] All Tier 3 Storybook stories deployed (http://localhost:6006)
- [ ] All Tier 4 OpenAPI docs generated (http://localhost:8000/docs)
- [ ] No orphaned documentation (files not updated in >3 months)

### Requirement Validation ✅
- [ ] All implemented requirements have tests
- [ ] All requirements link to USER_JOURNEYS.md
- [ ] No undefined requirement references (validate_requirement_ids.py passes)

### Archive Obsolete Docs ✅
- [ ] Sprint completion docs moved to `/docs/archive/history/sprints/sprint-X.XX/`
- [ ] Obsolete implementation details moved to `/docs/archive/YYYY-MM/`
- [ ] Archive README.md updated with rationale

### Environment Cleanup (Dockmaster) ✅
- [ ] All worktrees merged into main
- [ ] `git worktree remove` executed for all sprint tracks
- [ ] user-data-dir caches cleared/archived

---

## Sprint Metrics

Track these metrics for continuous improvement:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| PRs with Doc Updates | 100% | - | 🟡 |
| Test Coverage | > 80% | - | 🟡 |
| Documentation Drift Incidents | 0 | - | 🟡 |
| E2E Tests Passing | 100% | - | 🟡 |
| Accessibility Violations | 0 | - | 🟡 |
| Broken Doc Links | 0 | - | 🟡 |

---

## Next Sprint Planning

**Complete during sprint retrospective (1-2 days before sprint end)**

### Sprint X.XX+1 Preparation

#### 1. Review Current Sprint Outcomes
- [ ] All success criteria met?
- [ ] Any carryover work? (Document in "Sprint X.XX+1 Objectives" below)
- [ ] Learnings that impact next sprint scope?

#### 2. Validate Phase Roadmap Alignment
- [ ] Current phase timeline still accurate? (See [ROADMAP.md](../../ROADMAP.md))
- [ ] Dependencies from current sprint resolved?
- [ ] Any blockers identified for next sprint?

#### 3. Define Next Sprint Scope

**Proposed Sprint X.XX+1 Focus**: [1-sentence description]

**Requirements to Implement**:
- [ ] REQ-XX-YYY: [Requirement name] - [Priority: High/Medium/Low]
- [ ] REQ-XX-YYY: [Requirement name] - [Priority: High/Medium/Low]
- [ ] REQ-XX-YYY: [Requirement name] - [Priority: High/Medium/Low]

**Track Assignments** (preliminary):
- **Track A**: [Feature/Module] - Agent: [Persona]
- **Track B**: [Feature/Module] - Agent: [Persona]
- **Track C**: [Integration/Infrastructure] - Agent: [Persona]

**Estimated Duration**: [X days]

#### 4. Create Next Sprint SIM
- [ ] Copy this template to `SPRINT_X.XX+1_SIM.md`
- [ ] Fill in objectives, requirements, and agent assignments
- [ ] Define context injection prompts for each track
- [ ] Set documentation gate requirements
- [ ] Update CURRENT_SPRINT.md to point to new sprint

#### 5. Risk Assessment
Identify risks for next sprint:

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation strategy] |
| [Risk description] | Low/Med/High | Low/Med/High | [Mitigation strategy] |

#### 6. Planning Notes
[Free-form notes about next sprint planning, technical decisions, or scope adjustments]

---

**Next Sprint Status**: 🟡 PLANNING / 🟢 READY TO START  
**Planning Completed By**: [Agent Persona/Tech Lead]  
**Planning Date**: [Date]

---

**Sprint Status**: 🟡 IN PROGRESS / 🟢 COMPLETE / 🔴 BLOCKED  
**Created By**: [Agent Persona]  
**Approved By**: Tech Lead  
**Related Docs**: DOCS_GOVERNANCE.md, DOCUMENTATION_STRATEGY.md
