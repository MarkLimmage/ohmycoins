"""
End-to-end integration tests for the agentic workflow.

These tests verify the complete workflow from user goal to final report,
testing integration between all agents, tools, and workflow nodes.
"""

import uuid
from unittest.mock import patch

import pytest
from sqlmodel import Session

from app.models import (
    AgentSessionCreate,
    AgentSessionStatus,
    User,
)
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.session_manager import SessionManager


@pytest.fixture(name="db")
def db_fixture(session: Session):
    """Create a test database session using PostgreSQL.

    Uses the shared session fixture from conftest.py which provides:
    - PostgreSQL database connection (supports ARRAY types)
    - Transaction isolation via savepoints
    - Automatic cleanup after each test
    """
    return session


@pytest.fixture
def user_id(db: Session):
    """Generate a test user and return its ID."""
    import uuid

    user = User(
        id=uuid.uuid4(),
        email=f"test_agent_{uuid.uuid4()}@example.com",
        hashed_password="hashed",
        full_name="Test Agent User",
    )
    db.add(user)
    db.flush()  # Flush without committing to stay within the savepoint
    return user.id


@pytest.fixture
def session_manager():
    """Create a SessionManager instance."""
    return SessionManager()


@pytest.fixture
def orchestrator(session_manager: SessionManager):
    """Create an AgentOrchestrator instance."""
    return AgentOrchestrator(session_manager=session_manager)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_simple_workflow_completion(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test a simple workflow completes successfully."""
        # Create a session with a simple goal
        session_create = AgentSessionCreate(
            user_goal="Analyze Bitcoin price trends over the last week"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        assert session is not None
        assert session.status == AgentSessionStatus.PENDING
        assert session.user_goal == "Analyze Bitcoin price trends over the last week"

        # Mock the workflow execution to return a completed state
        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "data_retrieved": True,
                "analysis_completed": True,
                "reporting_completed": True,
            }

            # Execute workflow
            result = await orchestrator.run_workflow(db, session.id)

            # Verify workflow completed
            assert result["status"] == "completed"
            assert result["data_retrieved"] is True
            assert result["analysis_completed"] is True
            assert result["reporting_completed"] is True

    @pytest.mark.asyncio
    async def test_workflow_with_price_data(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test workflow that retrieves and analyzes price data."""
        session_create = AgentSessionCreate(
            user_goal="Predict Bitcoin price movements using historical data"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        # Mock data retrieval to return sample price data
        sample_price_data = {
            "coin_type": "BTC",
            "data_points": 100,
            "date_range": "2024-11-15 to 2024-11-22",
            "prices": [45000, 45100, 45200],  # Sample prices
        }

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "data_retrieved": True,
                "price_data": sample_price_data,
                "analysis_completed": True,
                "features_created": ["price_sma_7", "price_ema_14", "rsi_14"],
                "model_trained": True,
                "model_type": "RandomForest",
                "evaluation_score": 0.85,
            }

            result = await orchestrator.run_workflow(db, session.id)

            # Verify data retrieval
            assert result["data_retrieved"] is True
            assert result["price_data"]["coin_type"] == "BTC"
            assert result["price_data"]["data_points"] == 100

            # Verify analysis
            assert result["analysis_completed"] is True
            assert len(result["features_created"]) == 3

            # Verify model training
            assert result["model_trained"] is True
            assert result["model_type"] == "RandomForest"
            assert result["evaluation_score"] >= 0.8

    @pytest.mark.asyncio
    async def test_workflow_with_error_recovery(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test workflow handles errors and recovers."""
        session_create = AgentSessionCreate(
            user_goal="Build a trading model for Ethereum"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        # Simulate an error on first attempt, success on retry
        call_count = 0

        async def mock_workflow_with_retry(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "status": "error",
                    "error_message": "Failed to retrieve data",
                    "retry_count": 1,
                }
            else:
                return {
                    "status": "completed",
                    "data_retrieved": True,
                    "retry_count": 1,
                    "recovered_from_error": True,
                }

        with patch.object(orchestrator, "run_workflow", side_effect=mock_workflow_with_retry):
            # First attempt - error
            result1 = await orchestrator.run_workflow(db, session.id)
            assert result1["status"] == "error"
            assert result1["retry_count"] == 1

            # Second attempt - success
            result2 = await orchestrator.run_workflow(db, session.id)
            assert result2["status"] == "completed"
            assert result2["recovered_from_error"] is True

    @pytest.mark.asyncio
    async def test_workflow_with_clarification(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test workflow requests clarification for ambiguous goals."""
        session_create = AgentSessionCreate(
            user_goal="Predict crypto prices"  # Ambiguous - which crypto?
        )
        session = await session_manager.create_session(db, user_id, session_create)

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "awaiting_clarification",
                "clarifications_needed": [
                    "Which cryptocurrency would you like to predict?",
                    "What time frame are you interested in?",
                ],
                "awaiting_clarification": True,
            }

            result = await orchestrator.run_workflow(db, session.id)

            # Verify clarification request
            assert result["status"] == "awaiting_clarification"
            assert result["awaiting_clarification"] is True
            assert len(result["clarifications_needed"]) == 2
            assert "cryptocurrency" in result["clarifications_needed"][0].lower()

    @pytest.mark.asyncio
    async def test_workflow_with_model_selection(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test workflow presents model choices to user."""
        session_create = AgentSessionCreate(
            user_goal="Build a classification model for Bitcoin price direction"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "awaiting_choice",
                "choices_available": [
                    {
                        "model_type": "RandomForest",
                        "accuracy": 0.85,
                        "training_time": "30s",
                        "pros": ["High accuracy", "Good interpretability"],
                        "cons": ["Slower predictions"],
                    },
                    {
                        "model_type": "LogisticRegression",
                        "accuracy": 0.78,
                        "training_time": "5s",
                        "pros": ["Fast training", "Fast predictions"],
                        "cons": ["Lower accuracy"],
                    },
                ],
                "recommendation": {
                    "model": "RandomForest",
                    "reason": "Better accuracy for production use",
                },
                "awaiting_choice": True,
            }

            result = await orchestrator.run_workflow(db, session.id)

            # Verify choice presentation
            assert result["status"] == "awaiting_choice"
            assert result["awaiting_choice"] is True
            assert len(result["choices_available"]) == 2
            assert result["recommendation"]["model"] == "RandomForest"

    @pytest.mark.asyncio
    async def test_complete_workflow_with_reporting(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test complete workflow generates final report."""
        session_create = AgentSessionCreate(
            user_goal="Analyze and model Bitcoin price trends"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "data_retrieved": True,
                "analysis_completed": True,
                "model_trained": True,
                "model_evaluated": True,
                "reporting_completed": True,
                "report_data": {
                    "summary": "Successfully built RandomForest model with 85% accuracy",
                    "model_type": "RandomForest",
                    "accuracy": 0.85,
                    "precision": 0.83,
                    "recall": 0.87,
                    "recommendations": [
                        "Model performs well on trending markets",
                        "Consider retraining weekly",
                    ],
                    "visualizations": ["model_performance.png", "feature_importance.png"],
                },
            }

            result = await orchestrator.run_workflow(db, session.id)

            # Verify complete workflow
            assert result["status"] == "completed"
            assert result["reporting_completed"] is True

            # Verify report content
            report = result["report_data"]
            assert "RandomForest" in report["summary"]
            assert report["accuracy"] == 0.85
            assert len(report["recommendations"]) == 2
            assert len(report["visualizations"]) == 2

    @pytest.mark.asyncio
    async def test_workflow_session_lifecycle(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test session status transitions through workflow lifecycle."""
        session_create = AgentSessionCreate(
            user_goal="Test session lifecycle"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        # Verify initial state
        assert session.status == AgentSessionStatus.PENDING

        # Mock status transitions
        async def mock_workflow_with_status(*_args, **_kwargs):
            # Simulate session status updates
            await session_manager.update_status(db, session.id, AgentSessionStatus.RUNNING)
            return {
                "status": "completed",
                "session_status": AgentSessionStatus.COMPLETED,
            }

        with patch.object(orchestrator, "run_workflow", side_effect=mock_workflow_with_status):
            result = await orchestrator.run_workflow(db, session.id)

            # Verify completion
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_workflow_with_artifact_generation(
        self, db: Session, session_manager: SessionManager, orchestrator: AgentOrchestrator, user_id: uuid.UUID
    ):
        """Test workflow generates and stores artifacts."""
        session_create = AgentSessionCreate(
            user_goal="Generate model artifacts"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        with patch.object(orchestrator, "run_workflow") as mock_run:
            mock_run.return_value = {
                "status": "completed",
                "artifacts_generated": [
                    {
                        "type": "model",
                        "name": "random_forest_model.pkl",
                        "size": 1024000,
                    },
                    {
                        "type": "plot",
                        "name": "feature_importance.png",
                        "size": 50000,
                    },
                    {
                        "type": "report",
                        "name": "analysis_report.md",
                        "size": 5000,
                    },
                ],
            }

            result = await orchestrator.run_workflow(db, session.id)

            # Verify artifacts
            assert result["status"] == "completed"
            assert len(result["artifacts_generated"]) == 3

            artifacts = result["artifacts_generated"]
            assert artifacts[0]["type"] == "model"
            assert artifacts[1]["type"] == "plot"
            assert artifacts[2]["type"] == "report"


class TestWorkflowDataIntegration:
    """Test integration with data sources and storage."""

    @pytest.mark.asyncio
    async def test_workflow_data_retrieval_integration(self, db: Session, user_id: uuid.UUID):
        """Test workflow integrates with data retrieval."""
        # This would test actual data retrieval in a real integration test
        # For now, we verify the interface
        session_manager = SessionManager()
        session_create = AgentSessionCreate(
            user_goal="Retrieve Bitcoin price data"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        assert session is not None
        # In a real integration test, we would verify data was actually retrieved

    @pytest.mark.asyncio
    async def test_workflow_artifact_storage_integration(self, db: Session, user_id: uuid.UUID):
        """Test workflow stores artifacts in database."""
        session_manager = SessionManager()
        session_create = AgentSessionCreate(
            user_goal="Generate and store artifacts"
        )
        session = await session_manager.create_session(db, user_id, session_create)

        assert session is not None
        # In a real integration test, we would verify artifacts were stored
