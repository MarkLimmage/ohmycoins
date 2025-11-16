"""
DeFiLlama API collector for protocol fundamentals (Glass Ledger).

This collector fetches Total Value Locked (TVL), fees, and revenue data for
DeFi protocols from the DeFiLlama API (free, no authentication required).

Data Source: https://defillama.com/docs/api
Collection Frequency: Daily (updates daily at 2 AM UTC)
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlmodel import Session

from app.models import ProtocolFundamentals
from app.services.collectors.api_collector import APICollector

logger = logging.getLogger(__name__)


class DeFiLlamaCollector(APICollector):
    """
    Collector for DeFi protocol fundamentals from DeFiLlama API.
    
    Collects:
    - Total Value Locked (TVL) in USD
    - 24-hour fees
    - 24-hour revenue
    
    For protocols: Major DeFi protocols tracked by DeFiLlama
    """
    
    # List of protocol slugs to monitor (top protocols by TVL)
    MONITORED_PROTOCOLS = [
        "lido",           # Liquid staking
        "aave",           # Lending
        "makerdao",       # Stablecoin
        "uniswap",        # DEX
        "curve",          # DEX
        "justlend",       # Lending
        "compound",       # Lending
        "pancakeswap",    # DEX
        "balancer",       # DEX
        "rocket-pool",    # Liquid staking
        "convex-finance", # Yield
        "sushiswap",      # DEX
        "venus",          # Lending
        "gmx",            # Perpetuals
        "frax",           # Stablecoin
        "liquity",        # Lending
        "yearn-finance",  # Yield
        "stargate",       # Bridge
        "synthetix",      # Derivatives
        "pendle",         # Yield
    ]
    
    def __init__(self):
        """Initialize the DeFiLlama collector."""
        super().__init__(
            name="defillama_api",
            ledger="glass",
            base_url="https://api.llama.fi",
            timeout=30,
            max_retries=3,
            rate_limit_delay=0.1,  # Be respectful to free API
        )
    
    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect protocol fundamental data from DeFiLlama API.
        
        Returns:
            List of protocol data dictionaries
        
        Raises:
            Exception: If API request fails
        """
        logger.info(f"{self.name}: Collecting data for {len(self.MONITORED_PROTOCOLS)} protocols")
        
        all_data = []
        
        for protocol_slug in self.MONITORED_PROTOCOLS:
            try:
                # Fetch protocol TVL data
                protocol_data = await self.fetch_json(f"/protocol/{protocol_slug}")
                
                # Extract current TVL
                tvl = protocol_data.get("tvl")
                if tvl is None or len(tvl) == 0:
                    logger.warning(f"{self.name}: No TVL data for {protocol_slug}")
                    continue
                
                # Get the most recent TVL value
                latest_tvl = tvl[-1] if isinstance(tvl, list) else tvl
                current_tvl = latest_tvl.get("totalLiquidityUSD") if isinstance(latest_tvl, dict) else latest_tvl
                
                # Try to get fees/revenue data (not all protocols have this)
                fees_24h = None
                revenue_24h = None
                
                try:
                    # Fetch fees data (separate endpoint)
                    fees_data = await self.fetch_json(f"/summary/fees/{protocol_slug}")
                    if fees_data and "total24h" in fees_data:
                        fees_24h = fees_data["total24h"]
                    if fees_data and "totalRevenue24h" in fees_data:
                        revenue_24h = fees_data["totalRevenue24h"]
                except Exception as e:
                    logger.debug(f"{self.name}: No fees data for {protocol_slug}: {str(e)}")
                
                data_point = {
                    "protocol": protocol_slug,
                    "tvl_usd": current_tvl,
                    "fees_24h": fees_24h,
                    "revenue_24h": revenue_24h,
                    "collected_at": datetime.now(timezone.utc),
                }
                
                all_data.append(data_point)
                logger.debug(f"{self.name}: Collected data for {protocol_slug}: TVL=${current_tvl:,.0f}")
                
            except Exception as e:
                logger.error(f"{self.name}: Failed to collect data for {protocol_slug}: {str(e)}")
                # Continue with other protocols even if one fails
                continue
        
        logger.info(f"{self.name}: Collected data for {len(all_data)}/{len(self.MONITORED_PROTOCOLS)} protocols")
        return all_data
    
    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected protocol data.
        
        Args:
            data: Raw data collected from DeFiLlama API
        
        Returns:
            Validated data ready for storage
        
        Raises:
            ValueError: If validation fails
        """
        validated = []
        
        for item in data:
            try:
                # Validate required fields
                if not item.get("protocol"):
                    logger.warning(f"{self.name}: Missing protocol name, skipping")
                    continue
                
                if item.get("tvl_usd") is None:
                    logger.warning(f"{self.name}: Missing TVL for {item['protocol']}, skipping")
                    continue
                
                # Validate TVL is positive
                tvl = float(item["tvl_usd"])
                if tvl < 0:
                    logger.warning(f"{self.name}: Negative TVL for {item['protocol']}, skipping")
                    continue
                
                # Validate fees and revenue if present
                if item.get("fees_24h") is not None:
                    fees = float(item["fees_24h"])
                    if fees < 0:
                        logger.warning(f"{self.name}: Negative fees for {item['protocol']}, setting to None")
                        item["fees_24h"] = None
                
                if item.get("revenue_24h") is not None:
                    revenue = float(item["revenue_24h"])
                    if revenue < 0:
                        logger.warning(f"{self.name}: Negative revenue for {item['protocol']}, setting to None")
                        item["revenue_24h"] = None
                
                validated.append(item)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid data for {item.get('protocol', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"{self.name}: Validated {len(validated)}/{len(data)} records")
        return validated
    
    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated protocol fundamentals in the database.
        
        Args:
            data: Validated data to store
            session: Database session
        
        Returns:
            Number of records stored
        """
        stored_count = 0
        
        for item in data:
            try:
                # Convert to Decimal for database storage
                protocol_fundamental = ProtocolFundamentals(
                    protocol=item["protocol"],
                    tvl_usd=Decimal(str(item["tvl_usd"])) if item.get("tvl_usd") is not None else None,
                    fees_24h=Decimal(str(item["fees_24h"])) if item.get("fees_24h") is not None else None,
                    revenue_24h=Decimal(str(item["revenue_24h"])) if item.get("revenue_24h") is not None else None,
                    collected_at=item["collected_at"],
                )
                
                session.add(protocol_fundamental)
                stored_count += 1
                
            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to store data for {item.get('protocol', 'unknown')}: {str(e)}"
                )
                # Continue with other records
                continue
        
        # Commit all records at once
        session.commit()
        
        logger.info(f"{self.name}: Stored {stored_count} protocol fundamental records")
        return stored_count
