"""
API routes for Agent Sessions (Phase 3 - Agentic Data Science).

Provides endpoints for creating, managing, and interacting with agent sessions.
Week 9-10 additions: Human-in-the-Loop endpoints (clarifications, choices, approvals, overrides)
Week 11-12 additions: Artifact management endpoints (download, delete)
"""

import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
from app.services.agent.artifacts import ArtifactManager
from app.services.agent.nodes.approval import (
    handle_approval_granted,
    handle_approval_rejected,
)
from app.services.agent.nodes.choice_presentation import handle_choice_selection
from app.services.agent.nodes.clarification import handle_clarification_response
from app.services.agent.override import apply_user_override, get_override_points

router = APIRouter()

# Global session manager, orchestrator, and artifact manager
# TODO: Move to dependency injection in production
session_manager = SessionManager()
orchestrator = AgentOrchestrator(session_manager)
artifact_manager = ArtifactManager()


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
    session = await session_manager.create_session(db, current_user.id, session_in)

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

    count_statement = select(AgentSession).where(
        AgentSession.user_id == current_user.id
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
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

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
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this session"
        )

    # Cancel if running
    if session.status == "running":
        await orchestrator.cancel_session(db, session_id)

    # Delete from database (cascade will delete messages and artifacts)
    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}


@router.get(
    "/sessions/{session_id}/messages", response_model=list[AgentSessionMessagePublic]
)
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
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

    return session.messages


@router.get(
    "/sessions/{session_id}/artifacts", response_model=list[AgentArtifactPublic]
)
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
        raise HTTPException(
            status_code=403, detail="Not authorized to access this session"
        )

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
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this session"
        )

    if session.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Session is not active")

    await orchestrator.cancel_session(db, session_id)

    return {"message": "Session cancelled successfully"}


# ============================================================================
# Human-in-the-Loop (HiTL) Endpoints - Week 9-10
# ============================================================================


# Pydantic models for HiTL requests/responses
class ClarificationResponse(BaseModel):
    """User responses to clarification questions."""

    responses: dict[str, str]


class ChoiceSelection(BaseModel):
    """User selection from available choices."""

    selected_model: str


class ApprovalDecision(BaseModel):
    """User approval or rejection."""

    approved: bool
    reason: str | None = None


class OverrideRequest(BaseModel):
    """User override request."""

    override_type: str
    override_data: dict[str, Any]


# Clarification endpoints
@router.get("/sessions/{session_id}/clarifications")
async def get_clarifications(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get pending clarification questions for a session.

    Returns clarification questions that need user response
    before the workflow can proceed.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get state from session
    state = orchestrator.get_session_state(session_id)

    if not state or not state.get("awaiting_clarification"):
        return {
            "awaiting_clarification": False,
            "clarifications_needed": [],
        }

    return {
        "awaiting_clarification": True,
        "clarifications_needed": state.get("clarifications_needed", []),
        "current_goal": state.get("user_goal", ""),
    }


@router.post("/sessions/{session_id}/clarifications")
async def provide_clarifications(
    *,
    session_id: uuid.UUID,
    clarifications: ClarificationResponse,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Provide responses to clarification questions.

    This resumes the workflow with the provided clarifications.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get current state
    state = orchestrator.get_session_state(session_id)

    if not state or not state.get("awaiting_clarification"):
        raise HTTPException(
            status_code=400, detail="Session is not awaiting clarification"
        )

    # Apply clarifications
    updated_state = handle_clarification_response(state, clarifications.responses)

    # Update state and resume workflow
    orchestrator.update_session_state(session_id, updated_state)
    await orchestrator.resume_session(db, session_id)

    return {
        "message": "Clarifications received, workflow resumed",
        "updated_goal": updated_state.get("user_goal"),
    }


# Choice presentation endpoints
@router.get("/sessions/{session_id}/choices")
async def get_choices(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get available choices for user selection.

    Returns model choices with pros/cons and recommendation.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get state from session
    state = orchestrator.get_session_state(session_id)

    if not state or not state.get("awaiting_choice"):
        return {
            "awaiting_choice": False,
            "choices_available": [],
        }

    return {
        "awaiting_choice": True,
        "choices_available": state.get("choices_available", []),
        "recommendation": state.get("recommendation"),
    }


@router.post("/sessions/{session_id}/choices")
async def select_choice(
    *,
    session_id: uuid.UUID,
    selection: ChoiceSelection,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Select a choice from available options.

    This resumes the workflow with the selected model.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get current state
    state = orchestrator.get_session_state(session_id)

    if not state or not state.get("awaiting_choice"):
        raise HTTPException(status_code=400, detail="Session is not awaiting choice")

    # Apply selection
    updated_state = handle_choice_selection(state, selection.selected_model)

    # Update state and resume workflow
    orchestrator.update_session_state(session_id, updated_state)
    await orchestrator.resume_session(db, session_id)

    return {
        "message": "Choice selected, workflow resumed",
        "selected_model": selection.selected_model,
    }


# Approval endpoints
@router.get("/sessions/{session_id}/pending-approvals")
async def get_pending_approvals(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get pending approval requests for a session.

    Returns approval requests that need user decision.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get state from session
    state = orchestrator.get_session_state(session_id)

    if not state or not state.get("approval_needed"):
        return {
            "approval_needed": False,
            "pending_approvals": [],
        }

    return {
        "approval_needed": True,
        "pending_approvals": state.get("pending_approvals", []),
        "approval_mode": state.get("approval_mode", "manual"),
    }


@router.post("/sessions/{session_id}/approve")
async def approve_request(
    *,
    session_id: uuid.UUID,
    decision: ApprovalDecision,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Approve or reject a pending approval request.

    This resumes the workflow if approved, or stops it if rejected.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get current state
    state = orchestrator.get_session_state(session_id)

    if not state or not state.get("approval_needed"):
        raise HTTPException(status_code=400, detail="Session is not awaiting approval")

    # Get approval type from pending approvals
    pending_approvals = state.get("pending_approvals", [])
    if not pending_approvals:
        raise HTTPException(status_code=400, detail="No pending approvals found")

    approval_type = pending_approvals[0].get("approval_type")

    # Apply approval or rejection
    if decision.approved:
        updated_state = handle_approval_granted(state, approval_type)
        message = "Approval granted, workflow resumed"
    else:
        updated_state = handle_approval_rejected(state, approval_type, decision.reason)
        message = "Approval rejected, workflow stopped"

    # Update state
    orchestrator.update_session_state(session_id, updated_state)

    if decision.approved:
        await orchestrator.resume_session(db, session_id)

    return {
        "message": message,
        "approved": decision.approved,
    }


# Override endpoints
@router.get("/sessions/{session_id}/override-points")
async def get_override_points_endpoint(
    *,
    session_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get available override points for a session.

    Returns which overrides are currently available based on workflow state.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get state from session
    state = orchestrator.get_session_state(session_id)

    if not state:
        return {"override_points": {}}

    override_points = get_override_points(state)

    return {
        "override_points": override_points,
        "overrides_applied": state.get("overrides_applied", []),
    }


@router.post("/sessions/{session_id}/override")
async def apply_override(
    *,
    session_id: uuid.UUID,
    override_request: OverrideRequest,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Apply a user override to the workflow.

    Allows users to override agent decisions and modify workflow behavior.
    """
    session = await session_manager.get_session(db, session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get current state
    state = orchestrator.get_session_state(session_id)

    if not state:
        raise HTTPException(status_code=400, detail="Session state not found")

    # Apply override
    try:
        updated_state = apply_user_override(
            state, override_request.override_type, override_request.override_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid override: {str(e)}")

    # Update state and resume workflow
    orchestrator.update_session_state(session_id, updated_state)
    await orchestrator.resume_session(db, session_id)

    return {
        "message": "Override applied, workflow adjusted",
        "override_type": override_request.override_type,
        "current_step": updated_state.get("current_step"),
    }


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(
    *,
    artifact_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> FileResponse:
    """
    Download an artifact file.

    Args:
        artifact_id: Artifact ID
        db: Database session
        current_user: Currently authenticated user

    Returns:
        File response with artifact content

    Raises:
        HTTPException: If artifact not found, user doesn't have access, or file not found
    """
    artifact = artifact_manager.get_artifact(artifact_id, db)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify user has access to this artifact's session
    session = await session_manager.get_session(db, artifact.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this artifact"
        )

    # Get file path
    file_path = artifact.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Artifact file not found")

    return FileResponse(
        path=file_path,
        filename=artifact.name,
        media_type=artifact.mime_type or "application/octet-stream",
    )


@router.delete("/artifacts/{artifact_id}")
async def delete_artifact(
    *,
    artifact_id: uuid.UUID,
    db: SessionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    """
    Delete an artifact.

    Args:
        artifact_id: Artifact ID
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If artifact not found or user doesn't have access
    """
    artifact = artifact_manager.get_artifact(artifact_id, db)

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Verify user has access to this artifact's session
    session = await session_manager.get_session(db, artifact.session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this artifact"
        )

    # Delete artifact
    if not artifact_manager.delete_artifact(artifact_id, db):
        raise HTTPException(status_code=500, detail="Failed to delete artifact")

    return {"message": "Artifact deleted successfully"}


@router.get("/artifacts/stats")
async def get_artifact_stats(
    db: SessionDep,
    _current_user: CurrentUser,
) -> dict[str, Any]:
    """
    Get artifact storage statistics.

    Args:
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Storage statistics
    """
    # Get stats - this shows all artifacts, but in production you might want to filter by user
    stats = artifact_manager.get_storage_stats(db)
    return stats
