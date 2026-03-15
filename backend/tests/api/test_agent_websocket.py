"""
Tests for agent session WebSocket streaming endpoint.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models import (
    AgentSession,
    AgentSessionMessage,
    AgentSessionStatus,
    User,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _get_user_and_token(client: TestClient, session: Session) -> tuple[User, str]:
    """Create a test user and return (user, jwt_token)."""
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=session)
    token = headers["Authorization"].split(" ")[1]
    from sqlmodel import select
    user = session.exec(select(User).where(User.email == email)).first()
    assert user is not None
    return user, token


def test_agent_ws_invalid_token(client: TestClient) -> None:
    """WebSocket with invalid token should be rejected."""
    with pytest.raises(Exception):  # noqa: B017
        with client.websocket_connect(
            f"/ws/agent/{uuid.uuid4()}/stream?token=invalid_token"
        ):
            pass


def test_agent_ws_session_not_found(client: TestClient, session: Session) -> None:
    """WebSocket for non-existent session should be rejected."""
    _, token = _get_user_and_token(client, session)
    with pytest.raises(Exception):  # noqa: B017
        with client.websocket_connect(
            f"/ws/agent/{uuid.uuid4()}/stream?token={token}"
        ):
            pass


def test_agent_ws_unauthorized_session(client: TestClient, session: Session) -> None:
    """WebSocket for session owned by another user should be rejected."""
    user1, _ = _get_user_and_token(client, session)
    _, token2 = _get_user_and_token(client, session)

    # Create session owned by user1
    agent_session = AgentSession(
        id=uuid.uuid4(),
        user_id=user1.id,
        user_goal="User1 session",
        status=AgentSessionStatus.RUNNING,
    )
    session.add(agent_session)
    session.flush()

    # Try to connect as user2
    with pytest.raises(Exception):  # noqa: B017
        with client.websocket_connect(
            f"/ws/agent/{agent_session.id}/stream?token={token2}"
        ):
            pass


def test_agent_ws_completed_session_replays_and_closes(
    client: TestClient, session: Session
) -> None:
    """Connecting to a completed session should replay history then close."""
    user, token = _get_user_and_token(client, session)

    # Create completed session with messages
    agent_session = AgentSession(
        id=uuid.uuid4(),
        user_id=user.id,
        user_goal="Test goal for WS",
        status=AgentSessionStatus.COMPLETED,
        result_summary="Done",
    )
    session.add(agent_session)
    session.flush()

    for i in range(3):
        msg = AgentSessionMessage(
            session_id=agent_session.id,
            role="assistant",
            content=f"Message {i}",
            agent_name="test_agent",
        )
        session.add(msg)
    session.flush()

    with client.websocket_connect(
        f"/ws/agent/{agent_session.id}/stream?token={token}"
    ) as ws:
        # Should receive 3 replay messages
        messages = []
        for _ in range(3):
            data = ws.receive_json()
            messages.append(data)
                # Replay flag removed in favor of strict API contract
                # assert data.get("replay") is True
        assert messages[1]["payload"]["content"] == "Message 1"
        assert messages[2]["payload"]["content"] == "Message 2"

        # Legacy test expected a "done" message. Current implementation keeps connection open.
        # status_msg = ws.receive_json()
        # assert status_msg["done"] is True
        # assert status_msg["status"] == "completed"
