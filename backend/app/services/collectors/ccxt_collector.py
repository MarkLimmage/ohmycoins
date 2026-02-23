import datetime
import logging
import asyncio
from decimal import Decimal
from typing import Any, Dict, List, Optional

import ccxt.async_support as ccxt  # Use async support
from sqlmodel import Session, select

from app.models import ExchangeOHLCV
from app.services.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class CCXTCollector(BaseCollector):
    """
    Async Collector for fetching OHLCV data from exchanges via CCXT.
    Supports multiple exchanges and symbols.
    """

    def __init__(self, exchanges: Optional[List[str]] = None, symbols: Optional[List[str]] = None):
        super().__init__(name="ccxt_collector", ledger="exchange")
        self.exchanges = exchanges or ["binance", "kraken"]
        self.symbols = symbols or ["BTC/USDT", "ETH/USDT"]
        self.timeframe = "1h"
        self.limit = 100  # Default limit for fetch_ohlcv

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV data from configured exchanges asynchronously.
        Returns a list of OHLCV data records.
        """
        results = []

        for exchange_name in self.exchanges:
            exchange = None
            try:
                # Initialize exchange class dynamically
                if not hasattr(ccxt, exchange_name):
                    logger.error(f"Exchange {exchange_name} not found in ccxt.")
                    continue

                exchange_class = getattr(ccxt, exchange_name)
                exchange = exchange_class()
                
                # Check if fetch_ohlcv is supported
                if not exchange.has['fetchOHLCV']:
                    logger.warning(f"Exchange {exchange_name} does not support fetchOHLCV. Skipping.")
                    await exchange.close()
                    continue

                for symbol in self.symbols:
                    try:
                        logger.info(f"Fetching {symbol} from {exchange_name}...")
                        # Fetch data (async)
                        ohlcv = await exchange.fetch_ohlcv(symbol, self.timeframe, limit=self.limit)
                        
                        # Process data immediately
                        for entry in ohlcv:
                            # entry: [timestamp, open, high, low, close, volume]
                            ts = datetime.datetime.fromtimestamp(entry[0] / 1000, datetime.timezone.utc)
                            results.append({
                                "exchange": exchange_name,
                                "symbol": symbol,
                                "timestamp": ts,
                                "open": Decimal(str(entry[1])),
                                "high": Decimal(str(entry[2])),
                                "low": Decimal(str(entry[3])),
                                "close": Decimal(str(entry[4])),
                                "volume": Decimal(str(entry[5])),
                            })
                            
                    except Exception as e:
                        logger.error(f"Error fetching {symbol} from {exchange_name}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error initializing exchange {exchange_name}: {e}")
            finally:
                if exchange:
                    await exchange.close()
                
        return results

    async def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate that we received some data.
        """
        if not data:
            logger.warning("No data collected from any exchange.")
            return []
        
        return data

    async def store_data(self, data: List[Dict[str, Any]], session: Session) -> int:
        """
        Store collected OHLCV data into ExchangeOHLCV table.
        """
        count = 0
        for record in data:
            # Check for existing record to avoid duplicates
            existing = session.exec(
                select(ExchangeOHLCV).where(
                    ExchangeOHLCV.exchange == record["exchange"],
                    ExchangeOHLCV.symbol == record["symbol"],
                    ExchangeOHLCV.timestamp == record["timestamp"]
                )
            ).first()

            if not existing:
                obj = ExchangeOHLCV(**record)
                session.add(obj)
                count += 1
        
        try:
            session.commit()
            logger.info(f"Stored {count} new OHLCV records.")
        except Exception as e:
            session.rollback()
            logger.error(f"Database commit failed: {e}")
            raise e
            
        return count
