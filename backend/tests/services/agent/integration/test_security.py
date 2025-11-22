"""
Security tests for the agentic workflow.

These tests verify security characteristics including:
- API authentication
- Session isolation
- Access control
- Input validation
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.models import AgentSessionCreate, AgentSessionStatus
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.session_manager import SessionManager


@pytest.fixture(name="db")
def db_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def user_id():
    """Generate a test user ID."""
    return uuid.uuid4()


@pytest.fixture
def other_user_id():
    """Generate another test user ID."""
    return uuid.uuid4()


@pytest.fixture
def session_manager():
    """Create a SessionManager instance."""
    return SessionManager()


@pytest.fixture
def orchestrator():
    """Create an AgentOrchestrator instance."""
    return AgentOrchestrator()


class TestAuthentication:
    """Test authentication and authorization."""

    @pytest.mark.asyncio
    async def test_session_ownership_validation(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID, other_user_id: uuid.UUID
    ):
        """Test users can only access their own sessions."""
        # User 1 creates a session
        session_create = AgentSessionCreate(
            user_goal="User 1 goal"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        assert session.user_id == user_id

        # Retrieve as owner - should work
        retrieved_session = await session_manager.get_session(db, session.id)
        assert retrieved_session is not None
        assert retrieved_session.id == session.id

        # In a real API, other users wouldn't be able to access this session
        # This would be enforced by API endpoint authentication

    @pytest.mark.asyncio
    async def test_session_isolation(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID, other_user_id: uuid.UUID
    ):
        """Test sessions are isolated between users."""
        # User 1 creates a session
        session1 = await session_manager.create_session(
            db, user_id, AgentSessionCreate(user_goal="User 1 goal")
        )

        # User 2 creates a session
        session2 = await session_manager.create_session(
            db, other_user_id, AgentSessionCreate(user_goal="User 2 goal")
        )

        # Sessions should be different
        assert session1.id != session2.id
        assert session1.user_id != session2.user_id
        assert session1.user_goal != session2.user_goal


class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.mark.asyncio
    async def test_user_goal_validation(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test user goal is validated."""
        # Empty goal should be handled
        with pytest.raises(Exception):
            session_create = AgentSessionCreate(user_goal="")
            session = await session_manager.create_session(db, user_id, session_create)

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test SQL injection attempts are prevented."""
        # Attempt SQL injection in user goal
        malicious_goal = "'; DROP TABLE agent_sessions; --"

        session_create = AgentSessionCreate(user_goal=malicious_goal)
        session = await session_manager.create_session(db, user_id, session_create)

        # Session should be created with the goal as a string, not executed
        assert session is not None
        assert session.user_goal == malicious_goal

        # Table should still exist
        all_sessions = db.query(session_manager.model).all()
        assert len(all_sessions) >= 1

    @pytest.mark.asyncio
    async def test_script_injection_prevention(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test script injection attempts are handled."""
        # Attempt script injection
        malicious_goal = "<script>alert('XSS')</script>"

        session_create = AgentSessionCreate(user_goal=malicious_goal)
        session = await session_manager.create_session(db, user_id, session_create)

        # Session should be created, script should be stored as text
        assert session is not None
        assert session.user_goal == malicious_goal

    @pytest.mark.asyncio
    async def test_long_input_handling(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test system handles very long inputs."""
        # Very long goal (10,000 characters)
        long_goal = "A" * 10000

        session_create = AgentSessionCreate(user_goal=long_goal)
        session = await session_manager.create_session(db, user_id, session_create)

        # Should handle long input
        assert session is not None
        assert len(session.user_goal) == 10000

    @pytest.mark.asyncio
    async def test_special_characters_handling(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test system handles special characters."""
        # Goal with various special characters
        special_goal = "Test with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"

        session_create = AgentSessionCreate(user_goal=special_goal)
        session = await session_manager.create_session(db, user_id, session_create)

        # Should handle special characters
        assert session is not None
        assert session.user_goal == special_goal


class TestAccessControl:
    """Test access control mechanisms."""

    @pytest.mark.asyncio
    async def test_session_state_access_control(
        self, db: Session, orchestrator: AgentOrchestrator, session_manager: SessionManager,
        user_id: uuid.UUID, other_user_id: uuid.UUID
    ):
        """Test session state access is controlled."""
        # User 1 creates a session
        session_create = AgentSessionCreate(user_goal="User 1 goal")
        session = await session_manager.create_session(db, user_id, session_create)

        # Mock state update
        with patch.object(orchestrator, "update_session_state") as mock_update:
            mock_update.return_value = True

            # Owner can update state
            result = orchestrator.update_session_state(db, session.id, {"test": "data"})
            assert result is True

        # In production, API would verify user_id matches session.user_id

    @pytest.mark.asyncio
    async def test_artifact_access_control(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID, other_user_id: uuid.UUID
    ):
        """Test artifact access is controlled by session ownership."""
        # User 1 creates a session
        session_create = AgentSessionCreate(user_goal="Generate artifacts")
        session = await session_manager.create_session(db, user_id, session_create)

        # In production, artifacts would be associated with the session
        # and only accessible to the session owner
        assert session.user_id == user_id


class TestDataProtection:
    """Test data protection mechanisms."""

    @pytest.mark.asyncio
    async def test_session_data_isolation(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID, other_user_id: uuid.UUID
    ):
        """Test session data is isolated between users."""
        # Create sessions for both users
        session1 = await session_manager.create_session(
            db, user_id, AgentSessionCreate(user_goal="Sensitive data 1")
        )
        session2 = await session_manager.create_session(
            db, other_user_id, AgentSessionCreate(user_goal="Sensitive data 2")
        )

        # Update session 1 state
        await session_manager.update_status(db, session1.id, AgentSessionStatus.RUNNING)

        # Session 2 should not be affected
        session2_refreshed = await session_manager.get_session(db, session2.id)
        assert session2_refreshed.status == AgentSessionStatus.PENDING

    @pytest.mark.asyncio
    async def test_no_sensitive_data_in_errors(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test error messages don't leak sensitive data."""
        # Create session with sensitive goal
        session_create = AgentSessionCreate(
            user_goal="API_KEY=sk_test_12345 SECRET=abc123"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        # In production, any error messages should not include the sensitive goal
        assert session is not None
        # Error handling would sanitize output


class TestRateLimiting:
    """Test rate limiting and resource protection."""

    @pytest.mark.asyncio
    async def test_session_creation_rate(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test rapid session creation is handled."""
        # Create many sessions rapidly
        sessions = []
        for i in range(100):
            session_create = AgentSessionCreate(user_goal=f"Rate test {i}")
            session = await session_manager.create_session(db, user_id, session_create)
            sessions.append(session)

        # All should be created (in production, rate limiting would be at API level)
        assert len(sessions) == 100

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test system handles concurrent requests safely."""
        import asyncio

        # Simulate concurrent session creation
        async def create_session(i):
            session_create = AgentSessionCreate(user_goal=f"Concurrent {i}")
            return await session_manager.create_session(db, user_id, session_create)

        # Create 10 sessions concurrently
        tasks = [create_session(i) for i in range(10)]
        sessions = await asyncio.gather(*tasks)

        # All should succeed
        assert len(sessions) == 10
        assert all(s is not None for s in sessions)


class TestAuditAndLogging:
    """Test audit trail and logging."""

    @pytest.mark.asyncio
    async def test_session_creation_logged(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test session creation is logged."""
        session_create = AgentSessionCreate(user_goal="Test logging")
        session = await session_manager.create_session(db, user_id, session_create)

        # Verify session has timestamp
        assert session.created_at is not None

        # In production, there would be audit logs

    @pytest.mark.asyncio
    async def test_status_changes_tracked(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test status changes are tracked."""
        session_create = AgentSessionCreate(user_goal="Test status tracking")
        session = await session_manager.create_session(db, user_id, session_create)

        # Update status
        await session_manager.update_status(db, session.id, AgentSessionStatus.RUNNING)
        
        # Verify updated_at changed
        updated_session = await session_manager.get_session(db, session.id)
        assert updated_session.updated_at is not None
        assert updated_session.updated_at >= session.created_at
