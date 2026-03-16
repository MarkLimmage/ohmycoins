# Worker Mission: Messaging Bridge Agent (Workstream A/A+)

**Spec Version:** v1.2
**Dependency:** Workstream D (merge after D)

## Task
Refactor the messaging layer from flat dicts to the typed EventLedger system.

## Deliverables
1. **`emit_event()` helper** on `BaseAgent` — forces all agent output into `API_CONTRACTS.md` §1 envelope.
2. **Update all agents** (`DataRetrievalAgent`, `DataAnalystAgent`, `ModelTrainingAgent`, `ModelEvaluatorAgent`, `ReportingAgent`) to call `emit_event()`.
3. **`pending_events` list** in `AgentState` — runner drains and publishes.
4. **[A+] `BaseEvent` v1.2:** Add `sequence_id` (int, monotonic per session) and `timestamp` (ISO-8601 UTC) to `BaseEvent` in `lab_schema.py`.
5. **[A+] `ActionRequestEvent`** Pydantic model in `lab_schema.py` with `action_id`, `description`, `options`.
6. **Runner assigns `sequence_id`/`timestamp`** before publishing to Redis.

## Files to Modify
- `backend/app/services/agent/agents/base.py` — `emit_event()`
- `backend/app/services/agent/agents/data_retrieval.py`
- `backend/app/services/agent/agents/data_analyst.py`
- `backend/app/services/agent/agents/model_training.py`
- `backend/app/services/agent/agents/model_evaluator.py`
- `backend/app/services/agent/agents/reporting.py`
- `backend/app/services/agent/langgraph_workflow.py` — `pending_events` in `AgentState`
- `backend/app/services/agent/runner.py` — drain events, assign sequence_id/timestamp
- `backend/app/services/agent/lab_schema.py` — `BaseEvent`, `ActionRequestEvent`

## Constraints
- Do NOT write FastAPI routes, React code, or Dagger logic.
- Every event must match `API_CONTRACTS.md` v1.2 §1 envelope exactly.
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.
