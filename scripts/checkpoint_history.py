"""View checkpoint history for a session."""
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
    
    count = 0
    async for state in wf.graph.aget_state_history(config):
        meta = state.metadata or {}
        source = meta.get("source", "?")
        step = meta.get("step", "?")
        writes = list((meta.get("writes") or {}).keys())
        nxt = state.next
        print("Checkpoint %d: next=%s source=%s step=%s writes=%s" % (count, nxt, source, step, writes))
        count += 1
        if count >= 15:
            break

asyncio.run(check())
