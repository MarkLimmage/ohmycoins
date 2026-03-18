# 🧠 WORKER MISSION: Graph Agent (Conversational Pipeline)

**Branch:** `feature/langgraph-orchestrator`
**Directory:** `../omc-lab-graph`
**Port:** 8000 (FastAPI WebSocket Router)
**Role:** You are the Graph Agent. You are the sole developer in this worktree.

> ⚠️ **IGNORE** all legacy docs (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md). This file is your only mission brief. Read `API_CONTRACTS.md` (v1.3) as the strict schema contract.

---

## 🎯 Mission: Transform the Pipeline into a Conversation

The current Lab is an autopilot pipeline that emits sparse `status_update` events ("Step: initialization", "Step: reasoning") and presents two blind approval gates. The user has zero visibility into agent reasoning and zero ability to steer.

Your job is to make the agent **talk** — narrate its reasoning, present its interpretation, ask for confirmation, and respond to human input — while keeping the existing data pipeline intact.

---

## 📋 Workstream F: Conversational Pipeline (6 Tasks)

### F1. Wire Scope Confirmation into BUSINESS_UNDERSTANDING (MANDATORY)

**Files:** `backend/app/services/agent/langgraph_workflow.py`, `backend/app/services/agent/nodes/clarification.py`

The `clarification_node` already exists in `nodes/clarification.py` but is dead code — not wired into the graph.

1. Add a `scope_confirmation` node to the graph between `initialize` and `reason`.
2. Add `"scope_confirmation"` to `interrupt_before` list.
3. The node MUST:
   - Parse the `user_goal` and emit a `stream_chat` event explaining its interpretation
   - Emit an `action_request` with `action_id: "scope_confirmation_v1"` containing the parsed scope (assets, timeframe, analysis type, indicators)
   - Emit a `plan_established` event with the anticipated task list for the session
4. **NO CONDITIONAL SKIP.** Every session starts with scope confirmation. The user must explicitly CONFIRM or ADJUST before data retrieval begins.

**Resume path:** When user submits via `POST /sessions/{id}/clarifications`, call `handle_clarification_response()` to update state, then resume the graph.

**New graph flow:**
```
initialize → scope_confirmation [INTERRUPT] → reason → retrieve_data → ...
```

### F2. Wire Model Selection into EVALUATION

**Files:** `backend/app/services/agent/langgraph_workflow.py`, `backend/app/services/agent/nodes/choice_presentation.py`

The `choice_presentation_node` exists in `nodes/choice_presentation.py` but is dead code.

1. Add a `model_selection` node after `evaluate_model`, before `generate_report`.
2. Add `"model_selection"` to `interrupt_before` list (or wire it as a conditional interrupt after evaluate).
3. The node MUST emit `action_request` with `action_id: "model_selection_v1"` containing model comparison data (see API_CONTRACTS.md §2.3.3).
4. Resume via `POST /sessions/{id}/choices`.

**New graph flow:**
```
... → evaluate_model → model_selection [INTERRUPT] → generate_report → ...
```

### F3. Emit Reasoning as `stream_chat` Events

**Files:** `backend/app/services/agent/langgraph_workflow.py` (`_reason_node`), all agent `execute()` methods

The `_reason_node` currently stores reasoning in `reasoning_trace` (internal only) and never tells the user what it's thinking. The agents emit bare messages like `"Analyzing data..."`.

1. **Reasoning node:** After `_determine_next_action()`, emit a `stream_chat` event with a human-readable explanation:
   ```python
   await self._emit_event(state, "stream_chat", current_stage, {
       "text_delta": f"I've completed data retrieval with 720 BTC candles. The data quality looks good (no anomalies detected). Next I'll compute technical indicators (RSI, MACD, Bollinger Bands) to identify momentum patterns."
   })
   ```

2. **Agent execute() methods:** Upgrade status messages from bare labels to informative narration:
   - **DataRetrievalAgent:** `"Querying 30 days of BTC/USDT OHLCV data... Found 720 hourly candles. Now fetching sentiment scores from 3 sources..."`
   - **DataAnalystAgent:** `"Computing RSI(14) → currently at 72, indicating overbought. Running MACD crossover check... Golden cross detected on 4h chart."`
   - **ModelTrainingAgent:** `"Training XGBClassifier with 12 features across 680 samples. Running 5-fold cross-validation..."`
   - **ModelEvaluatorAgent:** `"Test accuracy: 85%. F1: 0.84. The model performs well on price direction but struggles with magnitude estimation."`

3. The `stream_chat` events go to the **Left Cell (Dialogue)** per API_CONTRACTS.md §2.1.

### F4. Emit `plan_established` After Scope Confirmation

**Files:** `backend/app/services/agent/nodes/clarification.py` or `langgraph_workflow.py`

After the user confirms scope in F1, the agent MUST emit a `plan_established` event containing the anticipated task list for all stages. See API_CONTRACTS.md §2.5 for the exact schema.

The plan should be dynamically generated based on the confirmed scope:
- If user wants "analysis only" → skip MODELING/EVALUATION tasks
- If user wants "full pipeline" → include all stages
- Task labels should reference the actual confirmed parameters (e.g., "Fetch 7d BTC/ETH OHLCV data")

### F5. Add `task_id` to Status Updates

**Files:** All agent `execute()` methods, `emit_event()` in `agents/base.py`

Add an optional `task_id` field to `status_update` payloads that matches the `task_id` in the `plan_established` event. This allows the Activity Tracker to update specific checklist items rather than just appending.

Example:
```python
await self.emit_event(state, "status_update", "DATA_ACQUISITION", {
    "status": "ACTIVE",
    "message": "Fetching 30d BTC/USDT OHLCV data...",
    "task_id": "fetch_price_data"
})
# ... work ...
await self.emit_event(state, "status_update", "DATA_ACQUISITION", {
    "status": "COMPLETE",
    "message": "Retrieved 720 hourly candles.",
    "task_id": "fetch_price_data"
})
```

### F6. Add `POST /message` Endpoint with Sequence Guarantee

**Files:** `backend/app/api/routes/agent.py`, `backend/app/services/agent/runner.py`

New endpoint: `POST /api/v1/lab/agent/sessions/{id}/message`

```json
Request:  { "content": "Focus on ETH instead" }
Response: { "message": "Received", "sequence_id": 42 }
```

**Implementation contract:**
1. Assign `sequence_id` N from the session's monotonic counter.
2. Persist the `user_message` event to the EventLedger (DB).
3. Broadcast the `user_message` event (with `sequence_id` N) via Redis pub/sub to all WS clients.
4. The agent's next response MUST be `sequence_id` N+1. Use a lock/semaphore to prevent race conditions.

### F7. Circuit Breaker → Clarification Escalation

**Files:** `backend/app/services/agent/langgraph_workflow.py` (`_route_after_error`, `handle_error`)

When the 3-cycle circuit breaker fires, instead of emitting `TERMINAL_ERROR`:
1. Emit `action_request` with `action_id: "circuit_breaker_v1"` (see API_CONTRACTS.md §2.3.4).
2. Set `interrupt_before` dynamically or use the existing `human_review` node.
3. The user chooses a suggestion, provides guidance, or aborts.

Only truly unrecoverable errors (zero-variance, sandbox crash) should use the `error` event type.

---

## 🚫 Constraints

- **DO NOT** write React/frontend code. That's the Glass Agent's job.
- **DO NOT** modify Dagger/MLflow sandbox code. That's the Engine Agent's job.
- **DO NOT** invent new event types beyond what's in API_CONTRACTS.md v1.3.
- **DO NOT** break existing E2E flow. The pipeline must still work end-to-end; you're adding conversational events on top.
- If a contract is impossible to implement, write a `CONTRACT_RFC.md` and halt.

## ✅ Definition of Done

1. `scope_confirmation` node wired and interrupting with rich `action_request`
2. `model_selection` node wired and interrupting with comparison data
3. Every node emits `stream_chat` events narrating its reasoning
4. `plan_established` event emitted after scope confirmation
5. `status_update` events include `task_id` matching the plan
6. `POST /message` endpoint returns `sequence_id` and broadcasts `user_message`
7. Circuit breaker escalates to `action_request` instead of `TERMINAL_ERROR`
8. All existing tests still pass
9. New tests for: scope_confirmation flow, message endpoint, plan_established emission
