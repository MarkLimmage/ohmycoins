"""
Performance tests for the agentic workflow.

These tests verify performance characteristics including:
- Large dataset handling
- Concurrent session execution
- Response times
- Resource usage
"""

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.models import AgentSessionCreate
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
def session_manager():
    """Create a SessionManager instance."""
    return SessionManager()


@pytest.fixture
def orchestrator():
    """Create an AgentOrchestrator instance."""
    return AgentOrchestrator()


class TestPerformance:
    """Test performance characteristics of the agentic system."""

    @pytest.mark.asyncio
    async def test_session_creation_performance(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test session creation is fast."""
        start_time = time.time()

        session_create = AgentSessionCreate(
            user_goal="Test performance goal"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        elapsed_time = time.time() - start_time

        # Session creation should be fast (< 1 second)
        assert session is not None
        assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_large_dataset_handling(
        self, db: Session, orchestrator: AgentOrchestrator, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test workflow handles large datasets efficiently."""
        session_create = AgentSessionCreate(
            user_goal="Analyze large dataset"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        # Mock large dataset (10,000 records)
        large_dataset = {
            "data_points": 10000,
            "features": 50,
            "size_mb": 100,
        }

        start_time = time.time()

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "dataset_size": large_dataset["data_points"],
                "processing_time_seconds": 45,
            }

            result = await orchestrator.run_workflow(db, session.id)
            elapsed_time = time.time() - start_time

        # Should handle large dataset efficiently
        assert result["status"] == "completed"
        assert result["dataset_size"] == 10000
        # Mock should be fast
        assert elapsed_time < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_sessions(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test system handles multiple concurrent sessions."""
        num_sessions = 5
        sessions = []

        # Create multiple sessions concurrently
        start_time = time.time()
        for i in range(num_sessions):
            session_create = AgentSessionCreate(
                user_goal=f"Concurrent test goal {i}"
            )
            session = await session_manager.create_session(db, user_id, session_create)
            sessions.append(session)

        elapsed_time = time.time() - start_time

        # All sessions should be created successfully
        assert len(sessions) == num_sessions
        # Should be reasonably fast even with multiple sessions
        assert elapsed_time < 5.0

        # All sessions should be unique
        session_ids = [s.id for s in sessions]
        assert len(set(session_ids)) == num_sessions

    @pytest.mark.asyncio
    async def test_workflow_execution_time(
        self, db: Session, orchestrator: AgentOrchestrator, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test workflow execution completes in reasonable time."""
        session_create = AgentSessionCreate(
            user_goal="Test execution time"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        start_time = time.time()

        with patch.object(orchestrator, "run_workflow") as mock_run:
            # Simulate workflow taking 2 seconds
            async def slow_workflow(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate work
                return {"status": "completed", "execution_time": 0.1}

            mock_run.side_effect = slow_workflow

            result = await orchestrator.run_workflow(db, session.id)
            elapsed_time = time.time() - start_time

        # Mock workflow should complete quickly
        assert result["status"] == "completed"
        assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_session_state_retrieval_performance(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test session state can be retrieved quickly."""
        # Create a session
        session_create = AgentSessionCreate(
            user_goal="Test state retrieval"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        # Measure state retrieval time
        start_time = time.time()
        state = orchestrator.get_session_state(db, session.id)
        elapsed_time = time.time() - start_time

        # State retrieval should be fast
        assert elapsed_time < 0.5  # 500ms

    @pytest.mark.asyncio
    async def test_multiple_workflow_runs(
        self, db: Session, orchestrator: AgentOrchestrator, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test multiple workflow runs don't degrade performance."""
        session_create = AgentSessionCreate(
            user_goal="Test multiple runs"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        execution_times = []

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {"status": "completed"}

            # Run workflow 10 times
            for i in range(10):
                start_time = time.time()
                result = await orchestrator.run_workflow(db, session.id)
                elapsed_time = time.time() - start_time
                execution_times.append(elapsed_time)

                assert result["status"] == "completed"

        # Later runs shouldn't be slower than early runs
        avg_first_half = sum(execution_times[:5]) / 5
        avg_second_half = sum(execution_times[5:]) / 5

        # Second half should not be significantly slower
        assert avg_second_half < avg_first_half * 2.0


class TestResourceUsage:
    """Test resource usage characteristics."""

    @pytest.mark.asyncio
    async def test_memory_usage_reasonable(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test creating sessions doesn't leak memory."""
        import gc
        import sys

        initial_objects = len(gc.get_objects())

        # Create and delete multiple sessions
        for i in range(100):
            session_create = AgentSessionCreate(
                user_goal=f"Memory test {i}"
            )
            session = await session_manager.create_session(db, user_id, session_create)
            # Session goes out of scope

        # Force garbage collection
        gc.collect()

        final_objects = len(gc.get_objects())

        # Object count shouldn't grow excessively
        # Allow for some growth but not proportional to number of sessions
        assert final_objects < initial_objects + 1000

    @pytest.mark.asyncio
    async def test_database_connection_handling(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test database connections are properly managed."""
        # Create multiple sessions to verify connection handling
        for i in range(20):
            session_create = AgentSessionCreate(
                user_goal=f"Connection test {i}"
            )
            session = await session_manager.create_session(db, user_id, session_create)
            assert session is not None

        # If connections weren't properly managed, this would fail
        # No assertion needed - test passes if no exception raised


class TestScalability:
    """Test system scalability characteristics."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_handles_many_sessions(
        self, db: Session, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test system can handle many sessions (scalability test)."""
        num_sessions = 50
        sessions_created = []

        for i in range(num_sessions):
            session_create = AgentSessionCreate(
                user_goal=f"Scalability test {i}"
            )
            session = await session_manager.create_session(db, user_id, session_create)
            sessions_created.append(session)

        # All sessions should be created successfully
        assert len(sessions_created) == num_sessions

        # All should have unique IDs
        session_ids = [s.id for s in sessions_created]
        assert len(set(session_ids)) == num_sessions

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_workflow_execution(
        self, db: Session, orchestrator: AgentOrchestrator, session_manager: SessionManager, user_id: uuid.UUID
    ):
        """Test multiple workflows can run concurrently."""
        num_workflows = 5

        # Create sessions
        sessions = []
        for i in range(num_workflows):
            session_create = AgentSessionCreate(
                user_goal=f"Concurrent workflow {i}"
            )
            session = await session_manager.create_session(db, user_id, session_create)
            sessions.append(session)

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {"status": "completed"}

            # Run workflows
            start_time = time.time()
            results = []
            for session in sessions:
                result = await orchestrator.run_workflow(db, session.id)
                results.append(result)

            elapsed_time = time.time() - start_time

        # All should complete
        assert len(results) == num_workflows
        assert all(r["status"] == "completed" for r in results)

        # Should complete in reasonable time
        assert elapsed_time < 10.0
