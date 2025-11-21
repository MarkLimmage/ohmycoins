"""
Algorithm Scheduler Service

Manages scheduled execution of deployed algorithms:
1. Per-algorithm execution frequency configuration
2. Concurrent execution management
3. Start/stop/pause algorithm control
4. Resource allocation and error recovery
5. Integration with APScheduler (reusing from Phase 2.5)

Phase 6, Weeks 3-4
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
from sqlmodel import Session, select

from app.models import DeployedAlgorithm, Algorithm
from app.services.trading.algorithm_executor import AlgorithmExecutor, get_algorithm_executor
from app.core.db import engine

logger = logging.getLogger(__name__)


class AlgorithmSchedulerError(Exception):
    """Exception raised when scheduler operation fails"""
    pass


class AlgorithmScheduler:
    """
    Manages scheduled execution of trading algorithms
    
    Responsible for:
    - Starting/stopping algorithm execution on a schedule
    - Managing concurrent algorithm execution
    - Handling execution errors and retries
    - Resource allocation across algorithms
    """
    
    def __init__(self, scheduler: AsyncIOScheduler | None = None):
        """
        Initialize algorithm scheduler
        
        Args:
            scheduler: APScheduler instance (creates new if None)
        """
        self.scheduler = scheduler or AsyncIOScheduler()
        self._job_map: dict[UUID, str] = {}  # deployment_id -> job_id mapping
        self._running = False
    
    def start(self) -> None:
        """Start the scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Algorithm scheduler started")
    
    def shutdown(self) -> None:
        """Shutdown the scheduler"""
        if self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Algorithm scheduler shutdown")
    
    async def schedule_deployment(
        self,
        deployment_id: UUID,
        execution_frequency: int | None = None,
    ) -> str:
        """
        Schedule a deployed algorithm for execution
        
        Args:
            deployment_id: UUID of the DeployedAlgorithm
            execution_frequency: Execution frequency in seconds (uses deployment default if None)
            
        Returns:
            Job ID from scheduler
            
        Raises:
            AlgorithmSchedulerError: If scheduling fails
        """
        try:
            # Load deployment to get frequency
            with Session(engine) as session:
                statement = select(DeployedAlgorithm).where(DeployedAlgorithm.id == deployment_id)
                deployment = session.exec(statement).first()
                
                if not deployment:
                    raise AlgorithmSchedulerError(f"Deployment {deployment_id} not found")
                
                if not deployment.is_active:
                    raise AlgorithmSchedulerError(f"Deployment {deployment_id} is not active")
                
                frequency = execution_frequency or deployment.execution_frequency
            
            # Check if already scheduled
            if deployment_id in self._job_map:
                logger.warning(f"Deployment {deployment_id} already scheduled, removing old job")
                await self.unschedule_deployment(deployment_id)
            
            # Create job
            job = self.scheduler.add_job(
                func=self._execute_deployment_job,
                trigger=IntervalTrigger(seconds=frequency),
                args=[deployment_id],
                id=f"deployment_{deployment_id}",
                name=f"Execute deployment {deployment_id}",
                replace_existing=True,
                max_instances=1,  # Prevent concurrent execution of same deployment
                coalesce=True,  # Coalesce missed runs
            )
            
            self._job_map[deployment_id] = job.id
            
            logger.info(
                f"Scheduled deployment {deployment_id}: "
                f"frequency={frequency}s, job_id={job.id}"
            )
            
            return job.id
            
        except Exception as e:
            logger.exception(f"Failed to schedule deployment {deployment_id}: {str(e)}")
            raise AlgorithmSchedulerError(f"Scheduling failed: {str(e)}") from e
    
    async def unschedule_deployment(self, deployment_id: UUID) -> bool:
        """
        Remove a deployed algorithm from the schedule
        
        Args:
            deployment_id: UUID of the DeployedAlgorithm
            
        Returns:
            True if unscheduled, False if not found
        """
        if deployment_id not in self._job_map:
            logger.warning(f"Deployment {deployment_id} not scheduled")
            return False
        
        job_id = self._job_map[deployment_id]
        
        try:
            self.scheduler.remove_job(job_id)
            del self._job_map[deployment_id]
            
            logger.info(f"Unscheduled deployment {deployment_id}, job_id={job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unschedule deployment {deployment_id}: {str(e)}")
            return False
    
    async def pause_deployment(self, deployment_id: UUID) -> bool:
        """
        Pause execution of a deployed algorithm (keeps in schedule but doesn't execute)
        
        Args:
            deployment_id: UUID of the DeployedAlgorithm
            
        Returns:
            True if paused, False if not found
        """
        if deployment_id not in self._job_map:
            logger.warning(f"Deployment {deployment_id} not scheduled")
            return False
        
        job_id = self._job_map[deployment_id]
        
        try:
            self.scheduler.pause_job(job_id)
            
            logger.info(f"Paused deployment {deployment_id}, job_id={job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause deployment {deployment_id}: {str(e)}")
            return False
    
    async def resume_deployment(self, deployment_id: UUID) -> bool:
        """
        Resume execution of a paused deployed algorithm
        
        Args:
            deployment_id: UUID of the DeployedAlgorithm
            
        Returns:
            True if resumed, False if not found
        """
        if deployment_id not in self._job_map:
            logger.warning(f"Deployment {deployment_id} not scheduled")
            return False
        
        job_id = self._job_map[deployment_id]
        
        try:
            self.scheduler.resume_job(job_id)
            
            logger.info(f"Resumed deployment {deployment_id}, job_id={job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume deployment {deployment_id}: {str(e)}")
            return False
    
    async def _execute_deployment_job(self, deployment_id: UUID) -> None:
        """
        Execute a deployed algorithm (called by scheduler)
        
        This is the function that gets called on schedule.
        It creates a database session and executor, then runs the algorithm.
        
        Args:
            deployment_id: UUID of the DeployedAlgorithm to execute
        """
        try:
            logger.debug(f"Executing scheduled deployment {deployment_id}")
            
            # Create database session and executor
            with Session(engine) as session:
                executor = get_algorithm_executor(session)
                
                # Execute algorithm (not dry run - this is production)
                result = await executor.execute_algorithm(
                    deployment_id=deployment_id,
                    dry_run=False,
                )
                
                logger.info(
                    f"Scheduled execution complete: deployment={deployment_id}, "
                    f"signals={len(result['signals'])}, "
                    f"orders={result['orders_submitted']}, "
                    f"time={result['execution_time_ms']:.2f}ms"
                )
                
        except Exception as e:
            logger.exception(f"Scheduled execution failed for deployment {deployment_id}: {str(e)}")
            # Don't raise - scheduler will retry on next interval
    
    async def schedule_all_active_deployments(self) -> int:
        """
        Schedule all active deployments from database
        
        Useful for startup - loads all active deployments and schedules them.
        
        Returns:
            Number of deployments scheduled
        """
        count = 0
        
        try:
            with Session(engine) as session:
                # Get all active deployments
                statement = select(DeployedAlgorithm).where(DeployedAlgorithm.is_active == True)
                deployments = session.exec(statement).all()
                
                for deployment in deployments:
                    try:
                        await self.schedule_deployment(deployment.id)
                        count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to schedule deployment {deployment.id}: {str(e)}"
                        )
            
            logger.info(f"Scheduled {count} active deployments")
            return count
            
        except Exception as e:
            logger.exception(f"Failed to schedule active deployments: {str(e)}")
            return count
    
    def get_scheduled_jobs(self) -> list[dict]:
        """
        Get list of currently scheduled jobs
        
        Returns:
            List of job info dicts with id, name, next_run_time, etc.
        """
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        
        return jobs
    
    def is_deployment_scheduled(self, deployment_id: UUID) -> bool:
        """Check if a deployment is currently scheduled"""
        return deployment_id in self._job_map
    
    def get_deployment_job_id(self, deployment_id: UUID) -> str | None:
        """Get the job ID for a scheduled deployment"""
        return self._job_map.get(deployment_id)


# Global scheduler instance (singleton)
_scheduler_instance: AlgorithmScheduler | None = None


def get_algorithm_scheduler() -> AlgorithmScheduler:
    """
    Get or create global algorithm scheduler instance
    
    Returns:
        AlgorithmScheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AlgorithmScheduler()
    return _scheduler_instance


async def start_algorithm_scheduler() -> AlgorithmScheduler:
    """
    Start the global algorithm scheduler and schedule all active deployments
    
    Should be called on application startup.
    
    Returns:
        AlgorithmScheduler instance
    """
    scheduler = get_algorithm_scheduler()
    scheduler.start()
    
    # Schedule all active deployments from database
    count = await scheduler.schedule_all_active_deployments()
    logger.info(f"Algorithm scheduler started with {count} active deployments")
    
    return scheduler


async def stop_algorithm_scheduler() -> None:
    """
    Stop the global algorithm scheduler
    
    Should be called on application shutdown.
    """
    global _scheduler_instance
    if _scheduler_instance is not None:
        _scheduler_instance.shutdown()
        _scheduler_instance = None
        logger.info("Algorithm scheduler stopped")
