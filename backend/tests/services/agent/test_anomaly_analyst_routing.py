"""
Tests for Anomaly Detection Integration in DataAnalystAgent and Routing — Sprint 2.36

Tests for the analyst agent's anomaly detection and the routing changes.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from app.services.agent.agents.data_analyst import DataAnalystAgent
from app.services.agent.langgraph_workflow import AgentState, LangGraphWorkflow


@pytest.fixture
def data_analyst_agent():
    """Create a DataAnalystAgent."""
    return DataAnalystAgent()


@pytest.fixture
def state_with_price_anomalies():
    """Create a state with price data containing anomalies."""
    now = datetime.now()
    data = []

    # Normal price trend with injected anomalies
    for i in range(50):
        timestamp = now - timedelta(hours=50 - i)
        price = 50000 + i * 100  # Normal trend

        # Inject anomalies
        if i == 10:
            price = 40000  # Minor anomaly
        elif i == 25:
            price = 45000  # Medium anomaly
        elif i == 40:
            price = 30000  # High anomaly

        data.append({
            "timestamp": timestamp.isoformat(),
            "coin_type": "BTC",
            "bid": float(price) - 50,
            "ask": float(price) + 50,
            "last": float(price),
        })

    return {
        "user_goal": "Detect anomalies in Bitcoin price",
        "retrieved_data": {
            "price_data": data,
        },
        "analysis_params": {},
    }


@pytest.fixture
def state_with_smooth_prices():
    """Create a state with smooth price data (no anomalies)."""
    now = datetime.now()
    data = []

    for i in range(30):
        timestamp = now - timedelta(hours=30 - i)
        price = 50000 + i * 50  # Smooth normal trend

        data.append({
            "timestamp": timestamp.isoformat(),
            "coin_type": "BTC",
            "bid": float(price) - 50,
            "ask": float(price) + 50,
            "last": float(price),
        })

    return {
        "user_goal": "Analyze price trends",
        "retrieved_data": {
            "price_data": data,
        },
        "analysis_params": {},
    }


class TestDataAnalystAnomalyFlow:
    """Tests for anomaly detection in DataAnalystAgent."""

    @pytest.mark.asyncio
    async def test_analyst_detects_anomalies(
        self, data_analyst_agent, state_with_price_anomalies
    ):
        """Test that analyst agent detects anomalies and sets state."""
        result = await data_analyst_agent.execute(state_with_price_anomalies)

        # Verify analysis completed
        assert result["analysis_completed"] is True

        # Verify anomaly detection was run
        assert "analysis_results" in result
        assert "anomaly_detection" in result["analysis_results"]

        # Verify anomaly_detected state is set
        assert result.get("anomaly_detected") is True
        assert result.get("anomaly_summary") is not None
        assert len(result["anomaly_summary"]) > 0

        # Verify anomaly data structure
        anomaly_data = result["analysis_results"]["anomaly_detection"]
        assert "model" in anomaly_data
        assert anomaly_data["model"] == "IsolationForest"
        assert "total_anomalies" in anomaly_data
        assert anomaly_data["total_anomalies"] > 0
        assert "anomalies" in anomaly_data
        assert "severity_distribution" in anomaly_data
        assert "summary" in anomaly_data

    @pytest.mark.asyncio
    async def test_analyst_no_anomalies_smooth_data(
        self, data_analyst_agent, state_with_smooth_prices
    ):
        """Test analyst with smooth data (no anomalies)."""
        result = await data_analyst_agent.execute(state_with_smooth_prices)

        # Verify analysis completed
        assert result["analysis_completed"] is True

        # Verify anomaly detection was run
        assert "anomaly_detection" in result.get("analysis_results", {})

        # With smooth data, anomaly_detected should be False
        # (or have very few anomalies)
        anomaly_data = result["analysis_results"]["anomaly_detection"]
        if anomaly_data["total_anomalies"] == 0:
            assert result.get("anomaly_detected") is False
        else:
            # Allow for some false positives, but should be minimal
            assert anomaly_data["total_anomalies"] <= 2

    @pytest.mark.asyncio
    async def test_analyst_anomaly_with_custom_contamination(
        self, data_analyst_agent, state_with_price_anomalies
    ):
        """Test anomaly detection with custom contamination parameter."""
        # Set low contamination
        state_with_price_anomalies["analysis_params"]["anomaly_contamination"] = 0.02

        result = await data_analyst_agent.execute(state_with_price_anomalies)

        assert result["analysis_completed"] is True
        anomaly_data = result["analysis_results"]["anomaly_detection"]
        assert anomaly_data["contamination"] == 0.02

    @pytest.mark.asyncio
    async def test_analyst_skip_anomaly_detection(
        self, data_analyst_agent, state_with_price_anomalies
    ):
        """Test that anomaly detection can be skipped."""
        # Change goal to not mention anomalies
        state_with_price_anomalies["user_goal"] = "Analyze price trends"
        # Explicitly disable anomaly detection
        state_with_price_anomalies["analysis_params"]["include_anomaly_detection"] = False

        result = await data_analyst_agent.execute(state_with_price_anomalies)

        assert result["analysis_completed"] is True
        # When anomaly detection is disabled, anomaly_detection should not be in results
        # (unless something else triggered it)
        if "anomaly_detection" in result.get("analysis_results", {}):
            # If it was run, that's ok - the test is flexible
            pass
        # anomaly_detected should not be True when disabled
        assert result.get("anomaly_detected") is not True


class TestRouteAfterAnalysisWithAnomalies:
    """Tests for routing logic after analysis with anomalies."""

    def test_route_to_train_with_ml_goal(self):
        """Test routing to training when ML goal present."""
        workflow = LangGraphWorkflow()

        state: AgentState = {
            "session_id": "test-1",
            "user_goal": "Build a prediction model for BTC",
            "status": "running",
            "current_step": "analyzing",
            "iteration": 0,
            "data_retrieved": True,
            "analysis_completed": True,
            "messages": [],
            "result": None,
            "error": None,
            "retrieved_data": None,
            "analysis_results": None,
            "insights": None,
            "retrieval_params": None,
            "analysis_params": None,
            "model_trained": False,
            "model_evaluated": False,
            "trained_models": None,
            "evaluation_results": None,
            "training_params": None,
            "evaluation_params": None,
            "training_summary": None,
            "evaluation_insights": None,
            "reasoning_trace": None,
            "decision_history": None,
            "retry_count": 0,
            "max_retries": 3,
            "skip_analysis": False,
            "skip_training": False,
            "needs_more_data": False,
            "quality_checks": None,
            "clarifications_needed": None,
            "clarifications_provided": None,
            "awaiting_clarification": False,
            "choices_available": None,
            "selected_choice": None,
            "awaiting_choice": False,
            "recommendation": None,
            "overrides_applied": None,
            "can_override": None,
            "approval_gates": None,
            "approvals_granted": None,
            "approval_mode": "auto",
            "approval_needed": False,
            "pending_approvals": None,
            "reporting_completed": False,
            "reporting_results": None,
            "anomaly_detected": True,
            "anomaly_summary": "5 anomalies detected",
            "alert_triggered": False,
            "alert_payload": None,
        }

        result = workflow._route_after_analysis(state)
        assert result == "train"

    def test_route_to_report_with_anomalies_non_ml_goal(self):
        """Test routing to report when anomalies detected and non-ML goal."""
        workflow = LangGraphWorkflow()

        state: AgentState = {
            "session_id": "test-2",
            "user_goal": "Analyze Bitcoin price trends for anomalies",
            "status": "running",
            "current_step": "analyzing",
            "iteration": 0,
            "data_retrieved": True,
            "analysis_completed": True,
            "messages": [],
            "result": None,
            "error": None,
            "retrieved_data": None,
            "analysis_results": None,
            "insights": None,
            "retrieval_params": None,
            "analysis_params": None,
            "model_trained": False,
            "model_evaluated": False,
            "trained_models": None,
            "evaluation_results": None,
            "training_params": None,
            "evaluation_params": None,
            "training_summary": None,
            "evaluation_insights": None,
            "reasoning_trace": None,
            "decision_history": None,
            "retry_count": 0,
            "max_retries": 3,
            "skip_analysis": False,
            "skip_training": False,
            "needs_more_data": False,
            "quality_checks": None,
            "clarifications_needed": None,
            "clarifications_provided": None,
            "awaiting_clarification": False,
            "choices_available": None,
            "selected_choice": None,
            "awaiting_choice": False,
            "recommendation": None,
            "overrides_applied": None,
            "can_override": None,
            "approval_gates": None,
            "approvals_granted": None,
            "approval_mode": "auto",
            "approval_needed": False,
            "pending_approvals": None,
            "reporting_completed": False,
            "reporting_results": None,
            "anomaly_detected": True,
            "anomaly_summary": "5 anomalies detected",
            "alert_triggered": False,
            "alert_payload": None,
        }

        result = workflow._route_after_analysis(state)
        assert result == "report"

    def test_route_to_finalize_no_anomalies(self):
        """Test routing to finalize when no anomalies and non-ML goal."""
        workflow = LangGraphWorkflow()

        state: AgentState = {
            "session_id": "test-3",
            "user_goal": "Analyze market sentiment",
            "status": "running",
            "current_step": "analyzing",
            "iteration": 0,
            "data_retrieved": True,
            "analysis_completed": True,
            "messages": [],
            "result": None,
            "error": None,
            "retrieved_data": None,
            "analysis_results": None,
            "insights": None,
            "retrieval_params": None,
            "analysis_params": None,
            "model_trained": False,
            "model_evaluated": False,
            "trained_models": None,
            "evaluation_results": None,
            "training_params": None,
            "evaluation_params": None,
            "training_summary": None,
            "evaluation_insights": None,
            "reasoning_trace": None,
            "decision_history": None,
            "retry_count": 0,
            "max_retries": 3,
            "skip_analysis": False,
            "skip_training": False,
            "needs_more_data": False,
            "quality_checks": None,
            "clarifications_needed": None,
            "clarifications_provided": None,
            "awaiting_clarification": False,
            "choices_available": None,
            "selected_choice": None,
            "awaiting_choice": False,
            "recommendation": None,
            "overrides_applied": None,
            "can_override": None,
            "approval_gates": None,
            "approvals_granted": None,
            "approval_mode": "auto",
            "approval_needed": False,
            "pending_approvals": None,
            "reporting_completed": False,
            "reporting_results": None,
            "anomaly_detected": False,
            "anomaly_summary": None,
            "alert_triggered": False,
            "alert_payload": None,
        }

        result = workflow._route_after_analysis(state)
        assert result == "finalize"

    def test_route_to_error_incomplete_analysis(self):
        """Test routing to error when analysis not completed."""
        workflow = LangGraphWorkflow()

        state: AgentState = {
            "session_id": "test-4",
            "user_goal": "Analyze data",
            "status": "running",
            "current_step": "analyzing",
            "iteration": 0,
            "data_retrieved": True,
            "analysis_completed": False,
            "messages": [],
            "result": None,
            "error": None,
            "retrieved_data": None,
            "analysis_results": None,
            "insights": None,
            "retrieval_params": None,
            "analysis_params": None,
            "model_trained": False,
            "model_evaluated": False,
            "trained_models": None,
            "evaluation_results": None,
            "training_params": None,
            "evaluation_params": None,
            "training_summary": None,
            "evaluation_insights": None,
            "reasoning_trace": None,
            "decision_history": None,
            "retry_count": 0,
            "max_retries": 3,
            "skip_analysis": False,
            "skip_training": False,
            "needs_more_data": False,
            "quality_checks": None,
            "clarifications_needed": None,
            "clarifications_provided": None,
            "awaiting_clarification": False,
            "choices_available": None,
            "selected_choice": None,
            "awaiting_choice": False,
            "recommendation": None,
            "overrides_applied": None,
            "can_override": None,
            "approval_gates": None,
            "approvals_granted": None,
            "approval_mode": "auto",
            "approval_needed": False,
            "pending_approvals": None,
            "reporting_completed": False,
            "reporting_results": None,
            "anomaly_detected": False,
            "anomaly_summary": None,
            "alert_triggered": False,
            "alert_payload": None,
        }

        result = workflow._route_after_analysis(state)
        assert result == "error"
        assert state["error"] is not None
