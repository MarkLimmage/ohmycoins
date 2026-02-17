# mypy: ignore-errors
"""
Execution Scheduler for Trading Algorithms

This module schedules and manages the execution of trading algorithms
at configured frequencies.
"""
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session, select

from app.models import Algorithm, DeployedAlgorithm
from app.services.trading.algorithm_executor import (
    TradingAlgorithm,
    get_algorithm_executor,
)
from app.services.trading.client import CoinspotTradingClient
from app.services.trading.exceptions import SchedulerError
from app.services.trading.strategies.ma_crossover import MACrossoverStrategy

logger = logging.getLogger(__name__)


class ExecutionScheduler:
    """
    Schedules and manages algorithm execution

    Features:
    - Per-algorithm execution frequency configuration
    - Concurrent execution management
    - Resource allocation
    - Error recovery
    - Health monitoring
    """

    def __init__(
        self,
        session: Session,
        api_key: str,
        api_secret: str,
        market_data_provider: Any | None = None
    ):
        """
        Initialize execution scheduler

        Args:
            session: Database session
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            market_data_provider: Market data provider (optional)
        """
        self.session = session
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_data_provider = market_data_provider
        self.executor = get_algorithm_executor(session, api_key, api_secret)
        self.scheduler = AsyncIOScheduler()
        self._running = False
        self._scheduled_algorithms: dict[str, dict[str, Any]] = {}

    def start(self) -> None:
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.start()
        self._running = True
        logger.info("Execution scheduler started")

    def stop(self) -> None:
        """Stop the scheduler"""
        if not self._running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("Execution scheduler stopped")

    def load_deployed_algorithms(self) -> int:
        """
        Load active deployed algorithms from the database and schedule them.

        Returns:
            Number of algorithms scheduled
        """
        logger.info("Loading deployed algorithms from database...")
        stmt = select(DeployedAlgorithm, Algorithm).join(Algorithm).where(DeployedAlgorithm.is_active is True)
        results = self.session.exec(stmt).all()

        count = 0
        for deployed_algo, algo_def in results:
            try:
                # Instantiate based on algorithm type/name - minimal implementation for Sprint 2.26
                algorithm_instance = None

                # Simple dispatch logic (to be replaced by a proper registry in Phase 3)
                if "MA Crossover" in algo_def.name or "MACrossover" in algo_def.name:
                    # Parse parameters
                    params = {}
                    if deployed_algo.parameters_json:
                        try:
                            params = json.loads(deployed_algo.parameters_json)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid parameters JSON for deployment {deployed_algo.id}")

                    # Defaults
                    short_window = params.get('short_window', 10)
                    long_window = params.get('long_window', 50)
                    coin_type = params.get('coin_type', 'BTC')

                    algorithm_instance = MACrossoverStrategy(
                        short_window=short_window,
                        long_window=long_window,
                        coin_type=coin_type
                    )

                if algorithm_instance:
                    # Calculate frequency
                    freq_seconds = deployed_algo.execution_frequency or algo_def.default_execution_frequency or 300
                    frequency = f"interval:{freq_seconds}:seconds"

                    self.schedule_algorithm(
                        user_id=deployed_algo.user_id,
                        algorithm_id=deployed_algo.algorithm_id,  # Use Algorithm ID for uniqueness per user/algo pair
                        algorithm=algorithm_instance,
                        frequency=frequency
                    )
                    count += 1
                else:
                    logger.warning(f"Unknown algorithm type for deployment {deployed_algo.id}: {algo_def.name}")

            except Exception as e:
                logger.error(f"Failed to load deployment {deployed_algo.id}: {e}")

        logger.info(f"Loaded {count} active algorithms from database")
        return count

    def schedule_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        algorithm: TradingAlgorithm,
        frequency: str,
        **kwargs
    ) -> str:
        """
        Schedule an algorithm for execution

        Args:
            user_id: User ID
            algorithm_id: Algorithm ID
            algorithm: Algorithm implementation
            frequency: Execution frequency
                - 'interval:N:unit' for interval (e.g., 'interval:5:minutes')
                - 'cron:expression' for cron (e.g., 'cron:0 */4 * * *')
            **kwargs: Additional scheduler arguments

        Returns:
            Job ID

        Raises:
            SchedulerError: If scheduling fails
        """
        if not self._running:
            raise SchedulerError("Scheduler is not running")

        job_id = f"{user_id}_{algorithm_id}"

        # Parse frequency
        trigger = self._parse_frequency(frequency)

        # Add job to scheduler
        try:
            self.scheduler.add_job(
                func=self._execute_algorithm_job,
                trigger=trigger,
                id=job_id,
                args=[user_id, algorithm_id, algorithm],
                replace_existing=True,
                **kwargs
            )

            # Track scheduled algorithm
            self._scheduled_algorithms[job_id] = {
                'user_id': user_id,
                'algorithm_id': algorithm_id,
                'frequency': frequency,
                'scheduled_at': datetime.now(timezone.utc),
                'last_execution': None,
                'execution_count': 0,
                'error_count': 0
            }

            logger.info(
                f"Algorithm {algorithm_id} scheduled for user {user_id} "
                f"with frequency: {frequency}"
            )

            return job_id

        except Exception as e:
            logger.error(f"Error scheduling algorithm {algorithm_id}: {e}")
            raise SchedulerError(f"Failed to schedule algorithm: {e}")

    def _parse_frequency(self, frequency: str) -> Any:
        """
        Parse frequency string into APScheduler trigger

        Args:
            frequency: Frequency string

        Returns:
            APScheduler trigger

        Raises:
            SchedulerError: If frequency format is invalid
        """
        parts = frequency.split(':', 1)

        if len(parts) != 2:
            raise SchedulerError(f"Invalid frequency format: {frequency}")

        freq_type, freq_value = parts

        if freq_type == 'interval':
            # Parse interval: N:unit (e.g., "5:minutes")
            interval_parts = freq_value.split(':', 1)
            if len(interval_parts) != 2:
                raise SchedulerError(f"Invalid interval format: {freq_value}")

            try:
                value = int(interval_parts[0])
                unit = interval_parts[1]

                # Create interval trigger
                kwargs = {unit: value}
                return IntervalTrigger(**kwargs)

            except (ValueError, TypeError) as e:
                raise SchedulerError(f"Invalid interval value: {e}")

        elif freq_type == 'cron':
            # Parse cron expression
            try:
                # Split cron expression (minute hour day month day_of_week)
                cron_parts = freq_value.split()
                if len(cron_parts) != 5:
                    raise SchedulerError(f"Invalid cron expression: {freq_value}")

                return CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4]
                )

            except Exception as e:
                raise SchedulerError(f"Invalid cron expression: {e}")

        else:
            raise SchedulerError(f"Unknown frequency type: {freq_type}")

    async def _execute_algorithm_job(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        algorithm: TradingAlgorithm
    ) -> None:
        """
        Execute algorithm job (called by scheduler)

        Args:
            user_id: User ID
            algorithm_id: Algorithm ID
            algorithm: Algorithm implementation
        """
        job_id = f"{user_id}_{algorithm_id}"

        logger.info(f"Executing scheduled algorithm job: {job_id}")

        try:
            # Get market data
            market_data = await self._get_market_data()

            # Execute algorithm
            result = await self.executor.execute_algorithm(
                user_id=user_id,
                algorithm_id=algorithm_id,
                algorithm=algorithm,
                market_data=market_data
            )

            # Update tracking
            if job_id in self._scheduled_algorithms:
                self._scheduled_algorithms[job_id]['last_execution'] = datetime.now(timezone.utc)
                self._scheduled_algorithms[job_id]['execution_count'] += 1

            logger.info(f"Algorithm job {job_id} completed: {result}")

        except Exception as e:
            logger.error(f"Error executing algorithm job {job_id}: {e}", exc_info=True)

            # Update error tracking
            if job_id in self._scheduled_algorithms:
                self._scheduled_algorithms[job_id]['error_count'] += 1

            # TODO: Implement error threshold and auto-disable failing algorithms (Phase 6 Weeks 7-8 - Advanced Features)

    async def _get_market_data(self) -> dict[str, Any]:
        """
        Get current market data

        Returns:
            Dictionary with market data
        """
        if self.market_data_provider:
            # Use custom market data provider if available
            return await self.market_data_provider.get_data()

        # Fallback: Fetch from Coinspot API
        try:
            async with CoinspotTradingClient(self.api_key, self.api_secret) as client:
                # Fetch latest prices for common coins
                prices = await client._get_public_price('BTC', 'buy')
                eth_price = await client._get_public_price('ETH', 'buy')
                doge_price = await client._get_public_price('DOGE', 'buy')

                market_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'prices': {
                        'BTC': {'last': prices, 'coin_type': 'BTC'},
                        'ETH': {'last': eth_price, 'coin_type': 'ETH'},
                        'DOGE': {'last': doge_price, 'coin_type': 'DOGE'}
                    },
                    # Legacy support for naive strats
                    'price': prices,
                    'coin_type': 'BTC',
                    'BTC': {'price': prices},
                    'ETH': {'price': eth_price},
                    'DOGE': {'price': doge_price}
                }
                return market_data
        except Exception as e:
            logger.error(f"Failed to fetch live market data: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'prices': {},
                'price': Decimal('0'),
                'coin_type': 'BTC'
            }

    def unschedule_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID
    ) -> bool:
        """
        Unschedule an algorithm

        Args:
            user_id: User ID
            algorithm_id: Algorithm ID

        Returns:
            True if algorithm was unscheduled, False if not found
        """
        job_id = f"{user_id}_{algorithm_id}"

        try:
            self.scheduler.remove_job(job_id)

            # Remove from tracking
            if job_id in self._scheduled_algorithms:
                del self._scheduled_algorithms[job_id]

            logger.info(f"Algorithm {algorithm_id} unscheduled for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error unscheduling algorithm {job_id}: {e}")
            return False

    def pause_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID
    ) -> bool:
        """
        Pause an algorithm (keep schedule but don't execute)

        Args:
            user_id: User ID
            algorithm_id: Algorithm ID

        Returns:
            True if algorithm was paused, False if not found
        """
        job_id = f"{user_id}_{algorithm_id}"

        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Algorithm {algorithm_id} paused for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error pausing algorithm {job_id}: {e}")
            return False

    def resume_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID
    ) -> bool:
        """
        Resume a paused algorithm

        Args:
            user_id: User ID
            algorithm_id: Algorithm ID

        Returns:
            True if algorithm was resumed, False if not found
        """
        job_id = f"{user_id}_{algorithm_id}"

        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Algorithm {algorithm_id} resumed for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error resuming algorithm {job_id}: {e}")
            return False

    def get_scheduled_algorithms(self) -> list[dict[str, Any]]:
        """
        Get list of all scheduled algorithms

        Returns:
            List of scheduled algorithm info
        """
        return [
            {
                'job_id': job_id,
                **info,
                'user_id': str(info['user_id']),
                'algorithm_id': str(info['algorithm_id']),
                'scheduled_at': info['scheduled_at'].isoformat() if info['scheduled_at'] else None,
                'last_execution': info['last_execution'].isoformat() if info['last_execution'] else None
            }
            for job_id, info in self._scheduled_algorithms.items()
        ]

    def get_scheduler_status(self) -> dict[str, Any]:
        """
        Get scheduler status

        Returns:
            Dictionary with scheduler status
        """
        return {
            'running': self._running,
            'total_jobs': len(self.scheduler.get_jobs()),
            'scheduled_algorithms': len(self._scheduled_algorithms),
            'state': self.scheduler.state
        }


# Global instance
_execution_scheduler: ExecutionScheduler | None = None


def get_execution_scheduler(
    session: Session,
    api_key: str,
    api_secret: str
) -> ExecutionScheduler:
    """
    Get or create the global execution scheduler instance

    Args:
        session: Database session
        api_key: Coinspot API key
        api_secret: Coinspot API secret

    Returns:
        ExecutionScheduler instance
    """
    global _execution_scheduler
    if _execution_scheduler is None:
        _execution_scheduler = ExecutionScheduler(
            session=session,
            api_key=api_key,
            api_secret=api_secret
        )
    return _execution_scheduler
