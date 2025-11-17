"""
Agent Orchestrator for coordinating multiple specialized agents.

This is the main entry point for the agentic data science system.
"""

import uuid
from typing import Any

from sqlmodel import Session

from app.models import AgentSessionStatus

from .session_manager import SessionManager
from .langgraph_workflow import LangGraphWorkflow, AgentState


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents to accomplish user goals.

    Week 1-2: Integrated with LangGraph workflow foundation.
    Weeks 7-8: Full ReAct loop implementation will be added.
    """

    def __init__(self, session_manager: SessionManager) -> None:
        """
        Initialize the orchestrator with a session manager.

        Args:
            session_manager: Session manager for state persistence
        """
        self.session_manager = session_manager
        self.workflow = LangGraphWorkflow(session=None)  # Session will be set per execution

    async def start_session(
        self, db: Session, session_id: uuid.UUID
    ) -> dict[str, Any]:
        """
        Start executing an agent session.

        Args:
            db: Database session
            session_id: ID of the session to start

        Returns:
            Initial response with session status
        """
        # Get the session from database
        session = await self.session_manager.get_session(db, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update status to running
        await self.session_manager.update_session_status(
            db, session_id, AgentSessionStatus.RUNNING
        )

        # Add initial system message
        await self.session_manager.add_message(
            db,
            session_id,
            role="system",
            content="Agent system initialized. Processing your request...",
        )

        # Initialize session state in Redis
        initial_state = {
            "session_id": str(session_id),
            "user_goal": session.user_goal,
            "status": AgentSessionStatus.RUNNING,
            "current_step": "initialization",
            "iteration": 0,
        }
        await self.session_manager.save_session_state(session_id, initial_state)

        return {
            "session_id": str(session_id),
            "status": AgentSessionStatus.RUNNING,
            "message": "Session started successfully",
        }

    async def execute_step(
        self, db: Session, session_id: uuid.UUID
    ) -> dict[str, Any]:
        """
        Execute one step of the agent workflow using LangGraph.

        Week 1-2: Basic LangGraph workflow execution.
        Weeks 7-8: Enhanced with full ReAct loop.

        Args:
            db: Database session
            session_id: ID of the session

        Returns:
            Step execution result
        """
        # Get current state
        state = await self.session_manager.get_session_state(session_id)
        if not state:
            raise ValueError(f"Session state not found for {session_id}")

        # Check if this is the first iteration - if so, run the full workflow
        iteration = state.get("iteration", 0)
        
        if iteration == 0:
            # First iteration - execute the full LangGraph workflow
            session = await self.session_manager.get_session(db, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Set database session for workflow agents
            self.workflow.set_session(db)
            
            # Prepare initial state for LangGraph
            langgraph_state: AgentState = {
                "session_id": str(session_id),
                "user_goal": session.user_goal,
                "status": AgentSessionStatus.RUNNING,
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
            
            # Execute the workflow
            final_state = await self.workflow.execute(langgraph_state)
            
            # Update session state with results
            state.update(final_state)
            await self.session_manager.save_session_state(session_id, state)
            
            # Add messages from workflow to session
            for msg in final_state.get("messages", []):
                await self.session_manager.add_message(
                    db,
                    session_id,
                    role=msg["role"],
                    content=msg["content"],
                )
            
            # Update session status
            if final_state.get("status") == "completed":
                await self.session_manager.update_session_status(
                    db,
                    session_id,
                    AgentSessionStatus.COMPLETED,
                    result_summary=final_state.get("result", "Workflow completed successfully"),
                )
                await self.session_manager.delete_session_state(session_id)
                return {
                    "session_id": str(session_id),
                    "status": AgentSessionStatus.COMPLETED,
                    "message": "Session completed",
                }
        else:
            # Subsequent iterations (for future incremental execution)
            iteration += 1
            state["iteration"] = iteration
            await self.session_manager.save_session_state(session_id, state)

        return {
            "session_id": str(session_id),
            "status": AgentSessionStatus.RUNNING,
            "message": f"Step {iteration} completed",
            "current_step": state.get("current_step", "processing"),
        }

    async def cancel_session(
        self, db: Session, session_id: uuid.UUID
    ) -> dict[str, Any]:
        """
        Cancel a running agent session.

        Args:
            db: Database session
            session_id: ID of the session to cancel

        Returns:
            Cancellation result
        """
        # Update status to cancelled
        await self.session_manager.update_session_status(
            db, session_id, AgentSessionStatus.CANCELLED
        )

        # Clean up state
        await self.session_manager.delete_session_state(session_id)

        return {
            "session_id": str(session_id),
            "status": AgentSessionStatus.CANCELLED,
            "message": "Session cancelled successfully",
        }
