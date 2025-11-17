"""
Collection metrics tracking for Phase 2.5 collectors.

This module tracks performance metrics for data collectors including
success rates, latency, and data volume.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class CollectorMetrics:
    """Tracks metrics for a single collector."""
    
    def __init__(self, collector_name: str):
        self.collector_name = collector_name
        self.total_runs = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.total_records_collected = 0
        self.total_latency_seconds = 0.0
        self.last_run_at: datetime | None = None
        self.last_success_at: datetime | None = None
        self.last_failure_at: datetime | None = None
        self.last_error: str | None = None
    
    def record_success(
        self,
        records_collected: int,
        latency_seconds: float
    ) -> None:
        """Record a successful collection run."""
        self.total_runs += 1
        self.successful_runs += 1
        self.total_records_collected += records_collected
        self.total_latency_seconds += latency_seconds
        self.last_run_at = datetime.now(timezone.utc)
        self.last_success_at = self.last_run_at
        
        logger.debug(
            f"Metrics: {self.collector_name} - Success "
            f"(records: {records_collected}, latency: {latency_seconds:.2f}s)"
        )
    
    def record_failure(self, error: str, latency_seconds: float) -> None:
        """Record a failed collection run."""
        self.total_runs += 1
        self.failed_runs += 1
        self.total_latency_seconds += latency_seconds
        self.last_run_at = datetime.now(timezone.utc)
        self.last_failure_at = self.last_run_at
        self.last_error = error
        
        logger.warning(
            f"Metrics: {self.collector_name} - Failure "
            f"(error: {error}, latency: {latency_seconds:.2f}s)"
        )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100
    
    @property
    def average_latency(self) -> float:
        """Calculate average latency in seconds."""
        if self.total_runs == 0:
            return 0.0
        return self.total_latency_seconds / self.total_runs
    
    @property
    def average_records_per_run(self) -> float:
        """Calculate average records collected per successful run."""
        if self.successful_runs == 0:
            return 0.0
        return self.total_records_collected / self.successful_runs
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "collector_name": self.collector_name,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "success_rate": round(self.success_rate, 2),
            "total_records_collected": self.total_records_collected,
            "average_records_per_run": round(self.average_records_per_run, 2),
            "average_latency_seconds": round(self.average_latency, 2),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_success_at": (
                self.last_success_at.isoformat() if self.last_success_at else None
            ),
            "last_failure_at": (
                self.last_failure_at.isoformat() if self.last_failure_at else None
            ),
            "last_error": self.last_error,
        }


class MetricsTracker:
    """
    Tracks metrics for all collectors.
    
    Provides centralized metrics tracking and reporting for the collection
    orchestrator and individual collectors.
    """
    
    def __init__(self):
        """Initialize the metrics tracker."""
        self._metrics: dict[str, CollectorMetrics] = {}
        self._started_at = datetime.now(timezone.utc)
    
    def get_collector_metrics(self, collector_name: str) -> CollectorMetrics:
        """
        Get or create metrics for a collector.
        
        Args:
            collector_name: Name of the collector
        
        Returns:
            CollectorMetrics instance for the collector
        """
        if collector_name not in self._metrics:
            self._metrics[collector_name] = CollectorMetrics(collector_name)
        return self._metrics[collector_name]
    
    def record_success(
        self,
        collector_name: str,
        records_collected: int,
        latency_seconds: float
    ) -> None:
        """
        Record a successful collection run.
        
        Args:
            collector_name: Name of the collector
            records_collected: Number of records collected
            latency_seconds: Time taken for collection
        """
        metrics = self.get_collector_metrics(collector_name)
        metrics.record_success(records_collected, latency_seconds)
    
    def record_failure(
        self,
        collector_name: str,
        error: str,
        latency_seconds: float
    ) -> None:
        """
        Record a failed collection run.
        
        Args:
            collector_name: Name of the collector
            error: Error message
            latency_seconds: Time taken before failure
        """
        metrics = self.get_collector_metrics(collector_name)
        metrics.record_failure(error, latency_seconds)
    
    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get metrics for all collectors.
        
        Returns:
            Dictionary containing all collector metrics
        """
        return {
            "system": {
                "started_at": self._started_at.isoformat(),
                "uptime_seconds": (
                    datetime.now(timezone.utc) - self._started_at
                ).total_seconds(),
                "collectors_tracked": len(self._metrics),
            },
            "collectors": {
                name: metrics.to_dict()
                for name, metrics in self._metrics.items()
            },
        }
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics across all collectors.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self._metrics:
            return {
                "total_collectors": 0,
                "total_runs": 0,
                "overall_success_rate": 0.0,
                "total_records_collected": 0,
                "average_latency": 0.0,
            }
        
        total_runs = sum(m.total_runs for m in self._metrics.values())
        successful_runs = sum(m.successful_runs for m in self._metrics.values())
        total_records = sum(
            m.total_records_collected for m in self._metrics.values()
        )
        total_latency = sum(
            m.total_latency_seconds for m in self._metrics.values()
        )
        
        return {
            "total_collectors": len(self._metrics),
            "total_runs": total_runs,
            "overall_success_rate": (
                round((successful_runs / total_runs) * 100, 2)
                if total_runs > 0 else 0.0
            ),
            "total_records_collected": total_records,
            "average_latency": (
                round(total_latency / total_runs, 2)
                if total_runs > 0 else 0.0
            ),
        }
    
    def get_health_status(self) -> dict[str, Any]:
        """
        Get health status of all collectors.
        
        Returns:
            Dictionary with health status information
        """
        now = datetime.now(timezone.utc)
        healthy_collectors = []
        degraded_collectors = []
        failing_collectors = []
        
        for name, metrics in self._metrics.items():
            # Check if collector has run recently
            if metrics.last_run_at:
                age = now - metrics.last_run_at
                
                # Check success rate
                if metrics.success_rate >= 95:
                    healthy_collectors.append(name)
                elif metrics.success_rate >= 80:
                    degraded_collectors.append(name)
                else:
                    failing_collectors.append(name)
            else:
                # Never run
                failing_collectors.append(name)
        
        # Determine overall health
        if failing_collectors:
            overall_health = "unhealthy"
        elif degraded_collectors:
            overall_health = "degraded"
        else:
            overall_health = "healthy"
        
        return {
            "overall_health": overall_health,
            "healthy_collectors": healthy_collectors,
            "degraded_collectors": degraded_collectors,
            "failing_collectors": failing_collectors,
            "total_collectors": len(self._metrics),
        }
    
    def reset_metrics(self, collector_name: str | None = None) -> None:
        """
        Reset metrics for a specific collector or all collectors.
        
        Args:
            collector_name: Name of collector to reset, or None for all
        """
        if collector_name:
            if collector_name in self._metrics:
                self._metrics[collector_name] = CollectorMetrics(collector_name)
                logger.info(f"Metrics reset for {collector_name}")
        else:
            self._metrics.clear()
            self._started_at = datetime.now(timezone.utc)
            logger.info("All metrics reset")


# Singleton instance
_metrics_tracker: MetricsTracker | None = None


def get_metrics_tracker() -> MetricsTracker:
    """Get or create the metrics tracker singleton."""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker
