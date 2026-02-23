# mypy: ignore-errors
"""
Database-Driven Scheduler for Data Collection

This module replaces the legacy in-memory scheduler. It reads from the `collector` table
and schedules jobs dynamically based on cron expressions stored in the database.
It supports both legacy Coinspot collector and new plugin-based strategies.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.core.db import engine
from app.models import Collector, CollectorRuns
from app.core.collectors.registry import CollectorRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseScheduler:
    """
    Scheduler that loads jobs from the database (Collector table).
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Start the scheduler and load jobs"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.start()
        self.is_running = True
        logger.info("DatabaseScheduler started")
        self.refresh_jobs()

    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("DatabaseScheduler stopped")

    def refresh_jobs(self):
        """
        Reload all enabled jobs from the database.
        This should be called whenever a schedule is updated.
        """
        self.scheduler.remove_all_jobs()
        
        with Session(engine) as session:
            try:
                # Select only enabled collectors
                collectors = session.exec(select(Collector).where(Collector.is_enabled == True)).all()
                
                count = 0
                for collector in collectors:
                    try:
                        # Use cron trigger. Assuming schedule_cron is valid cron string.
                        # apscheduler CronTrigger.from_crontab handles standard cron strings.
                        trigger = CronTrigger.from_crontab(collector.schedule_cron)
                        
                        self.scheduler.add_job(
                            self.run_job,
                            trigger=trigger,
                            id=str(collector.id),
                            name=f"{collector.name} ({collector.plugin_name})",
                            args=[collector.id],
                            replace_existing=True,
                            max_instances=1
                        )
                        count += 1
                        logger.info(f"Scheduled job for collector: {collector.name} ({collector.schedule_cron})")
                    except Exception as e:
                        logger.error(f"Failed to schedule collector {collector.name} (ID: {collector.id}): {e}")
                
                logger.info(f"Loaded {count} collector jobs from database")
            except Exception as e:
                logger.error(f"Error refreshing jobs: {e}")

    async def run_job(self, collector_id: int):
        """
        Execute a specific collector job by ID.
        This updates the database status and history.
        """
        with Session(engine) as session:
            collector = session.get(Collector, collector_id)
            if not collector:
                logger.error(f"Collector {collector_id} not found during execution")
                return

            # Avoid concurrent runs if status is running? 
            # (Optional, but APScheduler max_instances=1 handles per-job concurrency)
            
            # Create run record
            run_record = CollectorRuns(
                collector_name=collector.name,
                status="running",
                started_at=datetime.now(timezone.utc)
            )
            session.add(run_record)
            
            # Update collector status
            collector.status = "running"
            collector.last_run_at = datetime.now(timezone.utc)
            session.add(collector)
            session.commit()
            session.refresh(run_record)

            try:
                # Execute Logic
                records_count = 0
                error_msg = None
                
                logger.info(f"Executing collector: {collector.name}")

                # Ensure plugins are discovered
                CollectorRegistry.discover_strategies()
                
                # Check for legacy mapping
                plugin_name = collector.plugin_name
                if plugin_name == "coinspot_price":
                    plugin_name = "CoinspotExchange"

                strategy_cls = CollectorRegistry.get_strategy(plugin_name)
                
                if strategy_cls:
                    strategy = strategy_cls()
                    # Execute strategy
                    # Note: strategy.collect returns a list of items.
                    # TODO: Implement generic storage for these items.
                    # For now, we mainly focus on executing it.
                    results = await strategy.collect(collector.config)
                    records_count = len(results) if results else 0
                    logger.info(f"Strategy {plugin_name} returned {records_count} items")
                else:
                    raise ValueError(f"Unknown plugin type: {plugin_name}")

                # Success
                run_record.status = "completed"
                run_record.completed_at = datetime.now(timezone.utc)
                run_record.records_collected = records_count
                
                collector.status = "idle"

            except Exception as e:
                logger.error(f"Error running collector {collector.name}: {e}", exc_info=True)
                run_record.status = "error"
                run_record.completed_at = datetime.now(timezone.utc)
                run_record.error_message = str(e)
                
                collector.status = "error"
            
            finally:
                session.add(run_record)
                session.add(collector)
                session.commit()

    async def run_now(self, collector_id: int):
        """Manually trigger a job immediately"""
        await self.run_job(collector_id)


# Global scheduler instance
_scheduler_instance: DatabaseScheduler | None = None


def get_scheduler() -> DatabaseScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = DatabaseScheduler()
    return _scheduler_instance


async def start_scheduler():
    """Start the collection scheduler (called at application startup)"""
    scheduler = get_scheduler()
    scheduler.start()


async def stop_scheduler():
    """Stop the collection scheduler (called at application shutdown)"""
    scheduler = get_scheduler()
    scheduler.stop()

if __name__ == "__main__":
    # Test block
    pass
