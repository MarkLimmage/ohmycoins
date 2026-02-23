"""
Base collector class for all data collectors in Phase 2.5.

This module provides the abstract base class that all collectors must implement,
along with common functionality for error handling, logging, and metrics tracking.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel import Session
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from app.core.db import engine
from app.models import CollectorRuns

logger = logging.getLogger(__name__)


class CollectorStatus(str, Enum):
    """Status enumeration for collector runs"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors.

    Each collector implementation must:
    1. Implement the collect() method to fetch and return data
    2. Implement the validate_data() method to validate collected data
    3. Implement the store_data() method to persist data to the database

    The run() method orchestrates the collection workflow and handles:
    - Error handling and logging
    - Metrics tracking
    - Database transaction management
    - Status tracking in collector_runs table
    """

    def __init__(self, name: str, ledger: str):
        """
        Initialize the collector.

        Args:
            name: Unique name for this collector (e.g., "defillama_api")
            ledger: The ledger this collector belongs to
                   ("glass", "human", "catalyst", "exchange")
        """
        self.name = name
        self.ledger = ledger
        self.status = CollectorStatus.IDLE
        self.last_run: datetime | None = None
        self.error_count = 0
        self.success_count = 0

    @abstractmethod
    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect data from the source.

        Returns:
            List of dictionaries containing the raw collected data.
            Each dict should represent one data point/record.

        Raises:
            Exception: If data collection fails
        """
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def _collect_with_retry(self) -> list[dict[str, Any]]:
        """
        Wrapper around collect() to provide retry logic.
        """
        return await self.collect()

    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected data.
        
        Default implementation checks if data is a list. Subclasses can override for specific validation.

        Args:
            data: Raw data collected from the source

        Returns:
            Validated and cleaned data ready for storage

        Raises:
            ValueError: If data validation fails, e.g., if data is not a list.
        """
        if not isinstance(data, list):
            raise ValueError(f"Collected data must be a list, got {type(data)}")
        return data

    @abstractmethod
    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated data in the database.

        Args:
            data: Validated data to store
            session: Database session for transaction management

        Returns:
            Number of records successfully stored

        Raises:
            Exception: If database operations fail
        """
        pass

    async def run(self) -> bool:
        """
        Execute the complete collection workflow with error handling.

        Workflow:
        1. Update status to RUNNING
        2. Collect data from source
        3. Validate collected data
        4. Store data in database
        5. Update metrics and status
        6. Log results

        Returns:
            True if collection succeeded, False otherwise
        """
        self.status = CollectorStatus.RUNNING
        self.last_run = datetime.now(timezone.utc)
        started_at = self.last_run
        run_id = None
        records_collected = 0

        logger.info(f"Starting collector: {self.name} (ledger: {self.ledger})")

        try:
            with Session(engine) as session:
                # Create collector run record
                collector_run = CollectorRuns(
                    collector_name=self.name,
                    status=CollectorStatus.RUNNING,
                    started_at=started_at
                )
                session.add(collector_run)
                session.commit()
                session.refresh(collector_run)
                run_id = collector_run.id

                # Collect data
                logger.debug(f"{self.name}: Collecting data...")
                raw_data = await self._collect_with_retry()
                logger.debug(f"{self.name}: Collected {len(raw_data)} raw records")

                # Validate data
                logger.debug(f"{self.name}: Validating data...")
                validated_data = await self.validate_data(raw_data)
                logger.debug(f"{self.name}: Validated {len(validated_data)} records")

                # Store data
                logger.debug(f"{self.name}: Storing data...")
                records_collected = await self.store_data(validated_data, session)
                logger.info(
                    f"{self.name}: Successfully stored {records_collected} records"
                )

                # Update collector run record
                collector_run.status = CollectorStatus.SUCCESS
                collector_run.completed_at = datetime.now(timezone.utc)
                collector_run.records_collected = records_collected
                session.add(collector_run)
                session.commit()

                # Update metrics
                self.status = CollectorStatus.SUCCESS
                self.success_count += 1

                return True

        except Exception as e:
            logger.error(
                f"{self.name}: Collection failed: {str(e)}",
                exc_info=True
            )

            # Update collector run record with error
            if run_id:
                try:
                    with Session(engine) as session:
                        failed_run = session.get(CollectorRuns, run_id)
                        if failed_run:
                            failed_run.status = CollectorStatus.FAILED
                            failed_run.completed_at = datetime.now(timezone.utc)
                            failed_run.error_message = str(e)[:1000]  # Truncate long errors
                            session.add(failed_run)
                            session.commit()
                except Exception as db_error:
                    logger.error(
                        f"{self.name}: Failed to update collector run: {str(db_error)}"
                    )

            # Update metrics
            self.status = CollectorStatus.FAILED
            self.error_count += 1

            return False

    def get_status(self) -> dict[str, Any]:
        """
        Get current collector status and metrics.

        Returns:
            Dictionary containing collector status and metrics
        """
        return {
            "name": self.name,
            "ledger": self.ledger,
            "status": self.status.value,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }
