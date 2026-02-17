"""
Tests for data quality monitor.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models import (
    CatalystEvents,
    NewsSentiment,
    PriceData5Min,
)
from app.services.collectors.quality_monitor import (
    DataQualityMonitor,
    QualityMetrics,
    get_quality_monitor,
)


@pytest.fixture
def quality_monitor():
    """Create a quality monitor instance."""
    return DataQualityMonitor()


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def sample_price_data():
    """Sample price data for testing."""
    return PriceData5Min(
        id=1,
        coin_type="BTC",
        timestamp=datetime.now(timezone.utc),
        open_price=Decimal("50000.00"),
        high_price=Decimal("51000.00"),
        low_price=Decimal("49000.00"),
        close_price=Decimal("50500.00"),
        volume=Decimal("1000.00"),
    )


@pytest.fixture
def sample_sentiment_data():
    """Sample sentiment data for testing."""
    return NewsSentiment(
        id=1,
        title="Bitcoin price surges",
        source="CryptoPanic",
        url="https://example.com",
        published_at=datetime.now(timezone.utc),
        sentiment="bullish",
        sentiment_score=Decimal("0.75"),
        currencies=["BTC"],
        collected_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_catalyst_event():
    """Sample catalyst event for testing."""
    return CatalystEvents(
        id=1,
        event_type="listing",
        event_date=datetime.now(timezone.utc).date(),
        source="CoinSpot",
        description="New listing announcement",
        impact_score=Decimal("0.8"),
        currencies=["BTC"],
        url="https://example.com",
        collected_at=datetime.now(timezone.utc),
    )


class TestQualityMetrics:
    """Test suite for QualityMetrics class."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = QualityMetrics()

        assert metrics.completeness_score == 0.0
        assert metrics.timeliness_score == 0.0
        assert metrics.accuracy_score == 0.0
        assert metrics.overall_score == 0.0
        assert metrics.issues == []
        assert metrics.warnings == []
        assert metrics.info == []

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = QualityMetrics()
        metrics.completeness_score = 0.9
        metrics.timeliness_score = 0.8
        metrics.accuracy_score = 0.95
        metrics.overall_score = 0.88
        metrics.issues = ["Issue 1"]
        metrics.warnings = ["Warning 1"]
        metrics.info = ["Info 1"]

        result = metrics.to_dict()

        assert result["completeness_score"] == 0.9
        assert result["timeliness_score"] == 0.8
        assert result["accuracy_score"] == 0.95
        assert result["overall_score"] == 0.88
        assert len(result["issues"]) == 1
        assert len(result["warnings"]) == 1
        assert len(result["info"]) == 1


class TestDataQualityMonitor:
    """Test suite for DataQualityMonitor."""

    def test_initialization(self, quality_monitor):
        """Test monitor initialization."""
        assert quality_monitor.name == "data_quality_monitor"

    @pytest.mark.asyncio
    async def test_check_completeness_with_all_data(
        self, quality_monitor, mock_session
    ):
        """Test completeness check with all data types present."""
        # Mock query results - all tables have data
        mock_session.exec.return_value.one.side_effect = [
            100,  # Price data count
            50,   # Sentiment data count
            20,   # Catalyst events count
            10,   # Protocol fundamentals count
        ]

        metrics = await quality_monitor.check_completeness(mock_session)

        assert metrics.completeness_score == 1.0
        assert len(metrics.issues) == 0
        assert len(metrics.info) == 4

    @pytest.mark.asyncio
    async def test_check_completeness_with_missing_data(
        self, quality_monitor, mock_session
    ):
        """Test completeness check with missing data."""
        # Mock query results - some tables empty
        mock_session.exec.return_value.one.side_effect = [
            100,  # Price data count (present)
            0,    # Sentiment data count (missing)
            0,    # Catalyst events count (missing)
            10,   # Protocol fundamentals count (present)
        ]

        metrics = await quality_monitor.check_completeness(mock_session)

        assert metrics.completeness_score < 1.0
        assert len(metrics.warnings) >= 2

    @pytest.mark.asyncio
    async def test_check_completeness_with_no_price_data(
        self, quality_monitor, mock_session
    ):
        """Test completeness check with no price data (critical)."""
        # Mock query results - no price data
        mock_session.exec.return_value.one.side_effect = [
            0,   # Price data count (missing - critical!)
            50,  # Sentiment data count
            20,  # Catalyst events count
            10,  # Protocol fundamentals count
        ]

        metrics = await quality_monitor.check_completeness(mock_session)

        assert metrics.completeness_score < 1.0
        assert any("price" in issue.lower() for issue in metrics.issues)

    @pytest.mark.asyncio
    async def test_check_timeliness_with_fresh_data(
        self, quality_monitor, mock_session, sample_price_data,
        sample_sentiment_data, sample_catalyst_event
    ):
        """Test timeliness check with fresh data."""
        # Set up fresh timestamps
        now = datetime.now(timezone.utc)
        sample_price_data.timestamp = now - timedelta(minutes=5)
        sample_sentiment_data.collected_at = now - timedelta(minutes=10)
        sample_catalyst_event.collected_at = now - timedelta(hours=2)

        # Mock query results
        mock_session.exec.return_value.first.side_effect = [
            sample_price_data,
            sample_sentiment_data,
            sample_catalyst_event,
        ]

        metrics = await quality_monitor.check_timeliness(mock_session)

        assert metrics.timeliness_score >= 0.9
        assert len(metrics.issues) == 0

    @pytest.mark.asyncio
    async def test_check_timeliness_with_stale_data(
        self, quality_monitor, mock_session, sample_price_data
    ):
        """Test timeliness check with stale data."""
        # Set up stale timestamp
        now = datetime.now(timezone.utc)
        sample_price_data.timestamp = now - timedelta(hours=2)

        # Mock query results - stale price data, no other data
        mock_session.exec.return_value.first.side_effect = [
            sample_price_data,
            None,  # No sentiment data
            None,  # No catalyst data
        ]

        metrics = await quality_monitor.check_timeliness(mock_session)

        assert metrics.timeliness_score < 0.5
        assert len(metrics.issues) > 0 or len(metrics.warnings) > 0

    @pytest.mark.asyncio
    async def test_check_timeliness_with_no_data(
        self, quality_monitor, mock_session
    ):
        """Test timeliness check with no data."""
        # Mock query results - no data
        mock_session.exec.return_value.first.side_effect = [None, None, None]

        metrics = await quality_monitor.check_timeliness(mock_session)

        assert metrics.timeliness_score < 1.0
        assert len(metrics.issues) > 0 or len(metrics.warnings) > 0

    @pytest.mark.asyncio
    async def test_check_accuracy_with_valid_data(
        self, quality_monitor, mock_session
    ):
        """Test accuracy check with all valid data."""
        # Mock query results - no invalid records
        mock_session.exec.return_value.one.side_effect = [
            0,    # Invalid price count
            100,  # Total price count
            0,    # Invalid sentiment count
            50,   # Total sentiment count
            0,    # Invalid catalyst count
            20,   # Total catalyst count
        ]

        metrics = await quality_monitor.check_accuracy(mock_session)

        assert metrics.accuracy_score >= 0.9
        assert len(metrics.issues) == 0

    @pytest.mark.asyncio
    async def test_check_accuracy_with_invalid_data(
        self, quality_monitor, mock_session
    ):
        """Test accuracy check with some invalid data."""
        # Mock query results - some invalid records
        mock_session.exec.return_value.one.side_effect = [
            5,    # Invalid price count
            100,  # Total price count
            2,    # Invalid sentiment count
            50,   # Total sentiment count
            1,    # Invalid catalyst count
            20,   # Total catalyst count
        ]

        metrics = await quality_monitor.check_accuracy(mock_session)

        assert metrics.accuracy_score < 1.0
        assert len(metrics.warnings) > 0

    @pytest.mark.asyncio
    async def test_check_all_aggregates_scores(
        self, quality_monitor, mock_session
    ):
        """Test that check_all aggregates all scores correctly."""
        # Mock all queries to return some data
        # Completeness: 4 one() calls, then Accuracy: 6 one() calls
        mock_session.exec.return_value.one.side_effect = [
            # Completeness checks
            100, 50, 20, 10,
            # Accuracy checks
            0, 100,  # Price validity
            0, 50,   # Sentiment validity
            0, 20,   # Catalyst validity
        ]

        # Mock timeliness queries
        now = datetime.now(timezone.utc)
        mock_price = MagicMock()
        mock_price.timestamp = now - timedelta(minutes=5)
        mock_sentiment = MagicMock()
        mock_sentiment.collected_at = now - timedelta(minutes=15)
        mock_catalyst = MagicMock()
        mock_catalyst.collected_at = now - timedelta(hours=1)

        mock_session.exec.return_value.first.side_effect = [
            mock_price,
            mock_sentiment,
            mock_catalyst,
        ]

        metrics = await quality_monitor.check_all(mock_session)

        assert 0.0 <= metrics.completeness_score <= 1.0
        assert 0.0 <= metrics.timeliness_score <= 1.0
        assert 0.0 <= metrics.accuracy_score <= 1.0
        assert 0.0 <= metrics.overall_score <= 1.0

        # Overall score should be weighted average
        expected_overall = (
            metrics.completeness_score * 0.3 +
            metrics.timeliness_score * 0.4 +
            metrics.accuracy_score * 0.3
        )
        assert abs(metrics.overall_score - expected_overall) < 0.01

    @pytest.mark.asyncio
    async def test_generate_alert_when_below_threshold(
        self, quality_monitor
    ):
        """Test alert generation when score is below threshold."""
        metrics = QualityMetrics()
        metrics.overall_score = 0.6
        metrics.issues = ["Test issue"]

        alert = await quality_monitor.generate_alert(metrics, threshold=0.7)

        assert alert is not None
        assert alert["severity"] in ["high", "medium"]
        assert "quality score is low" in alert["message"].lower()
        assert "timestamp" in alert
        assert "metrics" in alert

    @pytest.mark.asyncio
    async def test_generate_alert_when_above_threshold(
        self, quality_monitor
    ):
        """Test no alert when score is above threshold."""
        metrics = QualityMetrics()
        metrics.overall_score = 0.9

        alert = await quality_monitor.generate_alert(metrics, threshold=0.7)

        assert alert is None

    @pytest.mark.asyncio
    async def test_generate_alert_severity_high_for_very_low_score(
        self, quality_monitor
    ):
        """Test that very low scores generate high severity alerts."""
        metrics = QualityMetrics()
        metrics.overall_score = 0.4

        alert = await quality_monitor.generate_alert(metrics, threshold=0.7)

        assert alert is not None
        assert alert["severity"] == "high"

    @pytest.mark.asyncio
    async def test_generate_alert_severity_medium_for_low_score(
        self, quality_monitor
    ):
        """Test that moderately low scores generate medium severity alerts."""
        metrics = QualityMetrics()
        metrics.overall_score = 0.6

        alert = await quality_monitor.generate_alert(metrics, threshold=0.7)

        assert alert is not None
        assert alert["severity"] == "medium"


def test_get_quality_monitor_singleton():
    """Test that get_quality_monitor returns a singleton."""
    monitor1 = get_quality_monitor()
    monitor2 = get_quality_monitor()

    assert monitor1 is monitor2
    assert isinstance(monitor1, DataQualityMonitor)
