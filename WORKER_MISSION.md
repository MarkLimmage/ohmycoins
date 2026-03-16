# Worker Mission: Resilience Bridge Agent (Workstream B/B+)

**Spec Version:** v1.2
**Dependency:** Workstream A (merge after A — needs EventLedger + ActionRequestEvent)

## Task
Implement MemorySaver checkpointing, HITL interrupt gates, and state rehydration.

## Deliverables
1. **MemorySaver Checkpointer:** Add `MemorySaver()` to `LangGraphWorkflow.__init__()`. Compile graph with `checkpointer=self._checkpointer`.
2. **Interrupt Gates:** `interrupt_before=["train_model", "finalize"]` per REQUIREMENTS.md §1.2.
3. **HITL Event Flow:** On interrupt, emit `action_request` event (API_CONTRACTS.md §2.3) + `status_update` with `AWAITING_APPROVAL`, then persist and exit.
4. **Resume Logic:** Wire `AgentOrchestrator.resume_session()` to use `thread_id` derived from `session_id`.
5. **[B+] Rehydration Endpoint:** `GET /api/v1/lab/agent/sessions/{id}/rehydrate` returning `{ session_id, last_sequence_id, event_ledger[] }`.
6. **[B+] WebSocket `?after_seq`:** Add query parameter to skip already-seen events on reconnect.
7. **[B+] MemorySaver Limitation:** Document that in-memory checkpointer loses state on process restart. Phase 6 migrates to PostgresSaver.

## Files to Modify
- `backend/app/services/agent/langgraph_workflow.py` — checkpointer, interrupt_before
- `backend/app/services/agent/runner.py` — interrupt handling, HITL event emission
- `backend/app/services/agent/orchestrator.py` — `resume_session()` with thread_id
- `backend/app/api/routes/lab.py` — rehydration GET endpoint
- `backend/app/api/routes/lab.py` — WebSocket `?after_seq` parameter

## Constraints
- Do NOT write React code, Dagger logic, or agent tool implementations.
- Follow `API_CONTRACTS.md` v1.2 §2.3 (action_request) and §3 (rehydration) exactly.
- If a contract is impossible, write `CONTRACT_RFC.md` and halt.
