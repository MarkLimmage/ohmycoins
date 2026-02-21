# Sprint 2.15 Initialization Manifest (SIM)

**Sprint Period**: January 27, 2026 - January 31, 2026  
**Focus**: Component Library Implementation & Storybook Foundation  
**Team Composition**: The UI/UX Agent, The Feature Developer, The Architect, The Quality Agent  
**Phase**: Phase 3 - UI/UX Foundation (Sprint 2 of 3)

---

## Sprint Objectives

### Primary Goal
Implement core UI component library with Storybook documentation, establishing the foundation for 4 Ledgers dashboard development. Pilot AI agent governance system with documentation gates.

### Success Criteria
- [x] 3 core components implemented (LedgerCard, AgentTerminal, SafetyButton)
- [x] Storybook deployed with component stories for all states
- [x] Accessibility features implemented (WCAG 2.1 AA, REQ-UX-001 table view toggles)
- [x] Documentation gates validated via automated checks
- [x] Component specifications match DESIGN_SYSTEM.md exactly

---

## Sprint Context: Sprint 2.14 Retrospective Summary

### Outcomes from Sprint 2.14 ✅
- ✅ Documentation uplift complete (~7,000 lines across 11 files)
- ✅ 4-tier documentation architecture operational
- ✅ AI agent governance system implemented (4 personas, SIM template, automation)
- ✅ UI/UX specifications created (DESIGN_SYSTEM.md, DATA_VISUALIZATION_SPEC.md, TRADING_UI_SPEC.md)
- ✅ Strategic roadmap restructured (ROADMAP.md v3.0)

### Learnings & Carryover
- **Learning 1**: Documentation-first approach requires upfront investment but prevents downstream confusion
- **Learning 2**: Component specifications need exact TypeScript interfaces for frontend implementation
- **Learning 3**: Accessibility requirements (REQ-UX-001) must be baked into components from start, not retrofitted
- **Carryover Work**: None - Sprint 2.14 fully complete

### Dependencies Resolved
- ✅ DESIGN_SYSTEM.md provides complete component specifications
- ✅ USER_JOURNEYS.md links components to user workflows
- ✅ API_CONTRACTS.md defines frontend-backend interaction patterns
- ✅ Doc-Sync Check automation ready for validation

---

## Agent Assignments

### Track A: Backend Support for Frontend Components

**Agent**: The Feature Developer (Backend Specialist)  
**Requirements**: REQ-UX-002, REQ-UX-003, API-001  
**Estimated Effort**: 1.5 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.15 - Track A: Backend API Support for UI Components
PROJECT: Oh My Coins - Backend API Enhancements
ROLE: The Feature Developer (Backend Specialist)

TIERED ACCESS:
  READ ONLY:
    - Tier 1: SYSTEM_REQUIREMENTS.md (Section 9: UI/UX NFRs)
    - Tier 1: USER_JOURNEYS.md (All journeys for API touchpoint validation)
    - Tier 1: API_CONTRACTS.md (Global Patterns, Error Handling)
  
  WRITE/UPDATE:
    - Tier 2: backend/app/api/routes/[module].py (if new endpoints needed)
    - Tier 4: Pydantic models (add Field descriptions for OpenAPI)

MISSION:
Ensure backend APIs support frontend component requirements per REQ-UX-002 
(skeleton data for loading states) and REQ-UX-003 (error state metadata).

SPECIFIC OBJECTIVES:
1. Validate all API endpoints return proper loading state indicators (data availability flags)
2. Enhance error responses with user-facing messages per API_CONTRACTS.md
3. Add OpenAPI Field descriptions for all response models used by UI components
4. Implement mock data endpoints for Storybook development (dev environment only)

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [ ] Review API_CONTRACTS.md Global Patterns (Loading, Error, Success states)
    - [ ] Document new endpoints in service README.md (if applicable)
  
  DURING IMPLEMENTATION:
    - [ ] Add Pydantic Field(description="...") for all response model fields
    - [ ] Follow API_CONTRACTS.md error handling patterns (4xx/5xx → user messages)
    - [ ] Ensure loading state support (e.g., `is_loading: bool`, `last_updated: datetime`)
  
  AFTER IMPLEMENTATION:
    - [ ] Write unit tests for new/modified endpoints
    - [ ] Validate OpenAPI docs render correctly (http://localhost:8000/docs)
    - [ ] Test with frontend mock data (Postman/Thunder Client)

CONSTRAINTS:
  - Follow API_CONTRACTS.md patterns:
    - Error responses include `message` (user-facing), `detail` (technical), `error_code` (string)
    - Loading responses include `is_loading`, `last_updated`, `data_staleness_seconds`
    - Success responses include data + metadata (`total_count`, `page`, etc.)
  - Performance targets:
    - NFR-UX-P-001: API response time < 500ms for UI data endpoints
  - Security requirements:
    - NFR-S-001: JWT authentication on all endpoints except /health
  - Mock endpoints MUST be disabled in production (environment check)

SUCCESS CRITERIA:
  - [ ] All API endpoints support component loading/error/success states
  - [ ] OpenAPI /docs shows Field descriptions for all UI-consumed models
  - [ ] Mock data endpoints available at /api/v1/mock/* (dev only)
  - [ ] All unit tests pass (pytest -v)
  - [ ] No new security vulnerabilities (safety audit passes)

BRANCH: feat/REQ-UX-002-api-component-support
COMMIT PATTERN:
  1. docs: Document API requirements for UI component support
  2. feat(api): Add loading/error metadata to response models
  3. feat(api): Implement mock data endpoints for Storybook
  4. test(api): Add tests for UI component API support
```

#### Deliverables

1. **Documentation** (Tier 2)
   - `backend/app/api/routes/README.md` (if new patterns added)
   - OpenAPI Field descriptions for all response models
   
2. **Implementation** (Code)
   - Enhanced error responses with user-facing messages
   - Loading state metadata in API responses
   - Mock data endpoints: `/api/v1/mock/ledgers/*` (dev only)
   - Unit tests: `tests/unit/api/test_ui_support.py`

3. **Validation** (Tests)
   - Unit test coverage: > 80%
   - OpenAPI schema validated with Field descriptions
   - Mock endpoints tested in dev environment

---

### Track B: Core Component Library Implementation

**Agent**: The UI/UX Agent (Frontend Specialist)  
**Requirements**: REQ-UX-001, REQ-UX-004, REQ-UX-005  
**Estimated Effort**: 3 days

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.15 - Track B: Core Component Library (LedgerCard, AgentTerminal, SafetyButton)
PROJECT: Oh My Coins - Frontend Component Library
ROLE: The UI/UX Agent (Frontend Specialist)

TIERED ACCESS:
  READ ONLY:
    - Tier 1: USER_JOURNEYS.md (Journey 1: Discovery Flow, Journey 5: Floor Risk Management)
    - Tier 1: API_CONTRACTS.md (Loading, Error, Success patterns)
    - Tier 3: DESIGN_SYSTEM.md (Section 2: Component Library - complete spec)
    - Tier 3: DATA_VISUALIZATION_SPEC.md (Chart specifications per ledger)
    - Tier 3: TRADING_UI_SPEC.md (SafetyButton spec)
  
  WRITE/UPDATE:
    - Tier 2: frontend/src/components/README.md
    - Tier 3: Storybook stories (*.stories.tsx)
    - Tier 3: Component documentation (inline JSDoc)

MISSION:
Implement LedgerCard, AgentTerminal, and SafetyButton components per DESIGN_SYSTEM.md 
specifications with full accessibility support (WCAG 2.1 AA, REQ-UX-001).

SPECIFIC OBJECTIVES:
1. Build LedgerCard component with 4 variants (Glass, Human, Catalyst, Exchange)
   - Implement all states: Loading (skeleton), Error (retry), Empty (no data), Live (auto-update)
   - Add REQ-UX-001: Table view toggle for accessibility
   
2. Build AgentTerminal component for streaming agent logs
   - Implement virtual scrolling (react-window for performance)
   - Add syntax highlighting (react-syntax-highlighter)
   - Support ANSI colors, copy transcript, search functionality
   
3. Build SafetyButton component (3 variants: KillSwitch, ConfirmTrade, EmergencyStop)
   - Implement typed confirmation flow ("STOP" input)
   - Add 5-second cooldown, audit logging
   - Include disabled state and loading spinner

DOC-GATE REQUIREMENTS:
  BEFORE CODE IMPLEMENTATION:
    - [x] Update frontend/src/components/README.md with component architecture
    - [x] Document props interfaces with JSDoc comments
    - [x] Review DESIGN_SYSTEM.md Section 2 for exact specifications
  
  DURING IMPLEMENTATION:
    - [x] Use Tailwind utility classes ONLY (no custom CSS)
    - [x] Implement all states per DESIGN_SYSTEM.md (Loading, Error, Empty, Live)
    - [x] Follow API_CONTRACTS.md for API integration (error handling, loading states)
    - [x] Add ARIA labels, keyboard navigation (Tab, Enter, Esc)
  
  AFTER IMPLEMENTATION:
    - [x] Create Storybook story for each component with ALL states
    - [x] Write component unit tests (vitest)
    - [x] Run accessibility audit (axe-core via Storybook addon)
    - [x] Verify against DESIGN_SYSTEM.md checklist

CONSTRAINTS:
  - Use Tailwind utility classes ONLY (no custom CSS unless approved)
  - Implement REQ-UX-001: ALL components with data visualization MUST have table view toggle
    - LedgerCard: Toggle between chart and data table
    - Keyboard shortcut: Ctrl+Shift+T (global toggle)
  - WCAG 2.1 AA compliance (non-negotiable):
    - ARIA labels on all interactive elements (aria-label, aria-describedby)
    - Keyboard navigation: Tab (next), Shift+Tab (prev), Enter (activate), Esc (close)
    - Focus indicators: 2px outline, 3:1 contrast ratio minimum
    - Color not sole indicator: Use icons + text for all state changes
  - Follow DESIGN_SYSTEM.md color palette:
    - Glass: Blue (#3b82f6)
    - Human: Green (#10b981)
    - Catalyst: Amber (#f59e0b)
    - Exchange: Purple (#a855f7)
    - Danger: Red (#ef4444), Success: Green (#22c55e)
  - Performance targets:
    - LedgerCard render time: < 100ms (NFR-UX-P-003)
    - AgentTerminal update latency: < 100ms (NFR-UX-P-002)
    - SafetyButton interaction latency: < 50ms (NFR-UX-P-004)
  - Component naming convention: PascalCase, descriptive (e.g., GlassLedgerCard, not Card1)

SUCCESS CRITERIA:
  - [x] LedgerCard: 4 variants × 4 states = 16 Storybook stories passing
  - [x] AgentTerminal: 5 message types + interactions = 8 Storybook stories passing
  - [x] SafetyButton: 3 variants × 3 states = 9 Storybook stories passing
  - [x] All components pass axe-core audit (0 violations)
  - [x] REQ-UX-001 table view toggle functional with Ctrl+Shift+T
  - [x] Component tests pass (vitest)
  - [x] Matches DESIGN_SYSTEM.md specification exactly (visual regression TBD)

BRANCH: feat/REQ-UX-001-core-component-library
COMMIT PATTERN:
  1. docs: Add component library architecture
  2. feat(ui): Implement LedgerCard with 4 variants
  3. feat(ui): Implement AgentTerminal with streaming
  4. feat(ui): Implement SafetyButton with confirmation flow
  5. feat(ui): Add table view toggle (REQ-UX-001)
  6. test(ui): Add component unit tests
  7. docs(storybook): Add component stories for all states
```

#### Deliverables

1. **Documentation** (Tier 2)
   - `frontend/src/components/README.md` with:
     - Component architecture overview
     - Props interface documentation (TypeScript)
     - Usage examples with code snippets
     - Accessibility features documentation
   
2. **Implementation** (Code)
   - `frontend/src/components/LedgerCard/` (4 variant files)
     - `LedgerCard.tsx` (base component)
     - `GlassLedgerCard.tsx`
     - `HumanLedgerCard.tsx`
     - `CatalystLedgerCard.tsx`
     - `ExchangeLedgerCard.tsx`
   - `frontend/src/components/AgentTerminal/AgentTerminal.tsx`
   - `frontend/src/components/SafetyButton/SafetyButton.tsx`
   - Component tests: `*.test.tsx` for each component
   - Accessibility helpers: `src/utils/accessibility.ts`

3. **Validation** (Tests & Storybook)
   - Storybook stories: 33 stories total (16 + 8 + 9)
   - Accessibility audit reports (axe-core, saved in `docs/accessibility/`)
   - Component unit tests (vitest, > 80% coverage)

---

### Track C: Storybook Setup & Documentation Infrastructure

**Agent**: The Architect (Orchestrator)  
**Requirements**: NFR-DOC-001, NFR-DOC-002  
**Estimated Effort**: 1 day

#### Context Injection Prompt

```markdown
CONTEXT: Sprint 2.15 - Track C: Storybook Infrastructure & Component Documentation
PROJECT: Oh My Coins - Frontend Documentation Infrastructure
ROLE: The Architect (System Orchestrator)

TIERED ACCESS:
  READ ONLY:
    - Tier 1: DOCUMENTATION_STRATEGY.md (Section 2.5: Tier 4 Auto-Generated Docs)
    - Tier 3: DESIGN_SYSTEM.md (for Storybook theming)
  
  WRITE/UPDATE:
    - Tier 2: frontend/README.md (Storybook usage instructions)
    - Tier 4: Storybook configuration (.storybook/*)

MISSION:
Set up Storybook 8.x with accessibility addon, theming per DESIGN_SYSTEM.md, 
and automated component documentation generation.

SPECIFIC OBJECTIVES:
1. Install and configure Storybook 8.x for React + TypeScript + Vite
2. Configure accessibility addon (axe-core) for automated WCAG 2.1 AA audits
3. Implement custom theme matching DESIGN_SYSTEM.md color palette
4. Set up automatic JSDoc → Storybook docs generation
5. Configure Chromatic for visual regression testing (preparation)

DOC-GATE REQUIREMENTS:
  - [ ] Update frontend/README.md with Storybook commands and usage
  - [ ] Document Storybook theming decisions in .storybook/README.md
  - [ ] Add Storybook URL to DOCUMENTATION_STRATEGY.md Tier 4 section

CONSTRAINTS:
  - Use Storybook 8.x (latest stable)
  - Accessibility addon REQUIRED (automatic axe-core audits)
  - Theme must match DESIGN_SYSTEM.md color palette exactly
  - Storybook must run on http://localhost:6006 (standard port)
  - Build time for Storybook: < 30 seconds (NFR-P-005)

SUCCESS CRITERIA:
  - [ ] Storybook runs locally: `npm run storybook`
  - [ ] Accessibility addon shows axe-core results for all stories
  - [ ] Theme matches DESIGN_SYSTEM.md (Glass blue, Human green, etc.)
  - [ ] JSDoc comments auto-generate component docs
  - [ ] No console errors or warnings in Storybook
  - [ ] README.md documents Storybook usage

BRANCH: feat/NFR-DOC-001-storybook-setup
```

#### Deliverables

1. **Infrastructure** (Configuration)
   - `.storybook/main.ts` (Storybook configuration)
   - `.storybook/preview.ts` (Global decorators, theming)
   - `.storybook/theme.ts` (Custom theme per DESIGN_SYSTEM.md)
   - `.storybook/README.md` (Configuration documentation)

2. **Documentation** (Tier 2)
   - `frontend/README.md` updated with Storybook section:
     - Installation: `npm install`
     - Development: `npm run storybook`
     - Build: `npm run build-storybook`
     - Accessibility testing workflow

3. **Validation** (Tests)
   - Storybook runs without errors
   - Accessibility addon functional (axe-core reports visible)
   - Theme renders correctly

---

## Documentation Gates (Quality Checklist)

All tracks MUST pass these gates before PR approval:

### Gate 1: Requirement Traceability ✅
- [ ] PR title references REQ-UX-001, REQ-UX-002, or NFR-DOC-001
- [ ] Requirements exist in SYSTEM_REQUIREMENTS.md Section 9
- [ ] Component requirements linked to USER_JOURNEYS.md

### Gate 2: Tier 2 Documentation ✅
- [ ] Component README.md created with architecture overview
- [ ] Props interfaces documented with JSDoc
- [ ] Usage examples provided

### Gate 3: Tier 4 Auto-Documentation ✅
- [ ] Storybook stories created for all component states
- [ ] JSDoc comments generate component docs in Storybook
- [ ] Accessibility audit results visible in Storybook

### Gate 4: Test Coverage ✅
- [ ] Component unit tests added (vitest, > 80% coverage)
- [ ] All Storybook stories render without errors
- [ ] Accessibility tests pass (axe-core, 0 violations)

### Gate 5: Accessibility (Frontend) ✅
- [ ] ARIA labels on all interactive elements
- [ ] Keyboard navigation tested (Tab, Enter, Esc)
- [ ] REQ-UX-001 table view toggle implemented on LedgerCard
- [ ] axe-core audit passes (0 violations)
- [ ] Focus indicators visible (2px outline, 3:1 contrast)

---

## Sprint Retrospective Checklist

At sprint end, The Architect validates:

### Documentation Sync ✅
- [ ] DESIGN_SYSTEM.md component specs match implementation
- [ ] Component README.md files up-to-date
- [ ] Storybook deployed locally (http://localhost:6006)
- [ ] DOCUMENTATION_STRATEGY.md updated with Storybook URL
- [ ] No orphaned documentation

### Requirement Validation ✅
- [ ] REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005 implemented
- [ ] All components link to USER_JOURNEYS.md workflows
- [ ] validate_requirement_ids.py passes

### Archive Obsolete Docs ✅
- [ ] Sprint 2.15 completion doc moved to `/docs/archive/history/sprints/sprint-2.15/`
- [ ] No obsolete docs identified (first implementation sprint)

### AI Agent Governance Pilot ✅
- [ ] Doc-Sync Check GitHub Action ran on all PRs
- [ ] PR template checklist completed for all merges
- [ ] Context injection prompts effective (agent feedback captured)
- [ ] Documentation gates prevented drift (track incidents)

---

## Sprint Metrics

Track these metrics for continuous improvement:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| PRs with Doc Updates | 100% | - | 🟡 |
| Test Coverage (Components) | > 80% | - | 🟡 |
| Documentation Drift Incidents | 0 | - | 🟡 |
| Storybook Stories Passing | 100% | - | 🟡 |
| Accessibility Violations | 0 | - | 🟡 |
| Component Render Performance | < 100ms | - | 🟡 |

---

## Next Sprint Planning

**Complete during sprint retrospective (January 30, 2026)**

### Sprint 2.16 Preparation

#### 1. Review Current Sprint Outcomes
- [ ] All 3 core components implemented?
- [ ] Storybook functional with accessibility addon?
- [ ] Any carryover work? (e.g., visual regression setup)
- [ ] Learnings about component complexity or accessibility challenges?

#### 2. Validate Phase Roadmap Alignment
- [ ] Phase 3 timeline still accurate? (2 sprints remaining: 2.16, potential 2.16.5)
- [ ] Dependencies resolved for 4 Ledgers dashboard implementation?
- [ ] Any blockers for chart library integration (recharts, visx, lightweight-charts)?

#### 3. Define Next Sprint Scope

**Proposed Sprint 2.16 Focus**: 4 Ledgers Dashboard Implementation

**Requirements to Implement**:
- [ ] REQ-GL-001: Glass Ledger Card (TVL/Fee line charts) - Priority: High
- [ ] REQ-HL-001: Human Ledger Card (Sentiment heatmap) - Priority: High
- [ ] REQ-CL-001: Catalyst Ledger Card (Real-time event ticker) - Priority: High
- [ ] REQ-EX-001: Exchange Ledger Card (Multi-coin sparklines) - Priority: High
- [ ] REQ-UX-006: 4 Ledgers dashboard layout (2x2 grid, responsive) - Priority: High
- [ ] REQ-UX-007: WebSocket integration for real-time updates - Priority: Medium

**Track Assignments** (preliminary):
- **Track A**: Backend - WebSocket endpoints for real-time data - Agent: Feature Developer
- **Track B**: Frontend - 4 Ledgers dashboard with chart integration - Agent: UI/UX Agent
- **Track C**: Integration - E2E test skeleton for Discovery Flow (USER_JOURNEYS.md Journey 1) - Agent: Quality Agent

**Estimated Duration**: 4-5 days

#### 4. Create Next Sprint SIM
- [ ] Copy SIM_TEMPLATE.md to `SPRINT_2.16_SIM.md`
- [ ] Fill in objectives: Implement DATA_VISUALIZATION_SPEC.md charts
- [ ] Define context injection prompts for chart library integration
- [ ] Set documentation gates: Link to USER_JOURNEYS.md Journey 1
- [ ] Update CURRENT_SPRINT.md to point to Sprint 2.16

#### 5. Risk Assessment
Identify risks for Sprint 2.16:

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Chart library performance issues (recharts/visx) | Medium | High | Benchmark early, consider react-window for virtualization |
| WebSocket connection stability | Medium | High | Implement fallback polling, disconnected state handling (REQ-FL-DISC-001) |
| Real-time data volume overwhelming UI | Low | Medium | Implement data throttling, show only last N records |
| Accessibility challenges with canvas-based charts | High | High | REQ-UX-001 table view toggle already implemented, extend to all chart types |
| Chart integration complexity (4 different libraries) | Medium | Medium | Start with simplest (recharts for Glass), validate pattern before others |

#### 6. Planning Notes

**Technical Decisions for Sprint 2.16**:
- **Chart Library Selection**:
  - Glass Ledger: recharts (line charts, dual Y-axis)
  - Human Ledger: visx (calendar heatmap - more control)
  - Catalyst Ledger: Custom component (scrolling ticker, no chart lib needed)
  - Exchange Ledger: lightweight-charts (performant sparklines)
- **WebSocket Strategy**: Use native WebSocket API first, consider Socket.io if connection management too complex
- **Data Fetching**: React Query for polling, WebSocket for real-time, fallback gracefully
- **Responsive Strategy**: 2x2 grid desktop, 2x2 stacked tablet, 1x4 scrollable mobile (per DATA_VISUALIZATION_SPEC.md)

**Scope Adjustments**:
- Defer visual regression testing (Chromatic) to Sprint 2.16.5 if time-constrained
- Prioritize Glass and Catalyst ledgers first (most critical per USER_JOURNEYS.md Journey 1)
- Human and Exchange ledgers can be Sprint 2.16 stretch goals if needed

---

**Next Sprint Status**: 🟡 PLANNING (to be completed January 30)  
**Planning Completed By**: The Architect  
**Planning Date**: January 24, 2026 (preliminary)

---

**Sprint Status**: 🟢 READY TO START  
**Created By**: The Architect  
**Approved By**: Tech Lead (pending)  
**Related Docs**: [DOCS_GOVERNANCE.md](../DOCS_GOVERNANCE.md), [DOCUMENTATION_STRATEGY.md](../DOCUMENTATION_STRATEGY.md), [ROADMAP.md](../../ROADMAP.md)
