"""Inspect LangGraph checkpoint state for a session."""
import asyncio
import sys

sys.path.insert(0, "/app")

SESSION_ID = sys.argv[1] if len(sys.argv) > 1 else "084e0760-45d4-4cbf-92b4-3139801d2b43"

async def check():
    from app.services.agent.runner import get_runner
    runner = get_runner()
    checkpointer = await runner._get_checkpointer()
    
    from app.services.agent.langgraph_workflow import LangGraphWorkflow
    wf = LangGraphWorkflow(session=None, checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": SESSION_ID}}
    state = await wf.graph.aget_state(config)
    
    print("Next:", state.next)
    meta = state.metadata or {}
    writes = meta.get("writes", {})
    print("Metadata writes keys:", list(writes.keys()))
    print("Tasks:", len(state.tasks))
    for t in state.tasks:
        print("  Task:", t.name, "interrupts=", t.interrupts)
    
    # Check key state values
    vals = state.values
    for key in ["model_trained", "approval_granted", "approval_needed", "error", "retry_count", "current_stage"]:
        print(f"  {key}: {vals.get(key)}")

asyncio.run(check())
