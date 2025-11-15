"""
Coinspot Data Collector Service

This module handles fetching cryptocurrency price data from the Coinspot public API
and storing it in the database for use by The Lab (backtesting and algorithm development).
"""
from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any
import uuid
import asyncio

import httpx
from sqlmodel import Session, select

from app.core.db import engine
from app.models import PriceData5Min

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Coinspot public API endpoint
COINSPOT_API_URL = "https://www.coinspot.com.au/pubapi/v2/latest"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT = 30.0


class CoinspotCollector:
    """Collector service for fetching and storing Coinspot price data"""

    def __init__(self):
        self.api_url = COINSPOT_API_URL
        self.session = None

    async def fetch_latest_prices(self) -> dict[str, Any] | None:
        """
        Fetch latest price data from Coinspot public API with retry logic
        
        Returns:
            Dictionary containing price data for all coins, or None if all retries fail
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    logger.info(f"Fetching prices from Coinspot API (attempt {attempt}/{MAX_RETRIES})")
                    response = await client.get(self.api_url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("status") == "ok":
                        prices = data.get("prices", {})
                        logger.info(f"Successfully fetched prices for {len(prices)} coins")
                        return prices
                    else:
                        logger.error(f"API returned non-ok status: {data.get('status')}")
                        if attempt < MAX_RETRIES:
                            logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                            await asyncio.sleep(RETRY_DELAY_SECONDS)
                        continue
                        
            except httpx.TimeoutException as e:
                logger.error(f"Request timeout on attempt {attempt}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP status error on attempt {attempt}/{MAX_RETRIES}: {e.response.status_code}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    
            except httpx.RequestError as e:
                logger.error(f"Request error on attempt {attempt}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}/{MAX_RETRIES}: {type(e).__name__}: {e}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        
        logger.error(f"Failed to fetch prices after {MAX_RETRIES} attempts")
        return None

    def store_prices(self, prices: dict[str, Any]) -> int:
        """
        Store price data in the database with error handling
        
        Args:
            prices: Dictionary of price data from Coinspot API
            
        Returns:
            Number of records successfully stored
        """
        if not prices:
            logger.warning("No prices to store")
            return 0

        stored_count = 0
        error_count = 0
        timestamp = datetime.now(timezone.utc)

        try:
            with Session(engine) as session:
                for coin_type, price_data in prices.items():
                    try:
                        # Validate price data
                        if not all(key in price_data for key in ["bid", "ask", "last"]):
                            logger.warning(f"Missing price fields for {coin_type}, skipping")
                            error_count += 1
                            continue
                        
                        # Check if record already exists for this coin/timestamp combination
                        existing = session.exec(
                            select(PriceData5Min).where(
                                PriceData5Min.coin_type == coin_type,
                                PriceData5Min.timestamp == timestamp
                            )
                        ).first()
                        
                        if existing:
                            logger.debug(f"Price data for {coin_type} at {timestamp} already exists, skipping")
                            continue

                        # Create new price record with validation
                        try:
                            bid = Decimal(str(price_data["bid"]))
                            ask = Decimal(str(price_data["ask"]))
                            last = Decimal(str(price_data["last"]))
                            
                            # Sanity check: prices should be positive
                            if bid < 0 or ask < 0 or last < 0:
                                logger.warning(f"Negative price detected for {coin_type}, skipping")
                                error_count += 1
                                continue
                            
                            price_record = PriceData5Min(
                                id=uuid.uuid4(),
                                coin_type=coin_type,
                                bid=bid,
                                ask=ask,
                                last=last,
                                timestamp=timestamp
                            )
                            
                            session.add(price_record)
                            stored_count += 1
                            
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid price data for {coin_type}: {e}")
                            error_count += 1
                            continue
                        
                    except Exception as e:
                        logger.error(f"Error processing price for {coin_type}: {type(e).__name__}: {e}")
                        error_count += 1
                        continue

                # Commit all records at once
                try:
                    session.commit()
                    logger.info(f"Successfully stored {stored_count} price records at {timestamp}")
                    if error_count > 0:
                        logger.warning(f"Encountered {error_count} errors during storage")
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error committing price data: {type(e).__name__}: {e}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Database session error: {type(e).__name__}: {e}")
            return 0

        return stored_count

    async def collect_and_store(self) -> int:
        """
        Main collection workflow: fetch prices and store them with comprehensive error handling
        
        Returns:
            Number of records stored
        """
        try:
            logger.info("Starting price collection...")
            
            # Fetch latest prices with retry logic
            prices = await self.fetch_latest_prices()
            
            if not prices:
                logger.error("Failed to fetch prices after all retries, skipping storage")
                return 0
            
            # Store in database
            stored_count = self.store_prices(prices)
            
            if stored_count > 0:
                logger.info(f"Collection complete. Stored {stored_count} records")
            else:
                logger.warning("Collection complete but no records were stored")
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Critical error in collection workflow: {type(e).__name__}: {e}", exc_info=True)
            return 0


async def run_collector():
    """Run the collector once (for manual execution or testing)"""
    collector = CoinspotCollector()
    return await collector.collect_and_store()


if __name__ == "__main__":
    import asyncio
    
    logger.info("Running Coinspot collector (manual execution)")
    result = asyncio.run(run_collector())
    logger.info(f"Collection complete: {result} records stored")
