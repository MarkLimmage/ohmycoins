"""
Tests for ReportingAgent - Week 11 Implementation

Tests for the ReportingAgent class and its workflow integration.
"""

import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

from app.services.agent.agents.reporting import ReportingAgent


@pytest.fixture
def temp_artifacts_dir():
    """Create and cleanup temporary artifacts directory."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def reporting_agent(temp_artifacts_dir):
    """Create ReportingAgent instance with temp directory."""
    return ReportingAgent(artifacts_dir=str(temp_artifacts_dir))


@pytest.fixture
def sample_state_complete():
    """Sample complete workflow state."""
    return {
        "session_id": str(uuid.uuid4()),
        "user_goal": "Predict BTC price movement using technical indicators",
        "analysis_results": {
            "exploratory_analysis": {
                "price_eda": {
                    "record_count": 1000,
                    "date_range": "2024-01-01 to 2024-02-01",
                    "coins": ["BTC", "ETH"],
                }
            },
            "technical_indicators": {
                "columns": ["timestamp", "close", "sma_20", "ema_20", "rsi"],
            },
            "sentiment_analysis": {
                "overall_sentiment": "Bullish",
                "avg_sentiment": 0.72,
            },
        },
        "model_results": {
            "trained_models": [
                {"name": "RandomForestModel_1", "algorithm": "RandomForest"},
                {"name": "LogisticRegressionModel_1", "algorithm": "LogisticRegression"},
            ]
        },
        "evaluation_results": {
            "evaluations": [
                {
                    "model_name": "RandomForestModel_1",
                    "algorithm": "RandomForest",
                    "metrics": {
                        "accuracy": 0.87,
                        "precision": 0.85,
                        "recall": 0.89,
                        "f1": 0.87,
                    },
                    "feature_importance": {
                        "sma_20": 0.35,
                        "ema_20": 0.25,
                        "rsi": 0.20,
                    },
                    "confusion_matrix": [[45, 5], [3, 47]],
                },
            ]
        },
    }


@pytest.fixture
def sample_state_minimal():
    """Sample minimal workflow state."""
    return {
        "session_id": str(uuid.uuid4()),
        "user_goal": "Test minimal workflow",
        "analysis_results": {},
        "model_results": {},
        "evaluation_results": {},
    }


class TestReportingAgentInitialization:
    """Tests for ReportingAgent initialization."""

    def test_init_with_default_dir(self):
        """Test initialization with default artifacts directory."""
        agent = ReportingAgent()

        assert agent.name == "ReportingAgent"
        assert agent.description == "Generates comprehensive reports and visualizations from workflow results"
        assert agent.artifacts_dir == Path("/tmp/agent_artifacts")

    def test_init_with_custom_dir(self, temp_artifacts_dir):
        """Test initialization with custom artifacts directory."""
        agent = ReportingAgent(artifacts_dir=str(temp_artifacts_dir))

        assert agent.artifacts_dir == temp_artifacts_dir
        assert temp_artifacts_dir.exists()


class TestReportingAgentExecute:
    """Tests for ReportingAgent execute method."""

    @pytest.mark.asyncio
    async def test_execute_complete_workflow(self, reporting_agent, sample_state_complete, temp_artifacts_dir):
        """Test execute with complete workflow results."""
        state = await reporting_agent.execute(sample_state_complete)

        # Check state updates
        assert state["reporting_completed"] is True
        assert state["error"] is None
        assert "reporting_results" in state

        # Check reporting results structure
        results = state["reporting_results"]
        assert "summary" in results
        assert "comparison_report" in results
        assert "recommendations" in results
        assert "visualizations" in results
        assert "artifacts_dir" in results
        assert "timestamp" in results
        assert "complete_report_path" in results

        # Check files were created
        session_dir = temp_artifacts_dir / sample_state_complete["session_id"]
        assert session_dir.exists()
        assert (session_dir / "summary.md").exists()
        assert (session_dir / "model_comparison.md").exists()
        assert (session_dir / "recommendations.md").exists()
        assert (session_dir / "complete_report.md").exists()

        # Check summary content
        assert "Agent Workflow Summary" in results["summary"]
        assert "Predict BTC price movement" in results["summary"]

    @pytest.mark.asyncio
    async def test_execute_minimal_workflow(self, reporting_agent, sample_state_minimal, temp_artifacts_dir):
        """Test execute with minimal workflow results."""
        state = await reporting_agent.execute(sample_state_minimal)

        # Check state updates
        assert state["reporting_completed"] is True
        assert state["error"] is None
        assert "reporting_results" in state

        # Check files were created even with minimal data
        session_dir = temp_artifacts_dir / sample_state_minimal["session_id"]
        assert session_dir.exists()
        assert (session_dir / "summary.md").exists()
        assert (session_dir / "complete_report.md").exists()

    @pytest.mark.asyncio
    async def test_execute_creates_session_dir(self, reporting_agent, sample_state_complete, temp_artifacts_dir):
        """Test that execute creates session-specific directory."""
        session_id = sample_state_complete["session_id"]

        state = await reporting_agent.execute(sample_state_complete)

        session_dir = temp_artifacts_dir / session_id
        assert session_dir.exists()
        assert session_dir.is_dir()

    @pytest.mark.asyncio
    async def test_execute_adds_message(self, reporting_agent, sample_state_complete):
        """Test that execute adds message to state."""
        state = await reporting_agent.execute(sample_state_complete)

        assert "messages" in state
        assert len(state["messages"]) > 0

        last_message = state["messages"][-1]
        assert last_message["role"] == "agent"
        assert last_message["agent_name"] == "ReportingAgent"
        assert "Report generation completed" in last_message["content"]
        assert "timestamp" in last_message

    @pytest.mark.asyncio
    async def test_execute_with_existing_messages(self, reporting_agent, sample_state_complete):
        """Test execute preserves existing messages."""
        sample_state_complete["messages"] = [
            {"role": "user", "content": "Test message"}
        ]

        state = await reporting_agent.execute(sample_state_complete)

        assert len(state["messages"]) == 2
        assert state["messages"][0]["content"] == "Test message"

    @pytest.mark.asyncio
    async def test_execute_recommendations_generated(self, reporting_agent, sample_state_complete):
        """Test that recommendations are generated."""
        state = await reporting_agent.execute(sample_state_complete)

        results = state["reporting_results"]
        assert len(results["recommendations"]) > 0
        assert isinstance(results["recommendations"], list)

    @pytest.mark.asyncio
    async def test_execute_visualizations_created(self, reporting_agent, sample_state_complete, temp_artifacts_dir):
        """Test that visualizations are created."""
        state = await reporting_agent.execute(sample_state_complete)

        results = state["reporting_results"]
        session_dir = temp_artifacts_dir / sample_state_complete["session_id"]

        # Check visualization files exist
        for plot_name, plot_path in results["visualizations"].items():
            assert Path(plot_path).exists()
            assert Path(plot_path).suffix == ".png"

    @pytest.mark.asyncio
    async def test_execute_complete_report_structure(self, reporting_agent, sample_state_complete, temp_artifacts_dir):
        """Test complete report has proper structure."""
        state = await reporting_agent.execute(sample_state_complete)

        session_dir = temp_artifacts_dir / sample_state_complete["session_id"]
        complete_report_path = session_dir / "complete_report.md"

        assert complete_report_path.exists()

        report_content = complete_report_path.read_text()
        assert "Oh My Coins - Agentic Workflow Complete Report" in report_content
        assert "Agent Workflow Summary" in report_content
        assert "Model Comparison Report" in report_content
        assert "Recommendations" in report_content


class TestReportingAgentErrorHandling:
    """Tests for ReportingAgent error handling."""

    @pytest.mark.asyncio
    async def test_execute_with_invalid_state(self, reporting_agent):
        """Test execute handles invalid state gracefully."""
        # State without required keys
        invalid_state = {}

        state = await reporting_agent.execute(invalid_state)

        # Should fail gracefully with error
        assert state["report_generated"] is False
        assert state["error"] is not None
        assert "No results available" in state["error"]


class TestCreateCompleteReport:
    """Tests for _create_complete_report method."""

    def test_create_complete_report_all_components(self, reporting_agent):
        """Test complete report with all components."""
        summary = "Test Summary"
        comparison = "Test Comparison"
        recommendations = ["Rec 1", "Rec 2"]
        visualizations = {
            "model_comparison": "/tmp/model_comparison.png",
            "feature_importance": "/tmp/feature_importance.png",
        }

        report = reporting_agent._create_complete_report(
            summary=summary,
            comparison_report=comparison,
            recommendations=recommendations,
            visualizations=visualizations,
        )

        assert "Oh My Coins - Agentic Workflow Complete Report" in report
        assert "Test Summary" in report
        assert "Test Comparison" in report
        assert "Rec 1" in report
        assert "Rec 2" in report
        assert "model_comparison" in report.lower()
        assert "feature_importance" in report.lower()

    def test_create_complete_report_minimal(self, reporting_agent):
        """Test complete report with minimal components."""
        report = reporting_agent._create_complete_report(
            summary="Minimal",
            comparison_report="",
            recommendations=[],
            visualizations={},
        )

        assert "Oh My Coins - Agentic Workflow Complete Report" in report
        assert "Minimal" in report
        assert "About This Report" in report
