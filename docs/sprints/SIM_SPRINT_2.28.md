# Sprint 2.28 Initialization Manifest (SIM)

**Sprint Period**: Feb 15, 2026 - Feb 28, 2026
**Focus**: Collector Uplift (Management UI & Logic)
**Team Composition**: The Architect, The Feature Developer, The UI/UX Agent, The Quality Agent

---

## Sprint Objectives

### Primary Goal
Revolutionize data collection management by implementing a **Plugin-Based Architecture**. Refactor existing scripts into standardized modules and create a `CollectorRegistry` for auto-discovery, allowing admins to configure powerful, pre-built strategies via the UI.

### Success Criteria
- [ ] **Architecture**: `ICollector` interface defined and enforced for all plugins.
- [ ] **Registry**: `CollectorRegistry` implemented to scan and register valid plugins at startup.
- [ ] **Plugins**: Ported 3+ reference scrapers (e.g., CoinDesk, Yahoo) to the new plugin format.
- [ ] **Frontend**: Dynamic configuration forms generated from plugin JSON schemas.
- [ ] **Backend**: Scheduler refactored to execute plugin instances with stored config.

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
| **Track A** | `feat/REQ-COLL-PLUGIN` | `../omc-track-a` | `../omc-data/agent-a` | `8010` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/REQ-COLL-UI` | `../omc-track-b` | `../omc-data/agent-b` | `8020` | `#c83737` (Red) | `track-b` |

### Track Objectives

#### **Track A: Backend & Plugin System (Protocol Droid)**
*   **Goal**: robust plugin infrastructure.
*   **Key Files**:
    *   `backend/app/core/collectors/base.py`: Abstract Base Class.
    *   `backend/app/core/collectors/registry.py`: Discovery logic.
    *   `backend/app/collectors/strategies/news_coindesk.py`: Ported scraper.
*   **Requirements**: `REQ-COLL-PLUG-001`, `REQ-COLL-PLUG-002`.

#### **Track B: Frontend Dynamic Forms (UI/UX Agent)**
*   **Goal**: Render configuration forms based on plugin schemas.
*   **Key Files**:
    *   `frontend/src/features/admin/CollectorForm.tsx`: Schema-driven form builder.
    *   `frontend/src/features/admin/CollectorDashboard.tsx`: Instance management.
*   **Requirements**: `REQ-COLL-PLUG-003`, `REQ-COLL-OPT-003`.

---

## Testing Strategy
- **Unit**: Mocked plugin execution in `test_registry.py`.
- **Integration**: Verify a new plugin added to the folder appears in the API response.


---

**generated-by**: GitHub Copilot
**date**: 2026-02-15
