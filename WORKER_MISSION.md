# Worker Mission: Safety Bridge Agent (Workstream D/D+)

**Spec Version:** v1.2
**Dependency:** None (first in merge order)

## Task
Implement Statistical Health Gates and the per-stage circuit breaker.

## Deliverables
1. **Zero-Variance Kill-Switch:** In `_validate_data_node`, detect zero variance in target/features or >90% outliers → emit `TERMINAL_DATA_ERROR` and route to `END`.
2. **3-Cycle Per-Stage Circuit Breaker:** Add `stage_iteration_counts: dict[str, int]` to `AgentState`. On the 4th attempt for any stage, trigger `Human_in_the_Loop` interrupt or `TERMINAL_ERROR`.
3. **Data Insufficiency Routing:** If retrieved data < 50 rows after 1 retry, route to `finalize` with `completed_with_errors`.

## Files to Modify
- `backend/app/services/agent/langgraph_workflow.py` — circuit breaker logic, `stage_iteration_counts` in `AgentState`
- `backend/app/services/agent/nodes/` — validation node changes

## Constraints
- Do NOT write FastAPI routes, React code, or WebSocket logic.
- Follow `API_CONTRACTS.md` v1.2 error schema (§4).
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.
