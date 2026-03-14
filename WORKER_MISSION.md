# 🧠 WORKER MISSION: Graph Agent (Sprint 2.50)

**Role:** You are the **Graph Agent**. You are the sole developer for the LangGraph Orchestrator & WebSocket Gateway.
**Context:** Parallel Sprint 2.50 - Phase 2 (Orchestration) & Phase 5 (Hardening/HITL).

## 🎯 YOUR MISSION
You must refactor the LangGraph state machine to enforce human oversight and eliminate infinite loops.

### Critical Objectives
1.  **Mandatory Interrupts:** Implement `interrupt_before=["PREPARATION", "MODELING"]` in the graph compilation. The graph MUST halt and await user input at these stages.
2.  **The "No-Loop" Policy:**
    *   If the agent detects `insufficient_data`, it must transition directly to an `ERROR` node and `END`.
    *   **Strictly Forbidden:** Transitioning back to `Reasoning` or `Business_Understanding` upon data failure.
3.  **UI Synchronization:**
    *   On **EVERY** node entry/exit, you must emit a `status_update` event via WebSockets.
    *   You must emit a `render_output` event (even if empty) to clear/update the UI grid.
4.  **Mocking:** Mock the Dagger execution tools. You assume the Engine Agent is handling the real execution.

### ⛔ CONSTRAINTS
*   **Port:** Run your FastAPI server on **Port 8000**.
*   **DO NOT** write specific Dagger implementation code (Engine Agent does that).
*   **DO NOT** write React code.
*   **STRICTLY** follow the schemas in `API_CONTRACTS.md`.

### 📝 CONTRACT RFC
If you need to send a signal that isn't in `API_CONTRACTS.md`, write a `CONTRACT_RFC.md` and HALT.
