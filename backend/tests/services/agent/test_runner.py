"""
Tests for AgentRunner — background session execution with Redis pub/sub.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.models import (
    AgentSession,
    AgentSessionCreate,
    AgentSessionStatus,
    User,
)
from app.services.agent.runner import AgentRunner, get_runner, shutdown_runner


@pytest.fixture
def runner() -> AgentRunner:
    return AgentRunner()


class TestAgentRunnerUnit:
    """Pure unit tests for AgentRunner — no DB or asyncio tasks."""

    def test_is_running_false_for_unknown(self, runner: AgentRunner) -> None:
        assert not runner.is_running(uuid.uuid4())

    def test_is_running_true_for_tracked_task(self, runner: AgentRunner) -> None:
        sid = uuid.uuid4()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        runner._tasks[sid] = mock_task
        assert runner.is_running(sid)

    def test_is_running_false_for_done_task(self, runner: AgentRunner) -> None:
        sid = uuid.uuid4()
        mock_task = MagicMock()
        mock_task.done.return_value = True
        runner._tasks[sid] = mock_task
        assert not runner.is_running(sid)

    def test_done_callback_cleans_up(self, runner: AgentRunner) -> None:
        sid = uuid.uuid4()
        mock_task = MagicMock()
        mock_task.cancelled.return_value = False
        mock_task.exception.return_value = None
        runner._tasks[sid] = mock_task

        runner._on_done(sid, mock_task)
        assert sid not in runner._tasks

    def test_done_callback_logs_exception(self, runner: AgentRunner) -> None:
        sid = uuid.uuid4()
        mock_task = MagicMock()
        mock_task.cancelled.return_value = False
        mock_task.exception.return_value = ValueError("boom")
        runner._tasks[sid] = mock_task

        runner._on_done(sid, mock_task)
        assert sid not in runner._tasks

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_returns_false(self, runner: AgentRunner) -> None:
        result = await runner.cancel_session(uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_done_task_returns_false(self, runner: AgentRunner) -> None:
        sid = uuid.uuid4()
        mock_task = MagicMock()
        mock_task.done.return_value = True
        runner._tasks[sid] = mock_task
        result = await runner.cancel_session(sid)
        assert result is False

    @pytest.mark.asyncio
    async def test_shutdown_empty(self, runner: AgentRunner) -> None:
        await runner.shutdown()
        assert len(runner._tasks) == 0
        assert runner._redis is None

    def test_start_session_skips_running(self, runner: AgentRunner) -> None:
        """Starting a session that's already tracked (not done) should skip."""
        sid = uuid.uuid4()
        mock_task = MagicMock()
        mock_task.done.return_value = False
        runner._tasks[sid] = mock_task

        with patch("asyncio.create_task") as mock_create:
            runner.start_session(sid)
            mock_create.assert_not_called()


class TestGetRunner:
    """Tests for the module-level singleton."""

    @pytest.mark.asyncio
    async def test_get_runner_returns_singleton(self) -> None:
        await shutdown_runner()
        r1 = get_runner()
        r2 = get_runner()
        assert r1 is r2
        await shutdown_runner()

    @pytest.mark.asyncio
    async def test_shutdown_runner_clears_singleton(self) -> None:
        await shutdown_runner()
        r1 = get_runner()
        await shutdown_runner()
        r2 = get_runner()
        assert r1 is not r2
        await shutdown_runner()


class TestAgentSessionCreateModel:
    """Tests for the updated AgentSessionCreate schema."""

    def test_create_without_credential(self) -> None:
        data = AgentSessionCreate(user_goal="Test goal")
        assert data.llm_credential_id is None

    def test_create_with_credential(self) -> None:
        cred_id = uuid.uuid4()
        data = AgentSessionCreate(user_goal="Test goal", llm_credential_id=cred_id)
        assert data.llm_credential_id == cred_id


class TestAgentSessionCredentialDB:
    """DB test for credential persistence."""

    def test_session_created_without_credential(self, db: Session) -> None:
        user = User(
            id=uuid.uuid4(),
            email=f"test_runner_cred_{uuid.uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test Runner User",
        )
        db.add(user)
        db.commit()

        session = AgentSession(
            user_id=user.id,
            user_goal="Test goal",
            llm_credential_id=None,
            status=AgentSessionStatus.PENDING,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        assert session.llm_credential_id is None
        assert session.user_goal == "Test goal"
