"""
Tests for Phase 7.2.1/7.2.2 Stale Protocol endpoints:
- POST /sessions/{id}/stages/{stage}/revise
- POST /sessions/{id}/stages/{stage}/rerun
- POST /sessions/{id}/stages/{stage}/keep-stale
- POST /sessions/{id}/messages (stage parameter)
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture
def created_session(
    client: TestClient, auth_headers: dict[str, str]
) -> dict:
    """Create a session and return its data."""
    with patch("app.api.routes.agent.get_runner") as mock_get_runner:
        mock_runner = MagicMock()
        mock_runner.start_session = AsyncMock()
        mock_get_runner.return_value = mock_runner

        response = client.post(
            "/api/v1/lab/agent/sessions",
            json={"user_goal": "Predict BTC price"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        return response.json()


class TestReviseEndpoint:
    """Tests for POST /sessions/{id}/stages/{stage_id}/revise"""

    @patch("app.api.routes.agent.get_runner")
    def test_revise_returns_202(
        self,
        mock_get_runner: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        mock_runner = MagicMock()
        mock_runner.start_session = AsyncMock()
        mock_get_runner.return_value = mock_runner

        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/DATA_ACQUISITION/revise",
            json={"instructions": "Use 7-day window instead"},
            headers=auth_headers,
        )
        assert response.status_code == 202
        data = response.json()
        assert "revision_id" in data
        # Verify runner was re-invoked
        mock_runner.start_session.assert_called_once()

    @patch("app.api.routes.agent.get_runner")
    def test_revise_without_instructions(
        self,
        mock_get_runner: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        mock_runner = MagicMock()
        mock_runner.start_session = AsyncMock()
        mock_get_runner.return_value = mock_runner

        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/PREPARATION/revise",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 202

    def test_revise_invalid_stage(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/INVALID_STAGE/revise",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_revise_nonexistent_session(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = uuid.uuid4()
        response = client.post(
            f"/api/v1/lab/agent/sessions/{fake_id}/stages/MODELING/revise",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_revise_requires_auth(
        self,
        client: TestClient,
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/MODELING/revise",
            json={},
        )
        assert response.status_code == 401

    @patch("app.api.routes.agent.get_runner")
    def test_revise_emits_stale_events(
        self,
        mock_get_runner: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
        session: Session,
    ) -> None:
        """Revising DATA_ACQUISITION should mark PREPARATION..DEPLOYMENT as STALE."""
        mock_runner = MagicMock()
        mock_runner.start_session = AsyncMock()
        mock_get_runner.return_value = mock_runner

        session_id = created_session["id"]
        client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/DATA_ACQUISITION/revise",
            json={},
            headers=auth_headers,
        )

        # Check rehydrate for the stale events
        response = client.get(
            f"/api/v1/lab/agent/sessions/{session_id}/rehydrate",
            headers=auth_headers,
        )
        data = response.json()
        ledger = data["event_ledger"]

        # Should have revision_start event
        revision_events = [e for e in ledger if e["event_type"] == "revision_start"]
        assert len(revision_events) >= 1
        assert revision_events[0]["payload"]["revised_stage"] == "DATA_ACQUISITION"
        assert "PREPARATION" in revision_events[0]["payload"]["stale_stages"]

        # Should have STALE status_updates for downstream stages
        stale_events = [
            e for e in ledger
            if e["event_type"] == "status_update"
            and e.get("payload", {}).get("status") == "STALE"
        ]
        stale_stages = [e["stage"] for e in stale_events]
        assert "PREPARATION" in stale_stages
        assert "EXPLORATION" in stale_stages
        assert "MODELING" in stale_stages


class TestRerunEndpoint:
    """Tests for POST /sessions/{id}/stages/{stage_id}/rerun"""

    @patch("app.api.routes.agent.get_runner")
    def test_rerun_returns_202(
        self,
        mock_get_runner: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        mock_runner = MagicMock()
        mock_runner.start_session = AsyncMock()
        mock_get_runner.return_value = mock_runner

        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/PREPARATION/rerun",
            headers=auth_headers,
        )
        assert response.status_code == 202
        mock_runner.start_session.assert_called_once()

    def test_rerun_invalid_stage(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/NOTREAL/rerun",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_rerun_requires_auth(
        self,
        client: TestClient,
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/MODELING/rerun",
        )
        assert response.status_code == 401


class TestKeepStaleEndpoint:
    """Tests for POST /sessions/{id}/stages/{stage_id}/keep-stale"""

    def test_keep_stale_returns_200(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/EXPLORATION/keep-stale",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "EXPLORATION"

    def test_keep_stale_emits_complete(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        """keep-stale should emit a COMPLETE status_update."""
        session_id = created_session["id"]
        client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/MODELING/keep-stale",
            headers=auth_headers,
        )

        response = client.get(
            f"/api/v1/lab/agent/sessions/{session_id}/rehydrate",
            headers=auth_headers,
        )
        ledger = response.json()["event_ledger"]
        complete_events = [
            e for e in ledger
            if e["event_type"] == "status_update"
            and e.get("payload", {}).get("status") == "COMPLETE"
            and e["stage"] == "MODELING"
        ]
        assert len(complete_events) >= 1

    def test_keep_stale_invalid_stage(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/BAD_STAGE/keep-stale",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_keep_stale_requires_auth(
        self,
        client: TestClient,
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/stages/MODELING/keep-stale",
        )
        assert response.status_code == 401


class TestMessageStageParameter:
    """Tests for optional `stage` parameter on POST /messages."""

    def test_message_with_stage(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/messages",
            json={"content": "Use more features", "stage": "MODELING"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "MODELING"

    def test_message_without_stage(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        created_session: dict,
    ) -> None:
        """Without stage, should derive from last message (backward compatible)."""
        session_id = created_session["id"]
        response = client.post(
            f"/api/v1/lab/agent/sessions/{session_id}/messages",
            json={"content": "Hello agent"},
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestLabSchemaStaleProtocol:
    """Unit tests for lab_schema additions."""

    def test_revision_start_event_schema(self) -> None:
        from app.services.agent.lab_schema import RevisionStartEvent, StageID

        event = RevisionStartEvent(
            event_type="revision_start",
            stage=StageID.DATA_ACQUISITION,
            sequence_id=42,
            timestamp="2026-03-21T00:00:00.000Z",
            payload={
                "revised_stage": "DATA_ACQUISITION",
                "stale_stages": ["PREPARATION", "EXPLORATION"],
                "revision_epoch": 1,
            },
        )
        assert event.event_type == "revision_start"
        assert event.stage == StageID.DATA_ACQUISITION

    def test_stages_after(self) -> None:
        from app.services.agent.lab_schema import StageID, stages_after

        result = stages_after(StageID.DATA_ACQUISITION)
        assert result == [
            StageID.PREPARATION,
            StageID.EXPLORATION,
            StageID.MODELING,
            StageID.EVALUATION,
            StageID.DEPLOYMENT,
        ]

    def test_stages_after_last(self) -> None:
        from app.services.agent.lab_schema import StageID, stages_after

        result = stages_after(StageID.DEPLOYMENT)
        assert result == []

    def test_dslc_stage_order(self) -> None:
        from app.services.agent.lab_schema import DSLC_STAGE_ORDER, StageID

        assert len(DSLC_STAGE_ORDER) == 7
        assert DSLC_STAGE_ORDER[0] == StageID.BUSINESS_UNDERSTANDING
        assert DSLC_STAGE_ORDER[-1] == StageID.DEPLOYMENT
