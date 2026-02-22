# mypy: ignore-errors
"""
Scheduled Task Runner for Cryptocurrency Data Collection

This module provides a scheduler that runs the Coinspot collector at 5-minute intervals.
It uses APScheduler for reliable task scheduling with error handling and logging.
"""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.collector import run_collector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CollectorScheduler:
    """Scheduler for running the Coinspot data collector at regular intervals"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Start the scheduler with a 5-minute cron job"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Schedule collector to run every 5 minutes (at :00, :05, :10, etc.)
        self.scheduler.add_job(
            self._run_collection_job,
            trigger=CronTrigger(minute="*/5"),  # Every 5 minutes
            id="coinspot_collector",
            name="Coinspot Price Collector",
            replace_existing=True,
            max_instances=1,  # Prevent overlapping runs
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("Scheduler started. Collector will run every 5 minutes")

    def stop(self):
        """Stop the scheduler gracefully"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Scheduler stopped")

    async def _run_collection_job(self):
        """
        Internal method that wraps the collector with error handling and metrics
        This is called by the scheduler
        """
        start_time = datetime.now()
        try:
            logger.info(f"Starting scheduled collection at {start_time}")
            records_stored = await run_collector()

            elapsed_seconds = (datetime.now() - start_time).total_seconds()

            if records_stored > 0:
                logger.info(
                    f"Scheduled collection completed successfully: "
                    f"{records_stored} records stored in {elapsed_seconds:.2f}s"
                )
            else:
                logger.warning(
                    f"Scheduled collection completed with no records stored "
                    f"(duration: {elapsed_seconds:.2f}s)"
                )

        except Exception as e:
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Error in scheduled collection after {elapsed_seconds:.2f}s: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )

    async def run_now(self):
        """Manually trigger a collection run (for testing or immediate execution)"""
        logger.info("Manual collection triggered")
        await self._run_collection_job()


# Global scheduler instance
_scheduler_instance: CollectorScheduler | None = None


def get_scheduler() -> CollectorScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CollectorScheduler()
    return _scheduler_instance


async def start_scheduler():
    """Start the collection scheduler (called at application startup)"""
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Collection scheduler initialized")


async def stop_scheduler():
    """Stop the collection scheduler (called at application shutdown)"""
    scheduler = get_scheduler()
    scheduler.stop()
    logger.info("Collection scheduler shut down")


if __name__ == "__main__":
    # For testing the scheduler standalone
    async def test_scheduler():
        scheduler = CollectorScheduler()
        scheduler.start()

        # Run immediately for testing
        await scheduler.run_now()

        # Keep running for 15 minutes to see scheduled executions
        logger.info("Scheduler running. Will collect data every 5 minutes. Press Ctrl+C to stop.")
        try:
            await asyncio.sleep(900)  # 15 minutes
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
        finally:
            scheduler.stop()

    asyncio.run(test_scheduler())
