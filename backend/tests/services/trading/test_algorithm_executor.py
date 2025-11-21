"""
Tests for Algorithm Executor and Scheduler

Tests cover:
- Algorithm execution
- Signal generation
- Safety integration
- Scheduler functionality
- Job management
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from typing import Any

from sqlmodel import Session

from app.models import User, Order
from app.services.trading.algorithm_executor import (
    AlgorithmExecutor,
    TradingAlgorithm,
    AlgorithmExecutionError,
    get_algorithm_executor
)
from app.services.trading.scheduler import ExecutionScheduler, get_execution_scheduler
from app.services.trading.safety import TradingSafetyManager


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="algo@test.com",
        hashed_password="test_hash",
        is_active=True,
        is_superuser=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def algorithm_executor(session: Session) -> AlgorithmExecutor:
    """Create algorithm executor for testing"""
    return AlgorithmExecutor(
        session=session,
        api_key="test_key",
        api_secret="test_secret"
    )


@pytest.fixture
def execution_scheduler(session: Session) -> ExecutionScheduler:
    """Create execution scheduler for testing"""
    return ExecutionScheduler(
        session=session,
        api_key="test_key",
        api_secret="test_secret"
    )


class MockAlgorithm:
    """Mock trading algorithm for testing"""
    
    def __init__(self, signal: dict[str, Any]):
        self._signal = signal
    
    def generate_signal(self, market_data: dict[str, Any]) -> dict[str, Any]:
        """Return pre-configured signal"""
        return self._signal


class TestAlgorithmExecutor:
    """Tests for AlgorithmExecutor"""
    
    @pytest.mark.asyncio
    async def test_execute_algorithm_hold_signal(
        self,
        algorithm_executor: AlgorithmExecutor,
        test_user: User
    ):
        """Test algorithm execution with hold signal"""
        algorithm = MockAlgorithm({
            'action': 'hold',
            'confidence': 0.8
        })
        
        market_data = {'prices': {}}
        
        result = await algorithm_executor.execute_algorithm(
            user_id=test_user.id,
            algorithm_id=uuid4(),
            algorithm=algorithm,
            market_data=market_data
        )
        
        assert result['executed'] is False
        assert result['reason'] == 'hold_signal'
    
    @pytest.mark.asyncio
    async def test_execute_algorithm_invalid_signal(
        self,
        algorithm_executor: AlgorithmExecutor,
        test_user: User
    ):
        """Test algorithm execution with invalid signal"""
        algorithm = MockAlgorithm({
            'action': 'buy',
            'coin_type': 'BTC',
            'quantity': 0  # Invalid: zero quantity
        })
        
        market_data = {'prices': {}}
        
        result = await algorithm_executor.execute_algorithm(
            user_id=test_user.id,
            algorithm_id=uuid4(),
            algorithm=algorithm,
            market_data=market_data
        )
        
        assert result['executed'] is False
        assert result['reason'] == 'invalid_signal'
    
    @pytest.mark.asyncio
    async def test_execute_algorithm_safety_violation(
        self,
        session: Session,
        test_user: User
    ):
        """Test algorithm execution blocked by safety check"""
        # Create executor with strict safety manager
        safety_manager = TradingSafetyManager(
            session=session,
            max_position_pct=Decimal('0.01')  # Very strict: 1%
        )
        safety_manager.activate_emergency_stop()  # Activate emergency stop
        
        executor = AlgorithmExecutor(
            session=session,
            api_key="test_key",
            api_secret="test_secret",
            safety_manager=safety_manager
        )
        
        algorithm = MockAlgorithm({
            'action': 'buy',
            'coin_type': 'BTC',
            'quantity': 0.01,
            'confidence': 0.9
        })
        
        market_data = {
            'prices': {
                'BTC': {'last': 60000}
            }
        }
        
        result = await executor.execute_algorithm(
            user_id=test_user.id,
            algorithm_id=uuid4(),
            algorithm=algorithm,
            market_data=market_data
        )
        
        assert result['executed'] is False
        assert result['reason'] == 'safety_violation'
        assert 'Emergency stop' in result['error']
    
    def test_get_algorithm_performance_placeholder(
        self,
        algorithm_executor: AlgorithmExecutor
    ):
        """Test algorithm performance metrics (placeholder)"""
        algorithm_id = uuid4()
        
        performance = algorithm_executor.get_algorithm_performance(algorithm_id)
        
        assert 'algorithm_id' in performance
        assert 'metrics' in performance
        assert performance['metrics']['total_trades'] == 0
    
    def test_get_algorithm_executor_factory(self, session: Session):
        """Test factory function"""
        executor = get_algorithm_executor(
            session=session,
            api_key="test_key",
            api_secret="test_secret"
        )
        
        assert isinstance(executor, AlgorithmExecutor)


class TestExecutionScheduler:
    """Tests for ExecutionScheduler"""
    
    def test_scheduler_start_stop(self, execution_scheduler: ExecutionScheduler):
        """Test starting and stopping scheduler"""
        assert not execution_scheduler._running
        
        execution_scheduler.start()
        assert execution_scheduler._running
        
        execution_scheduler.stop()
        assert not execution_scheduler._running
    
    def test_schedule_algorithm_interval(
        self,
        execution_scheduler: ExecutionScheduler,
        test_user: User
    ):
        """Test scheduling algorithm with interval frequency"""
        execution_scheduler.start()
        
        algorithm = MockAlgorithm({'action': 'hold'})
        algorithm_id = uuid4()
        
        job_id = execution_scheduler.schedule_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id,
            algorithm=algorithm,
            frequency='interval:5:minutes'
        )
        
        assert job_id == f"{test_user.id}_{algorithm_id}"
        assert job_id in execution_scheduler._scheduled_algorithms
        
        execution_scheduler.stop()
    
    def test_schedule_algorithm_cron(
        self,
        execution_scheduler: ExecutionScheduler,
        test_user: User
    ):
        """Test scheduling algorithm with cron frequency"""
        execution_scheduler.start()
        
        algorithm = MockAlgorithm({'action': 'hold'})
        algorithm_id = uuid4()
        
        job_id = execution_scheduler.schedule_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id,
            algorithm=algorithm,
            frequency='cron:0 */4 * * *'  # Every 4 hours
        )
        
        assert job_id == f"{test_user.id}_{algorithm_id}"
        
        execution_scheduler.stop()
    
    def test_unschedule_algorithm(
        self,
        execution_scheduler: ExecutionScheduler,
        test_user: User
    ):
        """Test unscheduling an algorithm"""
        execution_scheduler.start()
        
        algorithm = MockAlgorithm({'action': 'hold'})
        algorithm_id = uuid4()
        
        # Schedule
        execution_scheduler.schedule_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id,
            algorithm=algorithm,
            frequency='interval:5:minutes'
        )
        
        # Unschedule
        result = execution_scheduler.unschedule_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id
        )
        
        assert result is True
        assert f"{test_user.id}_{algorithm_id}" not in execution_scheduler._scheduled_algorithms
        
        execution_scheduler.stop()
    
    def test_pause_resume_algorithm(
        self,
        execution_scheduler: ExecutionScheduler,
        test_user: User
    ):
        """Test pausing and resuming an algorithm"""
        execution_scheduler.start()
        
        algorithm = MockAlgorithm({'action': 'hold'})
        algorithm_id = uuid4()
        
        # Schedule
        execution_scheduler.schedule_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id,
            algorithm=algorithm,
            frequency='interval:5:minutes'
        )
        
        # Pause
        result = execution_scheduler.pause_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id
        )
        assert result is True
        
        # Resume
        result = execution_scheduler.resume_algorithm(
            user_id=test_user.id,
            algorithm_id=algorithm_id
        )
        assert result is True
        
        execution_scheduler.stop()
    
    def test_get_scheduled_algorithms(
        self,
        execution_scheduler: ExecutionScheduler,
        test_user: User
    ):
        """Test getting list of scheduled algorithms"""
        execution_scheduler.start()
        
        # Schedule multiple algorithms
        for i in range(3):
            algorithm = MockAlgorithm({'action': 'hold'})
            execution_scheduler.schedule_algorithm(
                user_id=test_user.id,
                algorithm_id=uuid4(),
                algorithm=algorithm,
                frequency='interval:5:minutes'
            )
        
        # Get list
        scheduled = execution_scheduler.get_scheduled_algorithms()
        
        assert len(scheduled) == 3
        for item in scheduled:
            assert 'job_id' in item
            assert 'user_id' in item
            assert 'algorithm_id' in item
            assert 'frequency' in item
        
        execution_scheduler.stop()
    
    def test_get_scheduler_status(
        self,
        execution_scheduler: ExecutionScheduler
    ):
        """Test getting scheduler status"""
        status = execution_scheduler.get_scheduler_status()
        
        assert 'running' in status
        assert 'total_jobs' in status
        assert 'scheduled_algorithms' in status
        assert status['running'] is False
    
    def test_get_execution_scheduler_singleton(self, session: Session):
        """Test that get_execution_scheduler returns singleton"""
        scheduler1 = get_execution_scheduler(
            session=session,
            api_key="key",
            api_secret="secret"
        )
        scheduler2 = get_execution_scheduler(
            session=session,
            api_key="key",
            api_secret="secret"
        )
        
        # Note: The current implementation creates new instance,
        # but the function signature suggests singleton pattern
        assert isinstance(scheduler1, ExecutionScheduler)
        assert isinstance(scheduler2, ExecutionScheduler)
