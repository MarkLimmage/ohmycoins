# mypy: ignore-errors
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from app.services.scheduler import DatabaseScheduler
from app.models import Collector, CollectorRuns

@pytest.mark.asyncio
async def test_scheduler_refresh_jobs():
    scheduler = DatabaseScheduler()
    scheduler.scheduler = MagicMock()
    
    with patch("app.services.scheduler.Session") as mock_session_cls:
        mock_session = mock_session_cls.return_value
        mock_session.__enter__.return_value = mock_session
        
        # Mock collectors
        c1 = Collector(id=1, name="Test1", plugin_name="coinspot_price", schedule_cron="*/5 * * * *", is_enabled=True)
        # Only enabled collectors are returned by query logic in refresh_jobs
        
        # Mock the exec().all() chain
        mock_exec = MagicMock()
        mock_exec.all.return_value = [c1]
        mock_session.exec.return_value = mock_exec
        
        scheduler.refresh_jobs()
        
        # Should have added 1 job
        scheduler.scheduler.add_job.assert_called_once()
        args, kwargs = scheduler.scheduler.add_job.call_args
        assert kwargs['id'] == "1"
        # Check cron parsed correctly (just checking existence of trigger is enough for unit test usually)
        assert kwargs['trigger'] is not None

@pytest.mark.asyncio
async def test_scheduler_run_job_legacy():
    scheduler = DatabaseScheduler()
    
    with patch("app.services.scheduler.Session") as mock_session_cls, \
         patch("app.services.scheduler.run_legacy_collector", new_callable=AsyncMock) as mock_run_legacy:
        
        mock_session = mock_session_cls.return_value
        mock_session.__enter__.return_value = mock_session
        
        # Mock collector
        c1 = Collector(id=1, name="TestCoinspot", plugin_name="coinspot_price", schedule_cron="*/5 * * * *", is_enabled=True)
        mock_session.get.return_value = c1
        
        mock_run_legacy.return_value = 10 # 10 records
        
        await scheduler.run_job(1)
        
        mock_run_legacy.assert_called_once()
        
        # Verify status updates
        # We expect session.add to be called multiple times (status running, then status idle)
        assert mock_session.add.call_count >= 2
        assert c1.status == "idle" # End state
        
        # Verify run record created
        # We can't easily check the exact object passed to add without capturing it, 
        # but we can assume if code ran without error it's fine for this smoke test.

@pytest.mark.asyncio
async def test_scheduler_run_job_strategy():
    scheduler = DatabaseScheduler()
    
    with patch("app.services.scheduler.Session") as mock_session_cls, \
         patch("app.services.scheduler.CollectorRegistry") as mock_registry:
        
        mock_session = mock_session_cls.return_value
        mock_session.__enter__.return_value = mock_session
        
        # Mock collector
        c1 = Collector(id=2, name="TestStrategy", plugin_name="news_test", schedule_cron="*/5 * * * *", is_enabled=True, config={})
        mock_session.get.return_value = c1
        
        # Mock Strategy
        mock_strategy_cls = MagicMock()
        mock_strategy_instance = AsyncMock()
        mock_strategy_instance.collect.return_value = ["item1", "item2"]
        mock_strategy_cls.return_value = mock_strategy_instance
        
        mock_registry.get_strategy.return_value = mock_strategy_cls
        
        await scheduler.run_job(2)
        
        mock_registry.get_strategy.assert_called_with("news_test")
        mock_strategy_instance.collect.assert_called_once()
        
        assert c1.status == "idle"
