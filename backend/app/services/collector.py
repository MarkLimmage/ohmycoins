# mypy: ignore-errors
"""
Coinspot Data Collector Service

This module handles fetching cryptocurrency price data from the Coinspot exchange
and storing it in the database for use by The Lab (backtesting and algorithm development).

The collector supports two modes:
1. Public API: Returns 17 actively traded coins (no authentication required)
2. Web Scraping: Scrapes the tradecoins page to fetch all 500+ available coins

To enable web scraping mode, set COINSPOT_USE_WEB_SCRAPING=true in environment variables.
Note: The authenticated API endpoints don't provide all coin prices, so we scrape the public
tradecoins page which displays buy/sell prices for all 538+ coins available on the exchange.
"""
import asyncio
import logging
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import PriceData5Min

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Coinspot URLs
COINSPOT_PUBLIC_API_URL = "https://www.coinspot.com.au/pubapi/v2/latest"
COINSPOT_TRADECOINS_URL = "https://www.coinspot.com.au/tradecoins"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT = 30.0


class CoinspotCollector:
    """Collector service for fetching and storing Coinspot price data

    Supports two modes:
    - Public API mode: Fetches 17 major coins from /pubapi/v2/latest
    - Web scraping mode: Scrapes tradecoins page for all 538+ coins
    """

    def __init__(self):
        self.use_web_scraping = settings.COINSPOT_USE_WEB_SCRAPING

        if self.use_web_scraping:
            logger.info("Using web scraping mode to fetch all 538+ Coinspot coins")
        else:
            logger.info("Using public API mode (17 major coins)")

    async def fetch_latest_prices(self) -> dict[str, Any] | None:
        """
        Fetch latest price data from Coinspot with retry logic

        Uses either public API (17 coins) or web scraping (538+ coins)
        depending on configuration.

        Returns:
            Dictionary containing price data for all coins, or None if all retries fail
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if self.use_web_scraping:
                    prices = await self._fetch_scraped_prices(attempt)
                else:
                    prices = await self._fetch_public_prices(attempt)

                if prices:
                    return prices

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}/{MAX_RETRIES}: {type(e).__name__}: {e}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    await asyncio.sleep(RETRY_DELAY_SECONDS)

        logger.error(f"Failed to fetch prices after {MAX_RETRIES} attempts")
        return None

    async def _fetch_public_prices(self, attempt: int) -> dict[str, Any] | None:
        """Fetch prices from public API endpoint (17 major coins)"""
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                logger.info(f"Fetching from public API (attempt {attempt}/{MAX_RETRIES})")
                response = await client.get(COINSPOT_PUBLIC_API_URL)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "ok":
                    prices = data.get("prices", {})
                    total_coins = len(prices)
                    logger.info(f"Successfully fetched prices for {total_coins} coins from public API")

                    if total_coins > 0:
                        logger.debug(f"Coins fetched: {', '.join(sorted(prices.keys()))}")
                    return prices
                else:
                    logger.error(f"API returned non-ok status: {data.get('status')}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                        await asyncio.sleep(RETRY_DELAY_SECONDS)
                    return None

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error on attempt {attempt}/{MAX_RETRIES}: {e.response.status_code}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        except httpx.RequestError as e:
            logger.error(f"Request error on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

        return None

    async def _fetch_scraped_prices(self, attempt: int) -> dict[str, Any] | None:
        """
        Fetch prices by scraping the tradecoins page (all 538+ coins)

        The tradecoins page displays buy/sell prices for all available coins
        in HTML table rows with data-coin attributes.

        Structure: <tr data-coin="BTC">
          <td ...> (image)
          <td ...> (name/symbol)
          <td data-value="137184.97"> (buy price)
          <td data-value="135833.38"> (sell price)
          ...

        Based on: https://github.com/kochie/coinspot-async-api
        """
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                logger.info(f"Fetching from tradecoins page (attempt {attempt}/{MAX_RETRIES})")

                # Fetch the HTML page
                response = await client.get(COINSPOT_TRADECOINS_URL)
                response.raise_for_status()
                html_content = response.text

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                # Find all coin rows: <tr data-coin="BTC">
                coin_rows = soup.find_all('tr', attrs={'data-coin': True})

                prices = {}
                for row in coin_rows:
                    coin_symbol = row.get('data-coin', '').upper()
                    if not coin_symbol or coin_symbol == 'AUD':
                        continue

                    try:
                        # Get all td elements
                        tds = row.find_all('td')

                        if len(tds) >= 4:
                            # TD index 2: Buy price (data-value attribute)
                            # TD index 3: Sell price (data-value attribute)
                            buy_td = tds[2]
                            sell_td = tds[3]

                            buy_value = buy_td.get('data-value')
                            sell_value = sell_td.get('data-value')

                            if buy_value and sell_value:
                                buy_price = float(buy_value)
                                sell_price = float(sell_value)

                                if buy_price > 0 and sell_price > 0:
                                    # Use average of buy/sell as "last" price
                                    last_price = (buy_price + sell_price) / 2

                                    prices[coin_symbol.lower()] = {
                                        "bid": str(buy_price),
                                        "ask": str(sell_price),
                                        "last": str(last_price)
                                    }
                    except (ValueError, AttributeError, IndexError) as e:
                        logger.debug(f"Failed to parse prices for {coin_symbol}: {e}")
                        continue

                total_coins = len(prices)
                logger.info(f"Successfully scraped prices for {total_coins} coins from tradecoins page")

                if total_coins > 0:
                    sample_coins = sorted(prices.keys())[:10]
                    logger.debug(f"Sample coins: {', '.join(sample_coins)}")
                    return prices
                else:
                    logger.warning("No coin prices found on tradecoins page - HTML structure may have changed")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                        await asyncio.sleep(RETRY_DELAY_SECONDS)
                    return None

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error on attempt {attempt}/{MAX_RETRIES}: {e.response.status_code}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        except httpx.RequestError as e:
            logger.error(f"Request error on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            logger.error(f"Unexpected error parsing HTML on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

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

                            # Enhanced validation for invalid prices (NaN, Infinity, etc.)
                            if not all(math.isfinite(float(x)) for x in [bid, ask, last]):
                                logger.warning(f"Invalid price data for {coin_type} (NaN/Inf detected), skipping")
                                error_count += 1
                                continue

                            # Sanity check: prices should be positive
                            if bid < 0 or ask < 0 or last < 0:
                                logger.warning(f"Negative price detected for {coin_type}, skipping")
                                error_count += 1
                                continue

                            price_record = PriceData5Min(
                                coin_type=coin_type,
                                bid=bid,
                                ask=ask,
                                last=last,
                                timestamp=timestamp
                            )

                            session.add(price_record)
                            stored_count += 1

                        except (ValueError, TypeError, InvalidOperation) as e:
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
