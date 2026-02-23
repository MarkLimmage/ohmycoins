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


    def load_jobs_from_db(self) -> None:
        """
        Refresh jobs from the database configuration.
        This removes existing jobs and re-registers them based on the DB state.
        """
        from sqlmodel import Session, select
        from app.core.db import engine
        from app.models import Collector
        from app.core.collectors.registry import CollectorRegistry
        from app.services.collectors.strategy_adapter import StrategyAdapterCollector

        logger.info("Loading collector jobs from database...")
        
        # Ensure strategies are discovered/registered
        CollectorRegistry.discover_strategies()
        
        # Clear known collectors to avoid staleness
        current_job_ids = {job.id for job in self.scheduler.get_jobs()}
        
        with Session(engine) as session:
            db_collectors = session.exec(select(Collector).where(Collector.is_enabled == True)).all()
            
            active_ids = set()
            
            for db_coll in db_collectors:
                try:
                    active_ids.add(str(db_coll.id))
                    
                    # Check if strategy exists
                    strategy_cls = CollectorRegistry.get_strategy(db_coll.plugin_name)
                    if not strategy_cls:
                        logger.warning(f"Plugin {db_coll.plugin_name} not found for collector {db_coll.name}")
                        continue
                        
                    # Instantiate strategy
                    strategy = strategy_cls()
                    
                    # Create adapter
                    # TODO: Determine ledger name from strategy or config
                    ledger = "mixed" 
                    if "exchange" in db_coll.plugin_name.lower():
                        ledger = "exchange"
                    elif "news" in db_coll.plugin_name.lower() or "reddit" in db_coll.plugin_name.lower():
                        ledger = "human"
                        
                    adapter = StrategyAdapterCollector(
                        strategy,
                        ledger_name=ledger,
                        default_config=db_coll.config
                    )
                    
                    # Override name to match DB name so distinct instances work
                    adapter.name = db_coll.name 
                    
                    # Register/Update Job
                    # Determine trigger
                    trigger_args = {}
                    # Simple heuristic for cron string vs interval
                    # This needs a robust parser or assumption. 
                    # Assuming basic 5-part cron or exact kwargs passed in some other way?
                    # For now, let's support Interval if the string looks like "interval:5m" or use CronTrigger
                    
                    try:
                        trigger = CronTrigger.from_crontab(db_coll.schedule_cron)
                        
                        self.scheduler.add_job(
                            adapter.run,
                            trigger=trigger,
                            id=str(db_coll.id),
                            name=f"{ledger}/{db_coll.name}",
                            replace_existing=True,
                        )
                        # Also track in our local dict for manual triggers (using string ID)
                        self.collectors[str(db_coll.id)] = adapter
                        
                        logger.info(f"Loaded job: {db_coll.name} (ID: {db_coll.id})")
                    except Exception as e:
                        logger.error(f"Invalid cron for {db_coll.name}: {e}")

                except Exception as e:
                    logger.error(f"Error loading collector {db_coll.name}: {e}")

            # Remove jobs that are no longer enabled/present
            for job_id in current_job_ids:
                if job_id not in active_ids:
                    # Don't remove system jobs if we still have some hardcoded ones?
                    # For now, assumtion is PURE DB driven implies we remove anything not in DB.
                    # Verify if job_id is an integer (DB id)
                    if job_id.isdigit():
                         try:
                            self.scheduler.remove_job(job_id)
                            logger.info(f"Removed stale job: {job_id}")
                         except:
                            pass

    def start(self) -> None:
        """
        Start the collection orchestrator.
        Also starts a background poller to refresh jobs from DB.
        """
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            
            # Add a self-maintenance job to refresh configuration every minute
            self.scheduler.add_job(
                self.load_jobs_from_db,
                trigger=IntervalTrigger(minutes=1),
                id="orchestrator_refresh",
                name="System/ConfigRefresh",
                replace_existing=True
            )
            
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
