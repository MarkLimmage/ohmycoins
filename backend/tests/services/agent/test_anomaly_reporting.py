"""
Tests for Anomaly Detection Integration in ReportingAgent — Sprint 2.36

Tests for the reporting agent's anomaly detection sections and alert bridge.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.services.agent.agents.reporting import ReportingAgent
from app.services.agent.tools.reporting_tools import (
    generate_recommendations,
    generate_summary,
)


@pytest.fixture
def reporting_agent():
    """Create a ReportingAgent."""
    return ReportingAgent(artifacts_dir="/tmp/test_artifacts")


@pytest.fixture
def analysis_results_with_anomalies():
    """Create analysis results with anomalies."""
    return {
        "anomaly_detection": {
            "model": "IsolationForest",
            "contamination": 0.05,
            "coins_analyzed": ["BTC", "ETH"],
            "total_anomalies": 7,
            "anomalies": [
                {
                    "timestamp": "2026-02-25T14:30:00Z",
                    "coin": "BTC",
                    "price": 52340.0,
                    "anomaly_score": -0.87,
                    "is_anomaly": True,
                    "severity": "HIGH",
                },
                {
                    "timestamp": "2026-02-25T14:35:00Z",
                    "coin": "BTC",
                    "price": 52350.0,
                    "anomaly_score": -0.92,
                    "is_anomaly": True,
                    "severity": "HIGH",
                },
                {
                    "timestamp": "2026-02-25T14:40:00Z",
                    "coin": "ETH",
                    "price": 2840.0,
                    "anomaly_score": -0.75,
                    "is_anomaly": True,
                    "severity": "MEDIUM",
                },
                {
                    "timestamp": "2026-02-25T14:45:00Z",
                    "coin": "ETH",
                    "price": 2850.0,
                    "anomaly_score": -0.60,
                    "is_anomaly": True,
                    "severity": "LOW",
                },
            ],
            "severity_distribution": {"LOW": 2, "MEDIUM": 2, "HIGH": 2},
            "summary": "7 anomalies detected across 2 coins. 2 HIGH severity events require attention.",
        },
    }


@pytest.fixture
def analysis_results_no_anomalies():
    """Create analysis results without anomalies."""
    return {
        "technical_indicators": {
            "columns": ["close", "sma_20", "rsi"],
            "data_points": 50,
        },
        "sentiment_analysis": {
            "overall_sentiment": {"trend": "bullish"},
        },
    }


class TestReportingAnomalySummary:
    """Tests for anomaly section in report summary."""

    def test_generate_summary_with_anomalies(self, analysis_results_with_anomalies):
        """Test that summary includes anomaly section when present."""
        summary = generate_summary(
            user_goal="Analyze data for anomalies",
            evaluation_results={},
            model_results={},
            analysis_results=analysis_results_with_anomalies,
        )

        # Verify anomaly section is in summary
        assert "Anomaly Detection" in summary
        assert "IsolationForest" in summary
        assert "7" in summary  # total anomalies
        assert "HIGH Severity" in summary
        assert "2" in summary  # HIGH severity count

    def test_generate_summary_without_anomalies(self, analysis_results_no_anomalies):
        """Test that summary doesn't have anomaly section when not present."""
        summary = generate_summary(
            user_goal="Analyze data",
            evaluation_results={},
            model_results={},
            analysis_results=analysis_results_no_anomalies,
        )

        # Verify anomaly section is NOT in summary
        assert "Anomaly Detection" not in summary


class TestReportingAnomalyRecommendations:
    """Tests for anomaly-based recommendations."""

    def test_generate_recommendations_with_high_severity_anomalies(
        self, analysis_results_with_anomalies
    ):
        """Test that recommendations include HIGH severity warning."""
        recommendations = generate_recommendations(
            user_goal="Analyze data",
            evaluation_results={},
            model_results={},
            analysis_results=analysis_results_with_anomalies,
        )

        # Verify high severity recommendation is present
        high_severity_rec = None
        for rec in recommendations:
            if "HIGH severity" in rec or "URGENT" in rec:
                high_severity_rec = rec
                break

        assert high_severity_rec is not None
        assert "anomalies" in high_severity_rec.lower()
        assert "stop-loss" in high_severity_rec.lower() or "stop-losses" in high_severity_rec.lower()

    def test_generate_recommendations_without_anomalies(
        self, analysis_results_no_anomalies
    ):
        """Test that recommendations don't include anomaly warning when not present."""
        recommendations = generate_recommendations(
            user_goal="Analyze data",
            evaluation_results={},
            model_results={},
            analysis_results=analysis_results_no_anomalies,
        )

        # Verify no anomaly-related recommendations
        for rec in recommendations:
            assert "anomal" not in rec.lower()


class TestAlertBridge:
    """Tests for the Alert Bridge in ReportingAgent."""

    @pytest.mark.asyncio
    async def test_alert_bridge_triggered_on_high_severity(
        self, reporting_agent, analysis_results_with_anomalies
    ):
        """Test that alert_triggered and alert_payload are set when HIGH severity anomalies present."""
        state = {
            "session_id": "test-session",
            "user_goal": "Analyze data for anomalies",
            "analysis_results": analysis_results_with_anomalies,
            "model_results": {},
            "evaluation_results": {},
        }

        result = await reporting_agent.execute(state)

        # Verify alert is triggered
        assert result.get("alert_triggered") is True
        assert result.get("alert_payload") is not None

        # Verify alert payload structure
        payload = result["alert_payload"]
        assert payload["type"] == "anomaly_severity"
        assert payload["severity"] == "HIGH"
        assert payload["count"] == 2  # 2 HIGH severity anomalies
        assert "BTC" in payload["coins"]  # BTC has HIGH severity anomalies
        assert isinstance(payload["coins"], list)
        assert "summary" in payload
        assert "timestamp" in payload

    @pytest.mark.asyncio
    async def test_alert_bridge_not_triggered_without_anomalies(
        self, reporting_agent, analysis_results_no_anomalies
    ):
        """Test that alert is not triggered when no anomalies."""
        state = {
            "session_id": "test-session",
            "user_goal": "Analyze data",
            "analysis_results": analysis_results_no_anomalies,
            "model_results": {},
            "evaluation_results": {},
        }

        result = await reporting_agent.execute(state)

        # Verify alert is not triggered
        # alert_triggered should not be set or should be False
        assert result.get("alert_triggered") is not True

    @pytest.mark.asyncio
    async def test_alert_bridge_with_multiple_coins(
        self, reporting_agent, analysis_results_with_anomalies
    ):
        """Test alert payload includes all coins with HIGH severity anomalies."""
        # Add ETH with HIGH severity
        analysis_results_with_anomalies["anomaly_detection"]["anomalies"].append({
            "timestamp": "2026-02-25T14:50:00Z",
            "coin": "ETH",
            "price": 2860.0,
            "anomaly_score": -0.91,
            "is_anomaly": True,
            "severity": "HIGH",
        })
        analysis_results_with_anomalies["anomaly_detection"]["severity_distribution"]["HIGH"] = 3

        state = {
            "session_id": "test-session",
            "user_goal": "Analyze data for anomalies",
            "analysis_results": analysis_results_with_anomalies,
            "model_results": {},
            "evaluation_results": {},
        }

        result = await reporting_agent.execute(state)

        # Verify alert payload includes both coins
        payload = result["alert_payload"]
        assert payload["count"] == 3
        assert "BTC" in payload["coins"]
        assert "ETH" in payload["coins"]

    @pytest.mark.asyncio
    async def test_reporting_completed_with_anomalies(
        self, reporting_agent, analysis_results_with_anomalies
    ):
        """Test that reporting completes successfully with anomalies."""
        state = {
            "session_id": "test-session",
            "user_goal": "Analyze data for anomalies",
            "analysis_results": analysis_results_with_anomalies,
            "model_results": {},
            "evaluation_results": {},
        }

        result = await reporting_agent.execute(state)

        # Verify reporting completed
        assert result["reporting_completed"] is True
        assert "reporting_results" in result
        assert "error" not in result or result["error"] is None

        # Verify recommendations include anomaly warning
        recommendations = result["reporting_results"]["recommendations"]
        has_anomaly_rec = any("anomal" in rec.lower() for rec in recommendations)
        assert has_anomaly_rec
