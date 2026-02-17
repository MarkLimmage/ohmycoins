"""
Collection orchestrator for managing all data collectors in Phase 2.5.

This module provides the orchestrator that coordinates the execution of all
collectors according to their schedules, manages resources, and provides
health monitoring.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from .base import BaseCollector

logger = logging.getLogger(__name__)


class CollectionOrchestrator:
    """
    Orchestrates the execution of all data collectors.
    
    Responsibilities:
    - Register collectors with their schedules
    - Start/stop the collection scheduler
    - Monitor collector health
    - Provide metrics and status endpoints
    """
    
    def __init__(self) -> None:
        """Initialize the orchestrator with an async scheduler."""
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.collectors: dict[str, BaseCollector] = {}
        self._is_running = False
    
    def register_collector(
        self,
        collector: BaseCollector,
        schedule_type: str,
        **schedule_kwargs: Any,
    ) -> None:
        """
        Register a collector with a schedule.
        
        Args:
            collector: The collector instance to register
            schedule_type: Type of schedule ("interval" or "cron")
            **schedule_kwargs: Arguments for the schedule trigger
                For interval: seconds, minutes, hours
                For cron: minute, hour, day, day_of_week, etc.
        
        Example:
            # Register for 5-minute intervals
            orchestrator.register_collector(
                my_collector,
                "interval",
                minutes=5
            )
            
            # Register for daily at 2 AM
            orchestrator.register_collector(
                my_collector,
                "cron",
                hour=2,
                minute=0
            )
        """
        self.collectors[collector.name] = collector
        
        if schedule_type == "interval":
            trigger = IntervalTrigger(**schedule_kwargs, timezone="UTC")
        elif schedule_type == "cron":
            trigger = CronTrigger(**schedule_kwargs, timezone="UTC")
        else:
            raise ValueError(f"Invalid schedule_type: {schedule_type}")
        
        self.scheduler.add_job(
            collector.run,
            trigger=trigger,
            id=collector.name,
            name=f"{collector.ledger}/{collector.name}",
            replace_existing=True,
        )
        
        logger.info(
            f"Registered collector: {collector.name} "
            f"with {schedule_type} schedule: {schedule_kwargs}"
        )
    
    def start(self) -> None:
        """
        Start the collection scheduler.
        
        All registered collectors will begin running according to their schedules.
        """
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info(
                f"Collection orchestrator started with {len(self.collectors)} collectors"
            )
        else:
            logger.warning("Collection orchestrator is already running")
    
    def stop(self) -> None:
        """
        Stop the collection scheduler.
        
        All running collectors will be gracefully stopped.
        """
        if self._is_running:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Collection orchestrator stopped")
        else:
            logger.warning("Collection orchestrator is not running")
    
    async def trigger_manual(self, collector_name: str) -> bool:
        """
        Manually trigger a collector to run immediately.
        
        Args:
            collector_name: Name of the collector to trigger
        
        Returns:
            True if collector ran successfully, False otherwise
        
        Raises:
            KeyError: If collector name is not found
        """
        if collector_name not in self.collectors:
            raise KeyError(f"Collector not found: {collector_name}")
        
        collector = self.collectors[collector_name]
        logger.info(f"Manually triggering collector: {collector_name}")
        
        return await collector.run()
    
    def get_health_status(self) -> dict[str, Any]:
        """
        Get health status of all collectors.
        
        Returns:
            Dictionary containing:
            - orchestrator status (running/stopped)
            - collector count
            - individual collector statuses
            - last update timestamp
        """
        return {
            "orchestrator_status": "running" if self._is_running else "stopped",
            "collector_count": len(self.collectors),
            "collectors": [
                collector.get_status() for collector in self.collectors.values()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def get_collector_status(self, collector_name: str) -> dict[str, Any]:
        """
        Get status of a specific collector.
        
        Args:
            collector_name: Name of the collector
        
        Returns:
            Dictionary containing collector status and metrics
        
        Raises:
            KeyError: If collector name is not found
        """
        if collector_name not in self.collectors:
            raise KeyError(f"Collector not found: {collector_name}")
        
        return self.collectors[collector_name].get_status()


# Global orchestrator instance
_orchestrator: CollectionOrchestrator | None = None


def get_orchestrator() -> CollectionOrchestrator:
    """
    Get the global orchestrator instance (singleton pattern).
    
    Returns:
        The global CollectionOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CollectionOrchestrator()
    return _orchestrator
