import logging
import random
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select

# Adjust python path to include backend directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.core.db import engine
from app.models import Collector, CollectorRuns
from app.services.collectors.base import CollectorStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_metrics():
    with Session(engine) as session:
        # Get all collectors
        collectors = session.exec(select(Collector)).all()
        
        if not collectors:
            logger.warning("No collectors found. Please create a collector first.")
            return

        logger.info(f"Found {len(collectors)} collectors. Generating metrics...")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        for collector in collectors:
            logger.info(f"Generating metrics for {collector.name}...")
            
            # Generate random runs every 15-60 minutes
            current_time = start_time
            while current_time < end_time:
                # Randomize interval
                interval = timedelta(minutes=random.randint(15, 60))
                current_time += interval
                
                if current_time > end_time:
                    break
                
                # Determine success/failure (90% success)
                status = CollectorStatus.SUCCESS if random.random() < 0.9 else CollectorStatus.FAILED
                
                records_collected = 0
                error_message = None
                
                if status == CollectorStatus.SUCCESS:
                    records_collected = random.randint(10, 100)
                else:
                    error_message = "Random failure in mock data generation"
                
                run_duration = timedelta(seconds=random.uniform(1.0, 10.0))
                
                collector_run = CollectorRuns(
                    collector_name=collector.name,
                    status=status,
                    started_at=current_time,
                    completed_at=current_time + run_duration,
                    records_collected=records_collected,
                    error_message=error_message
                )
                session.add(collector_run)
            
            session.commit()
            logger.info(f"Metrics generated for {collector.name}")

if __name__ == "__main__":
    create_mock_metrics()
