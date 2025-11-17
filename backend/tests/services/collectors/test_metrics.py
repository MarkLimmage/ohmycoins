"""
Tests for collection metrics tracker.
"""

import pytest
from datetime import datetime, timezone

from app.services.collectors.metrics import (
    CollectorMetrics,
    MetricsTracker,
    get_metrics_tracker,
)


@pytest.fixture
def collector_metrics():
    """Create a collector metrics instance."""
    return CollectorMetrics("test_collector")


@pytest.fixture
def metrics_tracker():
    """Create a metrics tracker instance."""
    return MetricsTracker()


class TestCollectorMetrics:
    """Test suite for CollectorMetrics class."""
    
    def test_initialization(self, collector_metrics):
        """Test metrics initialization."""
        assert collector_metrics.collector_name == "test_collector"
        assert collector_metrics.total_runs == 0
        assert collector_metrics.successful_runs == 0
        assert collector_metrics.failed_runs == 0
        assert collector_metrics.total_records_collected == 0
        assert collector_metrics.total_latency_seconds == 0.0
        assert collector_metrics.last_run_at is None
        assert collector_metrics.last_success_at is None
        assert collector_metrics.last_failure_at is None
        assert collector_metrics.last_error is None
    
    def test_record_success(self, collector_metrics):
        """Test recording a successful run."""
        collector_metrics.record_success(records_collected=100, latency_seconds=2.5)
        
        assert collector_metrics.total_runs == 1
        assert collector_metrics.successful_runs == 1
        assert collector_metrics.failed_runs == 0
        assert collector_metrics.total_records_collected == 100
        assert collector_metrics.total_latency_seconds == 2.5
        assert collector_metrics.last_run_at is not None
        assert collector_metrics.last_success_at is not None
        assert collector_metrics.last_failure_at is None
    
    def test_record_failure(self, collector_metrics):
        """Test recording a failed run."""
        collector_metrics.record_failure(error="Connection timeout", latency_seconds=5.0)
        
        assert collector_metrics.total_runs == 1
        assert collector_metrics.successful_runs == 0
        assert collector_metrics.failed_runs == 1
        assert collector_metrics.total_records_collected == 0
        assert collector_metrics.total_latency_seconds == 5.0
        assert collector_metrics.last_run_at is not None
        assert collector_metrics.last_success_at is None
        assert collector_metrics.last_failure_at is not None
        assert collector_metrics.last_error == "Connection timeout"
    
    def test_success_rate_calculation(self, collector_metrics):
        """Test success rate calculation."""
        # Record some successes and failures
        collector_metrics.record_success(100, 2.0)
        collector_metrics.record_success(150, 2.5)
        collector_metrics.record_success(120, 2.2)
        collector_metrics.record_failure("Error", 3.0)
        
        # 3 successes out of 4 total = 75%
        assert collector_metrics.success_rate == 75.0
    
    def test_success_rate_with_no_runs(self, collector_metrics):
        """Test success rate when no runs recorded."""
        assert collector_metrics.success_rate == 0.0
    
    def test_average_latency_calculation(self, collector_metrics):
        """Test average latency calculation."""
        collector_metrics.record_success(100, 2.0)
        collector_metrics.record_success(150, 4.0)
        collector_metrics.record_failure("Error", 3.0)
        
        # (2.0 + 4.0 + 3.0) / 3 = 3.0
        assert collector_metrics.average_latency == 3.0
    
    def test_average_latency_with_no_runs(self, collector_metrics):
        """Test average latency when no runs recorded."""
        assert collector_metrics.average_latency == 0.0
    
    def test_average_records_per_run_calculation(self, collector_metrics):
        """Test average records per run calculation."""
        collector_metrics.record_success(100, 2.0)
        collector_metrics.record_success(200, 2.5)
        collector_metrics.record_failure("Error", 3.0)  # Doesn't count records
        
        # (100 + 200) / 2 successful runs = 150
        assert collector_metrics.average_records_per_run == 150.0
    
    def test_average_records_with_no_successful_runs(self, collector_metrics):
        """Test average records when no successful runs."""
        collector_metrics.record_failure("Error", 3.0)
        
        assert collector_metrics.average_records_per_run == 0.0
    
    def test_to_dict(self, collector_metrics):
        """Test conversion to dictionary."""
        collector_metrics.record_success(100, 2.5)
        collector_metrics.record_failure("Test error", 3.0)
        
        result = collector_metrics.to_dict()
        
        assert result["collector_name"] == "test_collector"
        assert result["total_runs"] == 2
        assert result["successful_runs"] == 1
        assert result["failed_runs"] == 1
        assert result["success_rate"] == 50.0
        assert result["total_records_collected"] == 100
        assert "average_records_per_run" in result
        assert "average_latency_seconds" in result
        assert result["last_run_at"] is not None
        assert result["last_success_at"] is not None
        assert result["last_failure_at"] is not None
        assert result["last_error"] == "Test error"


class TestMetricsTracker:
    """Test suite for MetricsTracker."""
    
    def test_initialization(self, metrics_tracker):
        """Test tracker initialization."""
        assert len(metrics_tracker._metrics) == 0
        assert metrics_tracker._started_at is not None
    
    def test_get_collector_metrics_creates_new(self, metrics_tracker):
        """Test that getting metrics creates new instance if needed."""
        metrics = metrics_tracker.get_collector_metrics("new_collector")
        
        assert isinstance(metrics, CollectorMetrics)
        assert metrics.collector_name == "new_collector"
        assert "new_collector" in metrics_tracker._metrics
    
    def test_get_collector_metrics_returns_existing(self, metrics_tracker):
        """Test that getting metrics returns existing instance."""
        metrics1 = metrics_tracker.get_collector_metrics("test_collector")
        metrics1.record_success(100, 2.0)
        
        metrics2 = metrics_tracker.get_collector_metrics("test_collector")
        
        assert metrics1 is metrics2
        assert metrics2.total_runs == 1
    
    def test_record_success(self, metrics_tracker):
        """Test recording success through tracker."""
        metrics_tracker.record_success("collector1", 100, 2.5)
        
        metrics = metrics_tracker.get_collector_metrics("collector1")
        assert metrics.successful_runs == 1
        assert metrics.total_records_collected == 100
    
    def test_record_failure(self, metrics_tracker):
        """Test recording failure through tracker."""
        metrics_tracker.record_failure("collector1", "Test error", 3.0)
        
        metrics = metrics_tracker.get_collector_metrics("collector1")
        assert metrics.failed_runs == 1
        assert metrics.last_error == "Test error"
    
    def test_get_all_metrics(self, metrics_tracker):
        """Test getting all metrics."""
        metrics_tracker.record_success("collector1", 100, 2.0)
        metrics_tracker.record_success("collector2", 50, 1.5)
        
        all_metrics = metrics_tracker.get_all_metrics()
        
        assert "system" in all_metrics
        assert "collectors" in all_metrics
        assert "started_at" in all_metrics["system"]
        assert "uptime_seconds" in all_metrics["system"]
        assert all_metrics["system"]["collectors_tracked"] == 2
        assert "collector1" in all_metrics["collectors"]
        assert "collector2" in all_metrics["collectors"]
    
    def test_get_summary(self, metrics_tracker):
        """Test getting summary statistics."""
        metrics_tracker.record_success("collector1", 100, 2.0)
        metrics_tracker.record_success("collector1", 150, 2.5)
        metrics_tracker.record_failure("collector2", "Error", 3.0)
        metrics_tracker.record_success("collector2", 75, 1.5)
        
        summary = metrics_tracker.get_summary()
        
        assert summary["total_collectors"] == 2
        assert summary["total_runs"] == 4
        assert summary["overall_success_rate"] == 75.0  # 3 success out of 4
        assert summary["total_records_collected"] == 325  # 100 + 150 + 75
        assert "average_latency" in summary
    
    def test_get_summary_with_no_data(self, metrics_tracker):
        """Test summary with no metrics."""
        summary = metrics_tracker.get_summary()
        
        assert summary["total_collectors"] == 0
        assert summary["total_runs"] == 0
        assert summary["overall_success_rate"] == 0.0
        assert summary["total_records_collected"] == 0
        assert summary["average_latency"] == 0.0
    
    def test_get_health_status_all_healthy(self, metrics_tracker):
        """Test health status when all collectors are healthy."""
        metrics_tracker.record_success("collector1", 100, 2.0)
        metrics_tracker.record_success("collector1", 150, 2.5)
        metrics_tracker.record_success("collector2", 75, 1.5)
        
        health = metrics_tracker.get_health_status()
        
        assert health["overall_health"] == "healthy"
        assert len(health["healthy_collectors"]) == 2
        assert len(health["degraded_collectors"]) == 0
        assert len(health["failing_collectors"]) == 0
    
    def test_get_health_status_with_degraded(self, metrics_tracker):
        """Test health status with degraded collectors."""
        # collector1: 2 success, 1 failure = 66.7% (degraded: 80-95%)
        metrics_tracker.record_success("collector1", 100, 2.0)
        metrics_tracker.record_failure("collector1", "Error", 3.0)
        metrics_tracker.record_success("collector1", 150, 2.5)
        
        # collector2: all success = 100% (healthy)
        metrics_tracker.record_success("collector2", 75, 1.5)
        
        # Add one more failure to get exactly in degraded range
        metrics_tracker.record_success("collector1", 100, 2.0)  # 3 success, 1 failure = 75%
        
        health = metrics_tracker.get_health_status()
        
        assert health["overall_health"] == "degraded"
        assert len(health["degraded_collectors"]) > 0 or len(health["failing_collectors"]) > 0
    
    def test_get_health_status_with_failing(self, metrics_tracker):
        """Test health status with failing collectors."""
        # collector1: all failures
        metrics_tracker.record_failure("collector1", "Error 1", 3.0)
        metrics_tracker.record_failure("collector1", "Error 2", 3.0)
        
        health = metrics_tracker.get_health_status()
        
        assert health["overall_health"] == "unhealthy"
        assert len(health["failing_collectors"]) > 0
    
    def test_reset_specific_collector(self, metrics_tracker):
        """Test resetting metrics for specific collector."""
        metrics_tracker.record_success("collector1", 100, 2.0)
        metrics_tracker.record_success("collector2", 50, 1.5)
        
        metrics_tracker.reset_metrics("collector1")
        
        metrics1 = metrics_tracker.get_collector_metrics("collector1")
        metrics2 = metrics_tracker.get_collector_metrics("collector2")
        
        assert metrics1.total_runs == 0
        assert metrics2.total_runs == 1
    
    def test_reset_all_collectors(self, metrics_tracker):
        """Test resetting all metrics."""
        metrics_tracker.record_success("collector1", 100, 2.0)
        metrics_tracker.record_success("collector2", 50, 1.5)
        
        metrics_tracker.reset_metrics()
        
        assert len(metrics_tracker._metrics) == 0
        summary = metrics_tracker.get_summary()
        assert summary["total_collectors"] == 0


def test_get_metrics_tracker_singleton():
    """Test that get_metrics_tracker returns a singleton."""
    tracker1 = get_metrics_tracker()
    tracker2 = get_metrics_tracker()
    
    assert tracker1 is tracker2
    assert isinstance(tracker1, MetricsTracker)
