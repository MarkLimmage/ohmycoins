"""
Tests for agent session API routes — non-blocking creation and credential passthrough.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import AgentSessionStatus


@pytest.fixture
def auth_headers(client: TestClient, session: Session) -> dict[str, str]:
    """Get auth headers for a normal user."""
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    email = random_email()
    return authentication_token_from_email(client=client, email=email, db=session)


class TestCreateSession:
    """Tests for POST /api/v1/lab/agent/sessions"""

    @patch("app.api.routes.agent.get_runner")
    def test_create_session_returns_immediately(
        self, mock_get_runner: MagicMock, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Session creation should return immediately without blocking."""
        mock_runner = MagicMock()
        mock_get_runner.return_value = mock_runner

        response = client.post(
            "/api/v1/lab/agent/sessions",
            json={"user_goal": "Predict BTC price"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == AgentSessionStatus.PENDING
        assert data["user_goal"] == "Predict BTC price"
        # Runner should have been called
        mock_runner.start_session.assert_called_once()

    def test_create_schema_accepts_credential(self) -> None:
        """AgentSessionCreate schema should accept llm_credential_id."""
        from app.models import AgentSessionCreate

        cred_id = uuid.uuid4()
        data = AgentSessionCreate(user_goal="Predict ETH price", llm_credential_id=cred_id)
        assert data.llm_credential_id == cred_id
        assert data.user_goal == "Predict ETH price"

    @patch("app.api.routes.agent.get_runner")
    def test_create_session_without_credential(
        self, mock_get_runner: MagicMock, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Session creation should work without llm_credential_id."""
        mock_runner = MagicMock()
        mock_get_runner.return_value = mock_runner

        response = client.post(
            "/api/v1/lab/agent/sessions",
            json={"user_goal": "Analyze SOL trends"},
            headers=auth_headers,
        )

        assert response.status_code == 201

    def test_create_session_requires_auth(self, client: TestClient) -> None:
        """Session creation should require authentication."""
        response = client.post(
            "/api/v1/lab/agent/sessions",
            json={"user_goal": "Test"},
        )
        assert response.status_code == 401

    @patch("app.api.routes.agent.get_runner")
    def test_create_session_validates_goal(
        self, mock_get_runner: MagicMock, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Session creation should validate user_goal."""
        mock_runner = MagicMock()
        mock_get_runner.return_value = mock_runner

        # Empty goal
        response = client.post(
            "/api/v1/lab/agent/sessions",
            json={"user_goal": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListSessions:
    """Tests for GET /api/v1/lab/agent/sessions"""

    @patch("app.api.routes.agent.get_runner")
    def test_list_sessions(
        self, mock_get_runner: MagicMock, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Listing sessions should return user's sessions."""
        mock_runner = MagicMock()
        mock_get_runner.return_value = mock_runner

        # Create a session first
        client.post(
            "/api/v1/lab/agent/sessions",
            json={"user_goal": "Test list"},
            headers=auth_headers,
        )

        response = client.get("/api/v1/lab/agent/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["data"]) >= 1
