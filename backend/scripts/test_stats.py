
import logging
import sys
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select, delete

# Add parent directory to path to import app
sys.path.append(".")

from app.core.db import engine, init_db
from app.models import CollectorRuns, Collector
from app.services.collectors.stats import CollectorStatsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stats():
    with Session(engine) as session:
        # cleanup
        session.exec(delete(CollectorRuns).where(CollectorRuns.collector_name.in_(["test_col_1", "test_col_2"])))
        session.exec(delete(Collector).where(Collector.name.in_(["test_col_1", "test_col_2"])))
        session.commit()
        
        # Setup Collectors
        c1 = Collector(name="test_col_1", plugin_name="test", is_enabled=True, status="idle")
        c2 = Collector(name="test_col_2", plugin_name="test", is_enabled=True, status="error")
        session.add(c1)
        session.add(c2)
        session.commit()

        # Add runs
        now = datetime.now(timezone.utc)
        
        # Run 1: Success, 100 records
        r1 = CollectorRuns(
            collector_name="test_col_1",
            status="success",
            started_at=now - timedelta(minutes=30),
            completed_at=now - timedelta(minutes=29),
            records_collected=100
        )
        session.add(r1)
        
        # Run 2: Failed
        r2 = CollectorRuns(
            collector_name="test_col_2",
            status="failed",
            started_at=now - timedelta(minutes=15),
            completed_at=now - timedelta(minutes=14),
            error_message="Test error"
        )
        session.add(r2)
        session.commit()

        service = CollectorStatsService(session)
        
        logger.info("Testing Dashboard Summary...")
        summary = service.get_dashboard_summary()
        logger.info(f"Summary: {summary}")
        
        assert summary["active_collectors"] >= 2
        assert summary["total_items_24h"] >= 100
        # error rate might depend on other existing data, but surely > 0
        
        logger.info("Testing Collector Health...")
        health = service.get_collector_health()
        for h in health:
            if h["name"] == "test_col_1":
                assert h["status"] == "healthy"
            if h["name"] == "test_col_2":
                # Collector status is 'error' so should be error
                assert h["status"] == "error"

        logger.info("SUCCESS: Stats Service validated.")

if __name__ == "__main__":
    test_stats()
