"""
Tests for ReportingAgent.

Week 11 tests: Testing report generation, visualizations, and recommendations.
"""

import pytest

from app.services.agent.agents.reporting import ReportingAgent


@pytest.fixture
def reporting_agent():
    """Create a ReportingAgent instance for testing."""
    return ReportingAgent()


@pytest.fixture
def sample_state_with_results():
    """Sample state with evaluation results."""
    return {
        "user_goal": "Predict BTC price movement",
        "evaluation_results": {
            "primary_model": {
                "accuracy": 0.85,
                "f1_score": 0.82,
                "precision": 0.88,
                "recall": 0.77,
            },
            "secondary_model": {
                "accuracy": 0.78,
                "f1_score": 0.75,
                "precision": 0.80,
                "recall": 0.71,
            },
        },
        "trained_models": {
            "primary_model": {
                "algorithm": "RandomForest",
                "task_type": "classification",
            },
            "secondary_model": {
                "algorithm": "LogisticRegression",
                "task_type": "classification",
            },
        },
        "analysis_results": {
            "feature_count": 10,
            "record_count": 1000,
            "insights": ["Strong correlation with volume", "Price momentum matters"],
        },
        "messages": [],
    }


@pytest.fixture
def sample_state_minimal():
    """Minimal sample state."""
    return {
        "user_goal": "Test goal",
        "evaluation_results": {
            "model": {"accuracy": 0.7},
        },
        "trained_models": {
            "model": {"algorithm": "SVM"},
        },
        "messages": [],
    }


class TestReportingAgentInitialization:
    """Tests for ReportingAgent initialization."""

    def test_agent_name(self, reporting_agent):
        """Test agent has correct name."""
        assert reporting_agent.name == "ReportingAgent"

    def test_agent_description(self, reporting_agent):
        """Test agent has description."""
        assert "report" in reporting_agent.description.lower()


class TestReportingAgentExecution:
    """Tests for ReportingAgent execution."""

    @pytest.mark.asyncio
    async def test_execute_with_results(self, reporting_agent, sample_state_with_results):
        """Test execution with full results."""
        result = await reporting_agent.execute(sample_state_with_results)

        assert result["report_generated"] is True
        assert result["error"] is None
        assert "report_data" in result

        # Check report data structure
        report_data = result["report_data"]
        assert "summary" in report_data
        assert "recommendations" in report_data
        assert "visualizations" in report_data
        assert report_data["summary"] is not None
        assert isinstance(report_data["recommendations"], list)
        assert len(report_data["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_execute_with_minimal_state(self, reporting_agent, sample_state_minimal):
        """Test execution with minimal state."""
        result = await reporting_agent.execute(sample_state_minimal)

        assert result["report_generated"] is True
        assert result["error"] is None
        assert "report_data" in result

    @pytest.mark.asyncio
    async def test_execute_no_results(self, reporting_agent):
        """Test execution with no results."""
        state = {
            "user_goal": "Test",
            "messages": [],
        }

        result = await reporting_agent.execute(state)

        assert result["report_generated"] is False
        assert result["error"] is not None
        assert "No results available" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_adds_message(self, reporting_agent, sample_state_with_results):
        """Test that execution adds a message to state."""
        result = await reporting_agent.execute(sample_state_with_results)

        assert "messages" in result
        assert len(result["messages"]) > 0

        # Check last message is from reporting agent
        last_message = result["messages"][-1]
        assert last_message["agent_name"] == "ReportingAgent"
        assert "role" in last_message
        assert "content" in last_message


class TestReportGeneration:
    """Tests for report generation functionality."""

    @pytest.mark.asyncio
    async def test_summary_generated(self, reporting_agent, sample_state_with_results):
        """Test that summary is generated."""
        result = await reporting_agent.execute(sample_state_with_results)

        report_data = result["report_data"]
        assert report_data["summary"] is not None
        assert len(report_data["summary"]) > 0

        # Check summary contains key information
        summary = report_data["summary"]
        assert "Goal" in summary or "goal" in summary.lower()

    @pytest.mark.asyncio
    async def test_comparison_generated_for_multiple_models(
        self, reporting_agent, sample_state_with_results
    ):
        """Test that comparison is generated when multiple models exist."""
        result = await reporting_agent.execute(sample_state_with_results)

        report_data = result["report_data"]
        assert report_data["comparison"] is not None
        assert len(report_data["comparison"]) > 0

    @pytest.mark.asyncio
    async def test_no_comparison_for_single_model(self, reporting_agent, sample_state_minimal):
        """Test that comparison is skipped for single model."""
        result = await reporting_agent.execute(sample_state_minimal)

        report_data = result["report_data"]
        # Comparison might be None or a message indicating single model
        assert report_data["comparison"] is None or "one model" in report_data["comparison"].lower()

    @pytest.mark.asyncio
    async def test_recommendations_generated(self, reporting_agent, sample_state_with_results):
        """Test that recommendations are generated."""
        result = await reporting_agent.execute(sample_state_with_results)

        report_data = result["report_data"]
        assert report_data["recommendations"] is not None
        assert isinstance(report_data["recommendations"], list)
        assert len(report_data["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_visualizations_created(self, reporting_agent, sample_state_with_results):
        """Test that visualizations are created."""
        result = await reporting_agent.execute(sample_state_with_results)

        report_data = result["report_data"]
        assert "visualizations" in report_data
        assert isinstance(report_data["visualizations"], list)
        # Visualizations might be empty if no data to visualize


class TestReportFormatting:
    """Tests for report formatting methods."""

    @pytest.mark.skip(reason="Format methods not yet implemented")
    def test_format_report_as_markdown(self, reporting_agent):
        """Test Markdown formatting."""
        report_data = {
            "summary": "Test summary",
            "comparison": "Test comparison",
            "recommendations": ["Rec 1", "Rec 2"],
            "visualizations": [
                {"title": "Chart 1", "file_path": "/tmp/chart1.png"},
            ],
        }

        markdown = reporting_agent._format_report_as_markdown(report_data)

        assert "## Summary" in markdown
        assert "Test summary" in markdown
        assert "## Model Comparison" in markdown
        assert "## Recommendations" in markdown
        assert "Rec 1" in markdown
        assert "Rec 2" in markdown
        assert "## Visualizations" in markdown

    @pytest.mark.skip(reason="Format methods not yet implemented")
    def test_format_report_as_html(self, reporting_agent):
        """Test HTML formatting."""
        report_data = {
            "summary": "Test summary",
            "comparison": "Test comparison",
            "recommendations": ["Rec 1", "Rec 2"],
            "visualizations": [
                {"title": "Chart 1", "file_path": "/tmp/chart1.png"},
            ],
        }

        html = reporting_agent._format_report_as_html(report_data)

        assert "<!DOCTYPE html>" in html
        assert "<h2>Summary</h2>" in html
        assert "Test summary" in html
        assert "<h2>Recommendations</h2>" in html
        assert "<li" in html
        assert "Rec 1" in html
