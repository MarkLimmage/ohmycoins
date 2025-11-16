"""
Tests for the SessionManager.

These tests verify the core session management functionality including
session creation, status updates, and state persistence.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.models import AgentSession, AgentSessionCreate, AgentSessionStatus
from app.services.agent.session_manager import SessionManager


@pytest.fixture(name="db")
def db_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Import all models to ensure they're registered
    from app.models import User, AgentSession, AgentSessionMessage, AgentArtifact
    
    # Create tables
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture
def session_manager():
    """Create a SessionManager instance."""
    return SessionManager()


@pytest.fixture
def user_id():
    """Generate a test user ID."""
    return uuid.uuid4()


@pytest.mark.asyncio
async def test_create_session(db: Session, session_manager: SessionManager, user_id: uuid.UUID):
    """Test creating a new agent session."""
    session_data = AgentSessionCreate(
        user_goal="Predict Bitcoin price movements"
    )
    
    session = await session_manager.create_session(db, user_id, session_data)
    
    assert session.id is not None
    assert session.user_id == user_id
    assert session.user_goal == "Predict Bitcoin price movements"
    assert session.status == AgentSessionStatus.PENDING
    assert session.error_message is None
    assert session.result_summary is None
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)


@pytest.mark.asyncio
async def test_get_session(db: Session, session_manager: SessionManager, user_id: uuid.UUID):
    """Test retrieving a session by ID."""
    # Create a session first
    session_data = AgentSessionCreate(user_goal="Test goal")
    created_session = await session_manager.create_session(db, user_id, session_data)
    
    # Retrieve the session
    retrieved_session = await session_manager.get_session(db, created_session.id)
    
    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.user_goal == "Test goal"


@pytest.mark.asyncio
async def test_get_nonexistent_session(db: Session, session_manager: SessionManager):
    """Test retrieving a session that doesn't exist."""
    nonexistent_id = uuid.uuid4()
    session = await session_manager.get_session(db, nonexistent_id)
    assert session is None


@pytest.mark.asyncio
async def test_update_session_status(db: Session, session_manager: SessionManager, user_id: uuid.UUID):
    """Test updating session status."""
    # Create a session
    session_data = AgentSessionCreate(user_goal="Test goal")
    session = await session_manager.create_session(db, user_id, session_data)
    
    # Update status to running
    await session_manager.update_session_status(
        db, session.id, AgentSessionStatus.RUNNING
    )
    
    # Verify update
    updated_session = await session_manager.get_session(db, session.id)
    assert updated_session is not None
    assert updated_session.status == AgentSessionStatus.RUNNING
    assert updated_session.completed_at is None


@pytest.mark.asyncio
async def test_update_session_status_with_error(db: Session, session_manager: SessionManager, user_id: uuid.UUID):
    """Test updating session status with error message."""
    # Create a session
    session_data = AgentSessionCreate(user_goal="Test goal")
    session = await session_manager.create_session(db, user_id, session_data)
    
    # Update status to failed with error
    error_msg = "Test error occurred"
    await session_manager.update_session_status(
        db, session.id, AgentSessionStatus.FAILED, error_message=error_msg
    )
    
    # Verify update
    updated_session = await session_manager.get_session(db, session.id)
    assert updated_session is not None
    assert updated_session.status == AgentSessionStatus.FAILED
    assert updated_session.error_message == error_msg
    assert updated_session.completed_at is not None


@pytest.mark.asyncio
async def test_update_session_status_with_result(db: Session, session_manager: SessionManager, user_id: uuid.UUID):
    """Test updating session status with result summary."""
    # Create a session
    session_data = AgentSessionCreate(user_goal="Test goal")
    session = await session_manager.create_session(db, user_id, session_data)
    
    # Update status to completed with result
    result_summary = "Model trained successfully with 95% accuracy"
    await session_manager.update_session_status(
        db, session.id, AgentSessionStatus.COMPLETED, result_summary=result_summary
    )
    
    # Verify update
    updated_session = await session_manager.get_session(db, session.id)
    assert updated_session is not None
    assert updated_session.status == AgentSessionStatus.COMPLETED
    assert updated_session.result_summary == result_summary
    assert updated_session.completed_at is not None


@pytest.mark.asyncio
async def test_add_message(db: Session, session_manager: SessionManager, user_id: uuid.UUID):
    """Test adding a message to a session."""
    # Create a session
    session_data = AgentSessionCreate(user_goal="Test goal")
    session = await session_manager.create_session(db, user_id, session_data)
    
    # Add a message
    message = await session_manager.add_message(
        db,
        session.id,
        role="user",
        content="This is a test message",
        agent_name="TestAgent",
    )
    
    assert message.id is not None
    assert message.session_id == session.id
    assert message.role == "user"
    assert message.content == "This is a test message"
    assert message.agent_name == "TestAgent"
    assert isinstance(message.created_at, datetime)


@pytest.mark.asyncio
async def test_session_state_persistence(session_manager: SessionManager):
    """Test saving and retrieving session state from Redis."""
    session_id = uuid.uuid4()
    test_state = {
        "session_id": str(session_id),
        "current_step": "data_retrieval",
        "iteration": 3,
        "data": {"test": "value"},
    }
    
    # Mock Redis client
    mock_redis = AsyncMock()
    session_manager.redis_client = mock_redis
    
    # Test saving state
    await session_manager.save_session_state(session_id, test_state)
    mock_redis.setex.assert_called_once()
    
    # Test retrieving state
    import json
    mock_redis.get.return_value = json.dumps(test_state)
    retrieved_state = await session_manager.get_session_state(session_id)
    
    assert retrieved_state == test_state
    mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_delete_session_state(session_manager: SessionManager):
    """Test deleting session state from Redis."""
    session_id = uuid.uuid4()
    
    # Mock Redis client
    mock_redis = AsyncMock()
    session_manager.redis_client = mock_redis
    
    # Test deleting state
    await session_manager.delete_session_state(session_id)
    mock_redis.delete.assert_called_once()
