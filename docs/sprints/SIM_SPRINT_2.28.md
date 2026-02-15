# Sprint 2.28 Initialization Manifest (SIM)

**Sprint Period**: Feb 15, 2026 - Feb 28, 2026
**Focus**: Collector Uplift (Management UI & Logic)
**Team Composition**: The Architect, The Feature Developer, The UI/UX Agent, The Quality Agent

---

## Sprint Objectives

### Primary Goal
Revolutionize data collection management by moving it from code-based configuration to an Admin UI, enabling simpler addition/modification of new data sources and improved operational visibility.

### Success Criteria
- [ ] **Frontend**: Admin UI for Collectors (List, Create/Edit Form, Dashboard) implemented and functional.
- [ ] **Backend**: API endpoints for Collector management (CRUD, active state toggling) exposed and secured.
- [ ] **Logic**: "Web Scraper" collector type supports dynamic selector configuration via UI.
- [ ] **Integration**: New collectors created via UI successfully fetch data and populate the **4 Ledgers**.
- [ ] **Validation**: E2E tests for `J-COLL-001`, `J-COLL-002`, `J-COLL-003` passing.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)
**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.
- [ ] **Test Alignment**: Run the full test suite (`bash scripts/test.sh`) at the end of the sprint to maintain alignment between the test suite and delivered work.

## Workspace Orchestration (Dockmaster Only)

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-COLL-API` | `../omc-track-a` | `../omc-data/agent-a` | `8010` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/REQ-COLL-UI` | `../omc-track-b` | `../omc-data/agent-b` | `8020` | `#c83737` (Red) | `track-b` |

### Track Objectives

#### **Track A: Backend & API (Protocol Droid)**
*   **Goal**: Enable dynamic collector management via API.
*   **Key Files**:
    *   `backend/app/models/collector.py`: New comprehensive DB model.
    *   `backend/app/api/v1/endpoints/collectors.py`: CRUD endpoints.
    *   `backend/app/services/collector_engine.py`: Scheduler logic to respect DB-driven configs.
*   **Requirements**: `REQ-COLL-UBI-001`, `REQ-COLL-EVT-001` to `005`.

#### **Track B: Frontend Admin UI (UI/UX Agent)**
*   **Goal**: Provide a clean, powerful interface for managing collectors.
*   **Key Files**:
    *   `frontend/src/features/admin/CollectorDashboard.tsx`: Health overview.
    *   `frontend/src/features/admin/CollectorForm.tsx`: Creation/Editing wizard.
    *   `frontend/src/components/SelectorBuilder.tsx`: Visual helper for CSS selectors.
*   **Requirements**: `REQ-COLL-OPT-001`, `REQ-COLL-OPT-003`.

---

## Testing Strategy
- **Unit**: 95% coverage on `collector_engine.py` (critical path).
- **Integration**: Verify scheduler picks up database changes (e.g., pause/resume) immediately.
- **E2E**: Implement `J-COLL-001` (Create & Activate) using Playwright.

---

**generated-by**: GitHub Copilot
**date**: 2026-02-15
