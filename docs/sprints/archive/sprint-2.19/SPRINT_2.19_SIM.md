# Sprint 2.19 Initialization Manifest (SIM)

**Sprint Period**: March 8, 2026 - March 21, 2026
**Focus**: The Strategist - Automated Backtesting & Strategy Generation
**Team Composition**: The Dockmaster, The Data Scientist (Agent), The Feature Developer, The Architect

---

## Sprint Objectives

### Primary Goal
Empower "The Lab" with autonomous strategy generation and backtesting capabilities ("The Strategist"), allowing the system to propose, test, and promote trading strategies without human intervention.

### Success Criteria
- [x] **Strategy Generator**: LLM-driven generation of trading parameters based on "Catalyst" events.
- [x] **Backtesting Engine**: Fast, vectorised backtesting service (likely utilizing `vectorbt` or custom pandas logic).
- [x] **Automated Report Card**: Generation of "Strategy Cards" with Sharpe Ratio, Max Drawdown, and Win Rate.
- [x] **Lab-to-Floor Pipeline**: Fully automated promotion of high-performing strategies to the "Pending Approval" queue.

---

## Agent Assignments

### Track A: The Data Scientist (Analysis)
**Focus**: Strategy Generation Logic
- Develop prompt templates for converting "Event: BTC Spot ETF Approval" -> "Strategy: Long BTC/USD".
- Implement `StrategyGenerator` service in `backend/app/services/agent/strategist`.

### Track B: The Feature Developer (Engine)
**Focus**: Backtesting Infrastructure
- [x] Implement `BacktestService` for historical simulation.
- [x] Ensure isolation of backtest data (separate from live pricing).

### Track C: The Architect (Governance)
**Focus**: Safety & Validation
- Define "Golden Rules" for strategy approval (e.g., Min Sharpe > 1.5).
- Implement automated validation checks before promotion.

---

## Workspace Orchestration (Plan)

*   **Track A**: `feat/REQ-LAB-001` (Strategy Generator)
*   **Track B**: `feat/REQ-LAB-002` (Backtest Engine)
*   **Track C**: `feat/REQ-LAB-003` (Governance Rules)

---

## Operational Constraints

- **Mock Data First**: Track A must use mock data for backtests until Track B delivers the engine.
- **Containerization**: All heavy data processing must run in `optimization` containers to avoid stalling the API.

## Execution Log

| Timestamp | Actor | Action | Status |
|-----------|-------|--------|--------|
| 2026-03-08 09:00 | Dockmaster | Provisioned worktrees for Track A, B, C | ✅ Success |
| 2026-03-10 14:00 | Track A | Implemented StrategyGenerator with LangChain | ✅ Success |
| 2026-03-15 11:00 | Track B | Implemented BacktestService with Pandas | ✅ Success |
| 2026-03-18 10:00 | Architect | Merged Track A and Track B | ✅ Success |
| 2026-03-18 11:30 | Architect | Implemented GovernanceEvaluator (Track C) | ✅ Success |
| 2026-03-18 12:00 | Architect | Verified Governance Logic with Unit Tests | ✅ Success |
| 2026-03-21 16:00 | Architect | Sprint Finalization | ✅ Complete |
