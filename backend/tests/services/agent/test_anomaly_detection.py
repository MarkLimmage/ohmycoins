"""
Tests for Anomaly Detection Tools — Sprint 2.36

Tests for the detect_price_anomalies function using synthetic data.
"""

from datetime import datetime, timedelta

import pytest

from app.services.agent.tools.anomaly_detection import detect_price_anomalies


@pytest.fixture
def sample_price_data_with_anomalies():
    """Create sample price data with synthetic anomalies."""
    now = datetime.now()
    data = []

    # BTC data: mostly normal with some anomalies
    for i in range(50):
        timestamp = now - timedelta(hours=50 - i)
        price = 50000 + i * 100  # Normal trend

        # Inject anomalies
        if i == 10:  # Minor anomaly
            price = 40000
        elif i == 25:  # Medium anomaly
            price = 45000
        elif i == 40:  # High anomaly
            price = 30000

        data.append({
            "timestamp": timestamp.isoformat(),
            "coin": "BTC",
            "price": float(price),
        })

    # ETH data: mostly normal with fewer anomalies
    for i in range(40):
        timestamp = now - timedelta(hours=40 - i)
        price = 2000 + i * 10  # Normal trend

        # Inject anomaly
        if i == 15:  # High anomaly
            price = 1000

        data.append({
            "timestamp": timestamp.isoformat(),
            "coin": "ETH",
            "price": float(price),
        })

    return data


@pytest.fixture
def sample_price_data_no_anomalies():
    """Create sample price data without anomalies (smooth trend)."""
    now = datetime.now()
    data = []

    for i in range(30):
        timestamp = now - timedelta(hours=30 - i)
        price = 50000 + i * 50  # Smooth normal trend

        data.append({
            "timestamp": timestamp.isoformat(),
            "coin": "BTC",
            "price": float(price),
        })

    return data


class TestDetectPriceAnomalies:
    """Tests for detect_price_anomalies function."""

    def test_detect_price_anomalies_with_synthetic_anomalies(
        self, sample_price_data_with_anomalies
    ):
        """Test anomaly detection with synthetic anomalies."""
        result = detect_price_anomalies(
            sample_price_data_with_anomalies,
            contamination=0.05
        )

        # Verify result structure
        assert "model" in result
        assert result["model"] == "IsolationForest"
        assert "contamination" in result
        assert "coins_analyzed" in result
        assert "total_anomalies" in result
        assert "anomalies" in result
        assert "severity_distribution" in result
        assert "summary" in result

        # Verify coins were analyzed
        assert "BTC" in result["coins_analyzed"]
        assert "ETH" in result["coins_analyzed"]

        # Verify anomalies were detected
        assert result["total_anomalies"] > 0

        # Verify anomaly objects have required fields
        for anomaly in result["anomalies"]:
            assert "timestamp" in anomaly
            assert "coin" in anomaly
            assert "price" in anomaly
            assert "anomaly_score" in anomaly
            assert "is_anomaly" in anomaly
            assert "severity" in anomaly
            assert anomaly["is_anomaly"] is True
            assert anomaly["severity"] in ["LOW", "MEDIUM", "HIGH"]

        # Verify severity distribution
        assert sum(result["severity_distribution"].values()) == result["total_anomalies"]

    def test_detect_price_anomalies_no_anomalies(
        self, sample_price_data_no_anomalies
    ):
        """Test anomaly detection with smooth data (no anomalies)."""
        result = detect_price_anomalies(
            sample_price_data_no_anomalies,
            contamination=0.01  # Low contamination rate
        )

        # Verify result structure
        assert "model" in result
        assert "coins_analyzed" in result

        # With smooth data and low contamination, expect very few/no anomalies
        # (May vary based on Isolation Forest randomness, but should be minimal)
        if result["total_anomalies"] > 0:
            assert result["total_anomalies"] <= 2  # Allow for some false positives

    def test_detect_price_anomalies_empty_data(self):
        """Test anomaly detection with empty data."""
        result = detect_price_anomalies([], contamination=0.05)

        assert result["model"] == "IsolationForest"
        assert result["coins_analyzed"] == []
        assert result["total_anomalies"] == 0
        assert result["anomalies"] == []
        assert "No price data provided" in result["summary"]

    def test_detect_price_anomalies_single_coin(self):
        """Test anomaly detection with single coin."""
        now = datetime.now()
        data = []

        for i in range(20):
            timestamp = now - timedelta(hours=20 - i)
            price = 50000 + i * 100
            data.append({
                "timestamp": timestamp.isoformat(),
                "coin": "BTC",
                "price": float(price),
            })

        result = detect_price_anomalies(data, contamination=0.05)

        assert len(result["coins_analyzed"]) == 1
        assert result["coins_analyzed"][0] == "BTC"

    def test_detect_price_anomalies_insufficient_data(self):
        """Test anomaly detection with insufficient data per coin."""
        now = datetime.now()
        data = [
            {
                "timestamp": now.isoformat(),
                "coin": "BTC",
                "price": 50000.0,
            },
            {
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "coin": "BTC",
                "price": 50100.0,
            },
        ]

        result = detect_price_anomalies(data, contamination=0.05)

        # With only 2 data points, should have insufficient data
        assert result["coins_analyzed"] == ["BTC"]
        assert result["total_anomalies"] == 0

    def test_detect_price_anomalies_severity_thresholds(
        self, sample_price_data_with_anomalies
    ):
        """Test severity threshold calculation."""
        result = detect_price_anomalies(
            sample_price_data_with_anomalies,
            contamination=0.1
        )

        # Verify severity distribution has correct keys
        severity_dist = result["severity_distribution"]
        assert "LOW" in severity_dist
        assert "MEDIUM" in severity_dist
        assert "HIGH" in severity_dist

        # All values should be non-negative integers
        for severity, count in severity_dist.items():
            assert isinstance(count, int)
            assert count >= 0

    def test_detect_price_anomalies_summary_generation(
        self, sample_price_data_with_anomalies
    ):
        """Test summary string generation."""
        result = detect_price_anomalies(
            sample_price_data_with_anomalies,
            contamination=0.05
        )

        summary = result["summary"]
        assert isinstance(summary, str)
        assert len(summary) > 0

        if result["total_anomalies"] > 0:
            assert "anomalies" in summary.lower()
            assert "detected" in summary.lower()
        else:
            assert "No anomalies" in summary

    def test_detect_price_anomalies_custom_contamination(
        self, sample_price_data_with_anomalies
    ):
        """Test with custom contamination rate."""
        # Low contamination should detect fewer anomalies
        result_low = detect_price_anomalies(
            sample_price_data_with_anomalies,
            contamination=0.02
        )

        # High contamination should detect more anomalies
        result_high = detect_price_anomalies(
            sample_price_data_with_anomalies,
            contamination=0.10
        )

        # Generally, higher contamination = more anomalies (not guaranteed due to IF randomness)
        assert result_high["total_anomalies"] >= result_low["total_anomalies"]
