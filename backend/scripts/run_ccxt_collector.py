import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import engine
from app.services.collectors.ccxt_collector import CCXTCollector
from sqlmodel import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_async():
    logger.info("Starting updated CCXT Collector (Async)...")
    
    # Initialize collector
    collector = CCXTCollector(
        exchanges=["binance", "kraken"],
        symbols=["BTC/USDT", "ETH/USDT"]
    )
    
    # Run fetch logic
    logger.info("Collecting data...")
    try:
        data = await collector.collect()
        
        # Validation (simple check)
        data = await collector.validate_data(data)
        
        if not data:
            logger.error("No data collected!")
            return

        # Store data
        logger.info("Storing data...")
        with Session(engine) as session:
            try:
                count = await collector.store_data(session=session, data=data) 
                logger.info(f"Success! Processed {count} records.")
            except Exception as e:
                logger.error(f"Failed to store data: {e}")
                
    except Exception as e:
        logger.error(f"Collector run failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_async())
