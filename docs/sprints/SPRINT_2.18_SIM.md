# Sprint 2.18 Initialization Manifest (SIM)

**Sprint Period**: February 22, 2026 - March 7, 2026
**Focus**: Integrated Trading Loop & UI Polish
**Team Composition**: The Dockmaster, The Feature Developer, The UI/UX Agent, The Architect

---

## Sprint Objectives

### Primary Goal
Complete the end-to-end integration of "The Floor" (Trading UI) with the Trading Engine (Backend) and ensure a polished, production-ready user experience.

### Success Criteria
- [ ] End-to-End Trading Flow operational (UI -> API -> Execution -> WebSocket -> UI)
- [ ] UI Polish applied (Animations, Loading States, Error Handling)
- [ ] Comprehensive Integration Tests covering the full loop
- [ ] Parallel development workflow refined with containerized testing

---

## Operational Adjustments (From Sprint 2.17 Retrospective)

### ⚠️ Testing Protocol Update
To avoid port conflicts and dependency issues observed in Sprint 2.17:
1. **Containerized Testing**: Agents MUST run tests within the Docker container, NOT on the host machine.
   * Command: `docker exec -it <container_name> pytest ...`
2. **Synchronous Testing**: If containerization is not possible, tests requiring shared ports (DB, Redis) must be run sequentially, not in parallel.

---

## Agent Assignments

### Track D: The Dockmaster (Orchestration)
**Responsibilities**:
- Provision worktrees for Tracks A & B.
- Ensure `docker-compose.override.yml` is configured for each track to avoid port contention.

### Track A: Backend Integration
**Focus**: WebSocket feeds for Order/Position updates, robust error handling for trading actions.

### Track B: Frontend Integration
**Focus**: Hooking up `FloorLayout` to real API endpoints, implementing "Optimistic UI" patterns for trading actions.

---

## Workspace Orchestration (Plan)

*   **Track A**: `feat/REQ-INT-005` (Backend Integration)
*   **Track B**: `feat/REQ-UX-008` (Frontend Wiring)
