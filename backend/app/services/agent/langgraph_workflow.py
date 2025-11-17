"""
LangGraph Workflow for Agent Orchestration.

This module implements the LangGraph state machine that coordinates
specialized agents to accomplish user goals.

Week 1-2 implementation: Basic workflow foundation using existing price data.
Week 3-4 enhancement: Added DataAnalystAgent node for comprehensive analysis.
"""

from typing import Any, TypedDict
from sqlmodel import Session

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.agent.agents.base import BaseAgent
from app.services.agent.agents.data_retrieval import DataRetrievalAgent
from app.services.agent.agents.data_analyst import DataAnalystAgent


class AgentState(TypedDict):
    """
    State dictionary for the agent workflow.
    
    This state is passed between nodes in the LangGraph workflow.
    
    Week 3-4 additions: retrieved_data, analysis_results, insights
    """
    session_id: str
    user_goal: str
    status: str
    current_step: str
    iteration: int
    data_retrieved: bool
    analysis_completed: bool
    messages: list[dict[str, str]]
    result: str | None
    error: str | None
    # Week 3-4 additions
    retrieved_data: dict[str, Any] | None
    analysis_results: dict[str, Any] | None
    insights: list[str] | None
    retrieval_params: dict[str, Any] | None
    analysis_params: dict[str, Any] | None


class LangGraphWorkflow:
    """
    LangGraph-based workflow for coordinating multiple agents.
    
    This implements a state machine that routes between specialized agents
    based on the current state and user goal.
    
    Week 3-4: Enhanced with DataAnalystAgent for comprehensive data analysis.
    """

    def __init__(self, session: Session | None = None) -> None:
        """
        Initialize the LangGraph workflow with agents and state graph.
        
        Args:
            session: Optional database session for agents
        """
        self.session = session
        self.graph = self._build_graph()
        self.data_retrieval_agent = DataRetrievalAgent(session=session)
        self.data_analyst_agent = DataAnalystAgent()
        
        # Initialize LLM for reasoning (if API key available)
        self.llm = None
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                max_tokens=settings.MAX_TOKENS_PER_REQUEST,
                streaming=settings.ENABLE_STREAMING,
            )
    
    def set_session(self, session: Session) -> None:
        """
        Set the database session for agents.
        
        Args:
            session: Database session
        """
        self.session = session
        self.data_retrieval_agent.set_session(session)

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        Week 3-4: Added analyze_data node between retrieve_data and finalize.
        
        Returns:
            Configured state graph
        """
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for different stages
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("retrieve_data", self._retrieve_data_node)
        workflow.add_node("analyze_data", self._analyze_data_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define edges (workflow transitions)
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "retrieve_data")
        workflow.add_edge("retrieve_data", "analyze_data")
        workflow.add_edge("analyze_data", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()

    async def _initialize_node(self, state: AgentState) -> AgentState:
        """
        Initialize the workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        state["current_step"] = "initialization"
        state["messages"] = state.get("messages", [])
        state["analysis_completed"] = False
        state["messages"].append({
            "role": "system",
            "content": "Agent workflow initialized. Starting data retrieval and analysis pipeline..."
        })
        return state

    async def _retrieve_data_node(self, state: AgentState) -> AgentState:
        """
        Execute data retrieval agent.
        
        Week 3-4: Enhanced to retrieve comprehensive data (price, sentiment, on-chain, catalysts).
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with retrieved data
        """
        state["current_step"] = "data_retrieval"
        
        # Execute data retrieval agent
        updated_state = await self.data_retrieval_agent.execute(state)
        
        # Add message about data retrieval
        data_types = updated_state.get("retrieval_metadata", {}).get("data_types", [])
        updated_state["messages"].append({
            "role": "assistant",
            "content": f"Data retrieval completed. Retrieved: {', '.join(data_types)}"
        })
        
        return updated_state

    async def _analyze_data_node(self, state: AgentState) -> AgentState:
        """
        Execute data analyst agent.
        
        Week 3-4: New node for comprehensive data analysis.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with analysis results
        """
        state["current_step"] = "data_analysis"
        
        # Execute data analyst agent
        updated_state = await self.data_analyst_agent.execute(state)
        
        # Add message about analysis
        insights = updated_state.get("insights", [])
        insight_summary = "; ".join(insights[:3]) if insights else "Analysis complete"
        updated_state["messages"].append({
            "role": "assistant",
            "content": f"Data analysis completed. Key insights: {insight_summary}"
        })
        
        return updated_state

    async def _finalize_node(self, state: AgentState) -> AgentState:
        """
        Finalize the workflow and prepare results.
        
        Week 3-4: Enhanced to include analysis results and insights in final result.
        
        Args:
            state: Current workflow state
            
        Returns:
            Final state with results
        """
        state["current_step"] = "finalization"
        state["status"] = "completed"
        
        # Build comprehensive result message
        insights = state.get("insights", [])
        if insights:
            result_parts = ["Analysis complete. Key insights:"]
            result_parts.extend([f"- {insight}" for insight in insights])
            state["result"] = "\n".join(result_parts)
        else:
            state["result"] = "Workflow completed successfully."
        
        state["messages"].append({
            "role": "assistant",
            "content": "Workflow completed. All results prepared."
        })
        
        return state

    async def execute(self, initial_state: AgentState) -> AgentState:
        """
        Execute the workflow from start to finish.
        
        Args:
            initial_state: Initial workflow state
            
        Returns:
            Final workflow state
        """
        # Execute the graph with the initial state
        final_state = await self.graph.ainvoke(initial_state)
        return final_state

    async def stream_execute(self, initial_state: AgentState):
        """
        Execute the workflow with streaming for real-time updates.
        
        Args:
            initial_state: Initial workflow state
            
        Yields:
            State updates as the workflow progresses
        """
        async for state in self.graph.astream(initial_state):
            yield state
