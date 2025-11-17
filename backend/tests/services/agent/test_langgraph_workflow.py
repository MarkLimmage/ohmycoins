"""
Tests for LangGraph Workflow.

Week 1-2: Basic workflow tests with mock agents.
"""

import pytest
from app.services.agent.langgraph_workflow import LangGraphWorkflow, AgentState


@pytest.mark.asyncio
async def test_workflow_initialization():
    """Test that workflow initializes correctly."""
    workflow = LangGraphWorkflow()
    assert workflow is not None
    assert workflow.graph is not None
    assert workflow.data_retrieval_agent is not None


@pytest.mark.asyncio
async def test_workflow_execute_basic():
    """Test basic workflow execution."""
    workflow = LangGraphWorkflow()
    
    # Prepare initial state
    initial_state: AgentState = {
        "session_id": "test-session-123",
        "user_goal": "Analyze Bitcoin price trends",
        "status": "running",
        "current_step": "start",
        "iteration": 0,
        "data_retrieved": False,
        "messages": [],
        "result": None,
        "error": None,
    }
    
    # Execute workflow
    final_state = await workflow.execute(initial_state)
    
    # Verify final state
    assert final_state is not None
    assert final_state["status"] == "completed"
    assert final_state["data_retrieved"] is True
    assert len(final_state["messages"]) > 0
    assert final_state["result"] is not None


@pytest.mark.asyncio
async def test_workflow_state_progression():
    """Test that workflow progresses through all states."""
    workflow = LangGraphWorkflow()
    
    initial_state: AgentState = {
        "session_id": "test-session-456",
        "user_goal": "Test workflow progression",
        "status": "running",
        "current_step": "start",
        "iteration": 0,
        "data_retrieved": False,
        "messages": [],
        "result": None,
        "error": None,
    }
    
    final_state = await workflow.execute(initial_state)
    
    # Check that we went through expected steps
    messages = final_state["messages"]
    assert any("initialized" in msg["content"].lower() for msg in messages)
    assert any("retrieval" in msg["content"].lower() for msg in messages)
    assert any("completed" in msg["content"].lower() for msg in messages)


@pytest.mark.asyncio
async def test_initialize_node():
    """Test the initialize node directly."""
    workflow = LangGraphWorkflow()
    
    state: AgentState = {
        "session_id": "test",
        "user_goal": "Test",
        "status": "running",
        "current_step": "start",
        "iteration": 0,
        "data_retrieved": False,
        "messages": [],
        "result": None,
        "error": None,
    }
    
    updated_state = await workflow._initialize_node(state)
    
    assert updated_state["current_step"] == "initialization"
    assert len(updated_state["messages"]) > 0
    assert updated_state["messages"][0]["role"] == "system"


@pytest.mark.asyncio
async def test_retrieve_data_node():
    """Test the data retrieval node directly."""
    workflow = LangGraphWorkflow()
    
    state: AgentState = {
        "session_id": "test",
        "user_goal": "Test",
        "status": "running",
        "current_step": "initialization",
        "iteration": 0,
        "data_retrieved": False,
        "messages": [],
        "result": None,
        "error": None,
    }
    
    updated_state = await workflow._retrieve_data_node(state)
    
    assert updated_state["current_step"] == "data_retrieval"
    assert updated_state["data_retrieved"] is True
    assert any("retrieval" in msg["content"].lower() for msg in updated_state["messages"])


@pytest.mark.asyncio
async def test_finalize_node():
    """Test the finalize node directly."""
    workflow = LangGraphWorkflow()
    
    state: AgentState = {
        "session_id": "test",
        "user_goal": "Test",
        "status": "running",
        "current_step": "data_retrieval",
        "iteration": 0,
        "data_retrieved": True,
        "messages": [],
        "result": None,
        "error": None,
    }
    
    updated_state = await workflow._finalize_node(state)
    
    assert updated_state["current_step"] == "finalization"
    assert updated_state["status"] == "completed"
    assert updated_state["result"] is not None
    assert any("completed" in msg["content"].lower() for msg in updated_state["messages"])


@pytest.mark.asyncio
async def test_workflow_with_different_goals():
    """Test workflow with different user goals."""
    workflow = LangGraphWorkflow()
    
    goals = [
        "Analyze Ethereum price trends",
        "Predict Bitcoin volatility",
        "Compare top 10 cryptocurrencies",
    ]
    
    for goal in goals:
        initial_state: AgentState = {
            "session_id": f"test-{goal[:10]}",
            "user_goal": goal,
            "status": "running",
            "current_step": "start",
            "iteration": 0,
            "data_retrieved": False,
            "messages": [],
            "result": None,
            "error": None,
        }
        
        final_state = await workflow.execute(initial_state)
        
        assert final_state["status"] == "completed"
        assert final_state["user_goal"] == goal
