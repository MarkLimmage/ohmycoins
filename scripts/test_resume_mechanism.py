"""Test: verify that passing None to astream correctly resumes past interrupt_before."""
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
    print("BEFORE: next=%s" % (state.next,))
    print("BEFORE: tasks=%d" % len(state.tasks))
    for t in state.tasks:
        print("  task: name=%s interrupts=%s" % (t.name, t.interrupts))
    
    # Try to stream with None (current approach)
    print("\nStreaming with None input...")
    count = 0
    try:
        async for chunk in wf.graph.astream(None, config):
            count += 1
            if isinstance(chunk, dict):
                print("  Chunk %d: keys=%s" % (count, list(chunk.keys())))
            else:
                print("  Chunk %d: type=%s" % (count, type(chunk)))
            if count >= 3:
                break
    except Exception as e:
        print("  ERROR: %s" % e)
    
    state2 = await wf.graph.aget_state(config)
    print("\nAFTER: next=%s" % (state2.next,))

asyncio.run(check())
