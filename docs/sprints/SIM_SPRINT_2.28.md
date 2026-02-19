# Sprint 2.28 Initialization Manifest (SIM)

**Sprint Period**: Feb 19, 2026 - Feb 28, 2026
**Focus**: Collector Uplift (Plugin Architecture)
**Team Composition**: The Architect, The Protocol Droid (Backend), The UI/UX Agent

---

## Sprint Objectives

### Primary Goal
Revolutionize data collection management by implementing a **Plugin-Based Architecture**. Refactor the collector system to use standardized modules (`ICollector`), typically auto-discovered by a `CollectorRegistry`. This allows Admins to activate, configure, and monitor powerful Python-based strategies via the UI without exposing raw code execution risks.

### Success Criteria
- [ ] **Architecture**: `ICollector` interface defined and enforced for all plugins.
- [ ] **Registry**: `CollectorRegistry` implemented to scan and register valid plugins at startup.
- [ ] **Data Model**: `Collector` table updated to store plugin configuration (JSON) and state.
- [ ] **Plugins**: Ported 3+ reference scrapers (e.g., CoinDesk, Yahoo, CryptoPanic) to the new plugin format.
- [ ] **Frontend**: Dynamic Admin UI forms generated from plugin JSON schemas.
- [ ] **Backend**: Scheduler refactored to execute plugin instances with stored config.

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)
**Agent**: The Architect
**Responsibilities**:
- [ ] **SIM Validation**: Validate that this SIM document strictly follows `docs/sprints/SIM_TEMPLATE.md` structure.
- [ ] **Roadmap Alignment**: Ensure sprint objectives align with `ROADMAP.md` Phase objectives.
- [ ] **Sprint Review**: Conduct final review and update `CURRENT_SPRINT.md` upon completion.

## Workspace Orchestration (Dockmaster Only)

| Track | Branch Name | Worktree Path | VS Code Data Dir | Assigned Port | Color Code | Container Prefix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A** | `feat/REQ-COLL-PLUGIN` | `../omc-track-a` | `../omc-data/agent-a` | `8010` | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/REQ-COLL-UI` | `../omc-track-b` | `../omc-data/agent-b` | `8020` | `#c83737` (Red) | `track-b` |

### Track Objectives

#### **Track A: Backend & Plugin System (Protocol Droid)**
*   **Goal**: robust plugin infrastructure.
*   **Key Files**:
    *   `backend/app/core/collectors/base.py`: Abstract Base Class `ICollector`.
    *   `backend/app/core/collectors/registry.py`: Discovery logic.
    *   `backend/app/collectors/strategies/news_coindesk.py`: Ported scraper.
    *   `backend/app/models/collector.py`: SQLModel for persistent configuration.
*   **Requirements**: `REQ-COLL-ARCH-001` (Interface), `REQ-COLL-EVT-001` (Registration).

#### **Track B: Frontend Dynamic Forms (UI/UX Agent)**
*   **Goal**: Render configuration forms based on plugin schemas.
*   **Key Files**:
    *   `frontend/src/features/admin/CollectorForm.tsx`: Schema-driven form builder.
    *   `frontend/src/features/admin/CollectorDashboard.tsx`: Instance management.
*   **Requirements**: `REQ-COLL-ARCH-002` (Dynamic UI), `REQ-COLL-ST-001` (Health Monitoring).

---

## Testing Strategy
- **Unit**: Mocked plugin execution in `test_registry.py`.
- **Integration**: Verify a new plugin added to the folder appears in the API response.
- **E2E**: `J-COLL-001`: Register & Activate CoinDesk Plugin.

---

**generated-by**: GitHub Copilot
**date**: 2026-02-19
