"""
Session Manager for Agent Sessions.

Manages the lifecycle of agent sessions including creation, state persistence,
and cleanup.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    AgentSession,
    AgentSessionCreate,
    AgentSessionMessage,
    AgentSessionStatus,
)


class SessionManager:
    """Manages agent session lifecycle and state persistence."""

    def __init__(self) -> None:
        """Initialize the session manager with Redis connection."""
        self.redis_client: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis for state management."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(  # type: ignore[no-untyped-call]
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None

    async def create_session(
        self, db: Session, user_id: uuid.UUID, session_data: AgentSessionCreate
    ) -> AgentSession:
        """
        Create a new agent session in the database.

        Args:
            db: Database session
            user_id: ID of the user creating the session
            session_data: Session creation data

        Returns:
            Created agent session
        """
        session = AgentSession(
            user_id=user_id,
            user_goal=session_data.user_goal,
            status=AgentSessionStatus.PENDING,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    async def get_session(
        self, db: Session, session_id: uuid.UUID
    ) -> AgentSession | None:
        """
        Get an agent session by ID.

        Args:
            db: Database session
            session_id: ID of the session to retrieve

        Returns:
            Agent session or None if not found
        """
        statement = select(AgentSession).where(AgentSession.id == session_id)
        result = db.exec(statement)
        return result.first()

    async def update_session_status(
        self,
        db: Session,
        session_id: uuid.UUID,
        status: str,
        error_message: str | None = None,
        result_summary: str | None = None,
    ) -> None:
        """
        Update the status of an agent session.

        Args:
            db: Database session
            session_id: ID of the session to update
            status: New status
            error_message: Optional error message if failed
            result_summary: Optional result summary if completed
        """
        statement = select(AgentSession).where(AgentSession.id == session_id)
        result = db.exec(statement)
        session = result.first()

        if session:
            session.status = status
            session.updated_at = datetime.now(timezone.utc)

            if error_message:
                session.error_message = error_message
            if result_summary:
                session.result_summary = result_summary
            if status in [AgentSessionStatus.COMPLETED, AgentSessionStatus.FAILED, AgentSessionStatus.CANCELLED]:
                session.completed_at = datetime.now(timezone.utc)

            db.add(session)
            db.commit()

    async def add_message(
        self,
        db: Session,
        session_id: uuid.UUID,
        role: str,
        content: str,
        agent_name: str | None = None,
        metadata: str | None = None,
    ) -> AgentSessionMessage:
        """
        Add a message to the session conversation history.

        Args:
            db: Database session
            session_id: ID of the session
            role: Message role (user, assistant, system, function)
            content: Message content
            agent_name: Optional name of the agent that sent the message
            metadata: Optional JSON metadata

        Returns:
            Created message
        """
        message = AgentSessionMessage(
            session_id=session_id,
            role=role,
            content=content,
            agent_name=agent_name,
            metadata=metadata,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    async def get_session_state(self, session_id: uuid.UUID) -> dict[str, Any] | None:
        """
        Get the current state of a session from Redis.

        Args:
            session_id: ID of the session

        Returns:
            Session state dictionary or None if not found
        """
        if not self.redis_client:
            await self.connect()

        if self.redis_client:
            state_key = f"agent:session:{session_id}:state"
            state_data = await self.redis_client.get(state_key)
            if state_data:
                import json
                result: dict[str, Any] = json.loads(state_data)
                return result
        return None

    async def save_session_state(
        self, session_id: uuid.UUID, state: dict[str, Any]
    ) -> None:
        """
        Save the current state of a session to Redis.

        Args:
            session_id: ID of the session
            state: Session state dictionary to save
        """
        if not self.redis_client:
            await self.connect()

        if self.redis_client:
            import json
            state_key = f"agent:session:{session_id}:state"
            # Store with 24-hour expiration
            await self.redis_client.setex(
                state_key, 86400, json.dumps(state)
            )

    async def delete_session_state(self, session_id: uuid.UUID) -> None:
        """
        Delete the state of a session from Redis.

        Args:
            session_id: ID of the session
        """
        if not self.redis_client:
            await self.connect()

        if self.redis_client:
            state_key = f"agent:session:{session_id}:state"
            await self.redis_client.delete(state_key)
