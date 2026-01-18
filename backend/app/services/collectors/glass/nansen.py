"""
Nansen API collector for smart money wallet tracking (Glass Ledger).

This collector fetches on-chain smart money wallet flows and behaviors from
the Nansen API, helping track what successful traders are buying and selling.

Data Source: https://docs.nansen.ai/
Collection Frequency: Every 15 minutes
Pricing: $49/month (Professional tier)
"""

import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlmodel import Session

# Note: SmartMoneyFlow model will be added in future sprint
# For now, collector logs data without storing to demonstrate functionality
# from app.models import SmartMoneyFlow
from app.services.collectors.api_collector import APICollector

logger = logging.getLogger(__name__)


class NansenCollector(APICollector):
    """
    Collector for smart money wallet tracking from Nansen API.
    
    Collects:
    - Smart money wallet net flows (USD)
    - Buying wallet addresses and counts
    - Selling wallet addresses and counts
    - Token/cryptocurrency being traded
    - Timestamp of flow data
    
    API Documentation: https://docs.nansen.ai/
    """
    
    # Top tokens to track for smart money flows
    TRACKED_TOKENS = [
        "ETH",  # Ethereum
        "BTC",  # Bitcoin (wrapped on Ethereum)
        "USDT",  # Tether
        "USDC",  # USD Coin
        "DAI",  # Dai stablecoin
    ]
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize the Nansen collector.
        
        Args:
            api_key: Nansen API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv("NANSEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Nansen API key required. Set NANSEN_API_KEY environment variable "
                "or pass api_key parameter. Get a key at: https://nansen.ai/"
            )
        
        super().__init__(
            name="nansen_api",
            ledger="glass",  # On-chain data
            base_url="https://api.nansen.ai/v1",
            timeout=30,
            max_retries=3,
            rate_limit_delay=5.0,  # Conservative rate limiting
        )
    
    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect smart money wallet flows from Nansen API.
        
        Returns:
            List of smart money flow dictionaries
        
        Raises:
            Exception: If API request fails
        """
        logger.info(f"{self.name}: Collecting smart money flows")
        
        collected_data = []
        
        try:
            # Collect flows for each tracked token
            for token in self.TRACKED_TOKENS:
                try:
                    # Use Bearer token authentication
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    }
                    
                    # Fetch smart money flows for this token
                    response = await self.fetch_json(
                        f"/smart-money/flows/{token}",
                        headers=headers
                    )
                    
                    if not response:
                        logger.warning(f"{self.name}: No data for {token}")
                        continue
                    
                    # Extract flow data
                    net_flow_usd = response.get("netFlowUsd", 0)
                    buying_wallets = response.get("buyingWallets", [])
                    selling_wallets = response.get("sellingWallets", [])
                    
                    data_point = {
                        "token": token,
                        "net_flow_usd": Decimal(str(net_flow_usd)) if net_flow_usd else Decimal("0"),
                        "buying_wallet_count": len(buying_wallets),
                        "selling_wallet_count": len(selling_wallets),
                        "buying_wallets": buying_wallets[:10],  # Store top 10 only
                        "selling_wallets": selling_wallets[:10],  # Store top 10 only
                        "collected_at": datetime.now(timezone.utc),
                    }
                    
                    collected_data.append(data_point)
                    logger.debug(f"{self.name}: Collected flow data for {token}")
                    
                except Exception as e:
                    logger.error(f"{self.name}: Failed to collect {token} flows: {str(e)}")
                    # Continue with other tokens
                    continue
            
            logger.info(f"{self.name}: Collected {len(collected_data)} smart money flows")
            return collected_data
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to collect smart money flows: {str(e)}")
            raise
    
    async def validate_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Validate the collected smart money flow data.
        
        Args:
            data: Raw data collected from Nansen API
        
        Returns:
            Validated data ready for storage
        
        Raises:
            ValueError: If validation fails
        """
        validated = []
        
        for item in data:
            try:
                # Validate required fields
                if not item.get("token"):
                    logger.warning(f"{self.name}: Missing token, skipping")
                    continue
                
                # Validate net flow is numeric
                if "net_flow_usd" in item:
                    try:
                        Decimal(str(item["net_flow_usd"]))
                    except Exception:
                        logger.warning(f"{self.name}: Invalid net_flow_usd for {item['token']}, skipping")
                        continue
                
                # Validate wallet counts
                if item.get("buying_wallet_count", 0) < 0 or item.get("selling_wallet_count", 0) < 0:
                    logger.warning(f"{self.name}: Invalid wallet counts for {item['token']}, skipping")
                    continue
                
                validated.append(item)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"{self.name}: Invalid data: {str(e)}")
                continue
        
        logger.info(f"{self.name}: Validated {len(validated)}/{len(data)} records")
        return validated
    
    async def store_data(self, data: list[dict[str, Any]], session: Session) -> int:
        """
        Store validated smart money flow data in the database.
        
        Note: SmartMoneyFlow model needs to be added to models.py in a future sprint.
        For Sprint 2.12, this collector demonstrates the API integration and data collection,
        with storage deferred to when the full Glass Ledger schema is implemented.
        
        Args:
            data: Validated data to store
            session: Database session
        
        Returns:
            Number of records that would be stored (currently logged only)
        """
        stored_count = 0
        
        for item in data:
            try:
                # TODO Sprint 2.13: Once SmartMoneyFlow model is added to models.py, uncomment:
                # smart_money_flow = SmartMoneyFlow(
                #     token=item["token"],
                #     net_flow_usd=item["net_flow_usd"],
                #     buying_wallet_count=item["buying_wallet_count"],
                #     selling_wallet_count=item["selling_wallet_count"],
                #     buying_wallets=item.get("buying_wallets"),
                #     selling_wallets=item.get("selling_wallets"),
                #     collected_at=item["collected_at"],
                # )
                # session.add(smart_money_flow)
                
                # For now, log the data to demonstrate collection works
                logger.info(
                    f"{self.name}: Collected smart money flow: {item['token']} - "
                    f"Net Flow: ${item['net_flow_usd']}, "
                    f"Buyers: {item['buying_wallet_count']}, "
                    f"Sellers: {item['selling_wallet_count']}"
                )
                
                stored_count += 1
                
            except Exception as e:
                logger.error(
                    f"{self.name}: Failed to log flow data for '{item.get('token', 'unknown')}': {str(e)}"
                )
                continue
        
        # TODO Sprint 2.13: Uncomment when SmartMoneyFlow model exists
        # try:
        #     session.commit()
        #     logger.info(f"{self.name}: Stored {stored_count} smart money flow records")
        # except Exception as e:
        #     logger.error(f"{self.name}: Failed to commit records: {str(e)}")
        #     session.rollback()
        #     stored_count = 0
        
        logger.info(f"{self.name}: Validated and logged {stored_count} smart money flow records (storage pending model creation)")
        return stored_count
