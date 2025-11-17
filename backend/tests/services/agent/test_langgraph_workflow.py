"""
Tests for LangGraph Workflow.

Week 1-2: Basic workflow tests with mock agents.
Week 3-4: Enhanced tests for DataAnalystAgent node.
"""

import pytest
from unittest.mock import Mock
from app.services.agent.langgraph_workflow import LangGraphWorkflow, AgentState


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock()


@pytest.mark.asyncio
async def test_workflow_initialization():
    """Test that workflow initializes correctly."""
    workflow = LangGraphWorkflow()
    assert workflow is not None
    assert workflow.graph is not None
    assert workflow.data_retrieval_agent is not None
    assert workflow.data_analyst_agent is not None


@pytest.mark.asyncio
async def test_workflow_execute_basic(mock_db_session):
    """Test basic workflow execution."""
    workflow = LangGraphWorkflow(session=mock_db_session)
    
    # Prepare initial state
    initial_state: AgentState = {
        "session_id": "test-session-123",
        "user_goal": "Analyze Bitcoin price trends",
        "status": "running",
        "current_step": "start",
        "iteration": 0,
        "data_retrieved": False,
        "analysis_completed": False,
        "messages": [],
        "result": None,
        "error": None,
        "retrieved_data": None,
        "analysis_results": None,
        "insights": None,
        "retrieval_params": {},
        "analysis_params": {},
    }
    
    # Execute workflow
    final_state = await workflow.execute(initial_state)
    
    # Verify final state
    assert final_state is not None
    assert final_state["status"] == "completed"
    assert final_state["data_retrieved"] is True
    assert final_state["analysis_completed"] is True
    assert len(final_state["messages"]) > 0
    assert final_state["result"] is not None


@pytest.mark.asyncio
async def test_workflow_state_progression(mock_db_session):
    """Test that workflow progresses through all states."""
    workflow = LangGraphWorkflow(session=mock_db_session)
    
    initial_state: AgentState = {
        "session_id": "test-session-456",
        "user_goal": "Test workflow progression",
        "status": "running",
        "current_step": "start",
        "iteration": 0,
        "data_retrieved": False,
        "analysis_completed": False,
        "messages": [],
        "result": None,
        "error": None,
        "retrieved_data": None,
        "analysis_results": None,
        "insights": None,
        "retrieval_params": {},
        "analysis_params": {},
    }
    
    final_state = await workflow.execute(initial_state)
    
    # Check that we went through expected steps
    messages = final_state["messages"]
    assert any("initialized" in msg["content"].lower() for msg in messages)
    assert any("retrieval" in msg["content"].lower() for msg in messages)
    assert any("analysis" in msg["content"].lower() for msg in messages)
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
        "analysis_completed": False,
        "messages": [],
        "result": None,
        "error": None,
        "retrieved_data": None,
        "analysis_results": None,
        "insights": None,
        "retrieval_params": {},
        "analysis_params": {},
    }
    
    updated_state = await workflow._initialize_node(state)
    
    assert updated_state["current_step"] == "initialization"
    assert len(updated_state["messages"]) > 0
    assert updated_state["messages"][0]["role"] == "system"
    assert updated_state["analysis_completed"] is False


@pytest.mark.asyncio
async def test_retrieve_data_node(mock_db_session):
    """Test the data retrieval node directly."""
    workflow = LangGraphWorkflow(session=mock_db_session)
    
    state: AgentState = {
        "session_id": "test",
        "user_goal": "Test",
        "status": "running",
        "current_step": "initialization",
        "iteration": 0,
        "data_retrieved": False,
        "analysis_completed": False,
        "messages": [],
        "result": None,
        "error": None,
        "retrieved_data": None,
        "analysis_results": None,
        "insights": None,
        "retrieval_params": {},
        "analysis_params": {},
    }
    
    updated_state = await workflow._retrieve_data_node(state)
    
    assert updated_state["current_step"] == "data_retrieval"
    # Note: data_retrieved will be False without proper DB, but node should execute
    assert any("retrieval" in msg["content"].lower() for msg in updated_state["messages"])


@pytest.mark.asyncio
async def test_analyze_data_node():
    """Test the data analysis node directly."""
    workflow = LangGraphWorkflow()
    
    state: AgentState = {
        "session_id": "test",
        "user_goal": "Test analysis",
        "status": "running",
        "current_step": "data_retrieval",
        "iteration": 0,
        "data_retrieved": True,
        "analysis_completed": False,
        "messages": [],
        "result": None,
        "error": None,
        "retrieved_data": {
            "price_data": [],
            "available_coins": ["BTC"],
        },
        "analysis_results": None,
        "insights": None,
        "retrieval_params": {},
        "analysis_params": {},
    }
    
    updated_state = await workflow._analyze_data_node(state)
    
    assert updated_state["current_step"] == "data_analysis"
    assert any("analysis" in msg["content"].lower() for msg in updated_state["messages"])


@pytest.mark.asyncio
async def test_finalize_node():
    """Test the finalize node directly."""
    workflow = LangGraphWorkflow()
    
    state: AgentState = {
        "session_id": "test",
        "user_goal": "Test",
        "status": "running",
        "current_step": "data_analysis",
        "iteration": 0,
        "data_retrieved": True,
        "analysis_completed": True,
        "messages": [],
        "result": None,
        "error": None,
        "retrieved_data": {},
        "analysis_results": {},
        "insights": ["Test insight 1", "Test insight 2"],
        "retrieval_params": {},
        "analysis_params": {},
    }
    
    updated_state = await workflow._finalize_node(state)
    
    assert updated_state["current_step"] == "finalization"
    assert updated_state["status"] == "completed"
    assert updated_state["result"] is not None
    assert "Test insight 1" in updated_state["result"]
    assert any("completed" in msg["content"].lower() for msg in updated_state["messages"])


@pytest.mark.asyncio
async def test_workflow_with_different_goals(mock_db_session):
    """Test workflow with different user goals."""
    workflow = LangGraphWorkflow(session=mock_db_session)
    
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
            "analysis_completed": False,
            "messages": [],
            "result": None,
            "error": None,
            "retrieved_data": None,
            "analysis_results": None,
            "insights": None,
            "retrieval_params": {},
            "analysis_params": {},
        }
        
        final_state = await workflow.execute(initial_state)
        
        assert final_state["status"] == "completed"
        assert final_state["user_goal"] == goal
