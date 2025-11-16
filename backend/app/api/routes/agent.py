"""
API routes for Agent Sessions (Phase 3 - Agentic Data Science).

Provides endpoints for creating, managing, and interacting with agent sessions.
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    AgentArtifactPublic,
    AgentSession,
    AgentSessionCreate,
    AgentSessionMessagePublic,
    AgentSessionPublic,
    AgentSessionsPublic,
)
from app.services.agent import AgentOrchestrator, SessionManager

router = APIRouter()

# Global session manager and orchestrator
# TODO: Move to dependency injection in production
session_manager = SessionManager()
orchestrator = AgentOrchestrator(session_manager)


@router.post("/sessions", response_model=AgentSessionPublic, status_code=201)
async def create_agent_session(
    *,
    session_in: AgentSessionCreate,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Create a new agent session.

    This initiates a new agentic data science workflow with a user-defined goal.

    Args:
        session_in: Session creation data with user goal
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Created agent session
    """
    # Create session in database
    session = await session_manager.create_session(
        db, current_user.id, session_in
    )

    # Start the agent workflow asynchronously
    # TODO: Use background tasks or celery for production
    try:
        await orchestrator.start_session(db, session.id)
    except Exception as e:
        # If start fails, update session status
        await session_manager.update_session_status(
            db, session.id, "failed", error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to start session: {e}")

    return session


@router.get("/sessions", response_model=AgentSessionsPublic)
async def list_agent_sessions(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all agent sessions for the current user.

    Args:
        db: Database session
        current_user: Currently authenticated user
        skip: Number of sessions to skip
        limit: Maximum number of sessions to return

    Returns:
        List of agent sessions
    """
    statement = (
        select(AgentSession)
        .where(AgentSession.user_id == current_user.id)
        .order_by(AgentSession.created_at.desc())  # type: ignore[attr-defined]
        .offset(skip)
        .limit(limit)
    )
    sessions = db.exec(statement).all()

    count_statement = (
        select(AgentSession)
        .where(AgentSession.user_id == current_user.id)
    )
    count = len(db.exec(count_statement).all())

    return AgentSessionsPublic(data=sessions, count=count)


@router.get("/sessions/{session_id}", response_model=AgentSessionPublic)
async def get_agent_session(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get details of a specific agent session.

    Args:
        session_id: ID of the session to retrieve
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Agent session details

    Raises:
        HTTPException: If session not found or user doesn't have access
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    return session


@router.delete("/sessions/{session_id}", response_model=dict[str, str])
async def delete_agent_session(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Delete an agent session.

    This cancels the session if running and deletes all associated data.

    Args:
        session_id: ID of the session to delete
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If session not found or user doesn't have access
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")

    # Cancel if running
    if session.status == "running":
        await orchestrator.cancel_session(db, session_id)

    # Delete from database (cascade will delete messages and artifacts)
    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}


@router.get("/sessions/{session_id}/messages", response_model=list[AgentSessionMessagePublic])
async def get_session_messages(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get all messages for an agent session.

    Args:
        session_id: ID of the session
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of session messages

    Raises:
        HTTPException: If session not found or user doesn't have access
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    return session.messages


@router.get("/sessions/{session_id}/artifacts", response_model=list[AgentArtifactPublic])
async def get_session_artifacts(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get all artifacts for an agent session.

    Args:
        session_id: ID of the session
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List of session artifacts

    Raises:
        HTTPException: If session not found or user doesn't have access
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    return session.artifacts


@router.post("/sessions/{session_id}/cancel", response_model=dict[str, str])
async def cancel_agent_session(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Cancel a running agent session.

    Args:
        session_id: ID of the session to cancel
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: If session not found or user doesn't have access
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this session")

    if session.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Session is not active")

    await orchestrator.cancel_session(db, session_id)

    return {"message": "Session cancelled successfully"}
