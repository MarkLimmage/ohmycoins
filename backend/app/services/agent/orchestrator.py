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
            Step execution result including workflow state
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
                # Week 3-4 fields
                "retrieved_data": None,
                "analysis_results": None,
                "insights": None,
                "retrieval_params": {},
                "analysis_params": {},
                # Week 5-6 fields
                "model_trained": False,
                "model_evaluated": False,
                "trained_models": None,
                "evaluation_results": None,
                "training_params": {},
                "evaluation_params": {},
                "training_summary": None,
                "evaluation_insights": None,
                # Week 7-8 fields - ReAct loop
                "reasoning_trace": [],
                "decision_history": [],
                "retry_count": 0,
                "max_retries": 3,
                "skip_analysis": False,
                "skip_training": False,
                "needs_more_data": False,
                "quality_checks": {},
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
                    "workflow_state": state,  # Include the state before deletion
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
            "workflow_state": state,  # Include the state
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
    
    def get_session_state(self, db: Session | uuid.UUID, session_id: uuid.UUID = None) -> dict[str, Any] | None:
        """
        Get the current state of a session synchronously.
        
        This is a synchronous wrapper for the async get_session_state method,
        used by the HiTL endpoints and tests.
        
        Args:
            db: Database session (for test compatibility) OR session_id for direct calls
            session_id: ID of the session (optional if db is actually session_id)
            
        Returns:
            Session state dictionary or None if not found
        """
        import asyncio
        
        # Handle both calling conventions:
        # - New: get_session_state(db, session_id) for tests
        # - Old: get_session_state(session_id) for existing code
        if session_id is None:
            # Called with just session_id (old style)
            actual_session_id = db
        else:
            # Called with db, session_id (new test style)
            actual_session_id = session_id
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async method
        return loop.run_until_complete(
            self.session_manager.get_session_state(actual_session_id)
        )
    
    def update_session_state(
        self, session_id: uuid.UUID, state: dict[str, Any]
    ) -> None:
        """
        Update the state of a session synchronously.
        
        Args:
            session_id: ID of the session
            state: Updated state dictionary
        """
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async method
        loop.run_until_complete(
            self.session_manager.save_session_state(session_id, state)
        )
    
    async def resume_session(
        self, db: Session, session_id: uuid.UUID
    ) -> dict[str, Any]:
        """
        Resume a paused session after user interaction.
        
        This is called after clarifications, choices, or approvals are provided.
        
        Args:
            db: Database session
            session_id: ID of the session to resume
            
        Returns:
            Resume result
        """
        # Get current state
        state = await self.session_manager.get_session_state(session_id)
        
        if not state:
            raise ValueError(f"Session {session_id} state not found")
        
        # Update status to running if it was paused
        if state.get("status") != AgentSessionStatus.RUNNING:
            state["status"] = AgentSessionStatus.RUNNING
            await self.session_manager.save_session_state(session_id, state)
            
            await self.session_manager.update_session_status(
                db, session_id, AgentSessionStatus.RUNNING
            )
        
        # Add message about resumption
        await self.session_manager.add_message(
            db,
            session_id,
            role="system",
            content=f"Workflow resumed from {state.get('current_step', 'unknown')} step",
        )
        
        # The workflow will continue from its current state
        # In a full implementation, this would trigger the next workflow step
        
        return {
            "session_id": str(session_id),
            "status": AgentSessionStatus.RUNNING,
            "message": "Session resumed successfully",
            "current_step": state.get("current_step"),
        }
    
    async def run_workflow(
        self, db: Session, session_id: uuid.UUID
    ) -> dict[str, Any]:
        """
        Run a complete workflow from start to finish.
        
        This is a high-level method that combines start_session and execute_step
        to run the entire workflow. It's primarily used by integration tests.
        
        Args:
            db: Database session
            session_id: ID of the session to run
            
        Returns:
            Workflow execution result with status and any generated data
        """
        # Get the session from database
        session = await self.session_manager.get_session(db, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Start the session
        await self.start_session(db, session_id)
        
        # Execute the workflow step
        result = await self.execute_step(db, session_id)
        
        # Build response combining execution result and workflow state
        response = {
            "session_id": str(session_id),
            "status": result.get("status", "completed"),
        }
        
        # Add workflow state fields to the response for test compatibility
        workflow_state = result.get("workflow_state", {})
        if workflow_state:
            response.update(workflow_state)
        
        return response
