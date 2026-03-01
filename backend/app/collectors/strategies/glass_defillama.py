"""
DeFiLlama API collector plugin for protocol fundamentals (Glass Ledger).

This collector fetches Total Value Locked (TVL), fees, and revenue data for
DeFi protocols from the DeFiLlama API (free, no authentication required).
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

import aiohttp

from app.core.collectors.base import ICollector
from app.models import ProtocolFundamentals

logger = logging.getLogger(__name__)


class GlassDefiLlama(ICollector):
    """Collector for DeFi protocol fundamentals from DeFiLlama API."""

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

    @property
    def name(self) -> str:
        return "glass_defillama"

    @property
    def description(self) -> str:
        return "DeFi protocol TVL, fees, and revenue from DeFiLlama API"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "protocols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of protocol slugs to monitor",
                    "default": self.MONITORED_PROTOCOLS,
                },
                "rate_limit_delay": {
                    "type": "number",
                    "description": "Delay between requests in seconds",
                    "default": 0.1,
                },
            },
            "required": [],
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        if "protocols" in config:
            if not isinstance(config["protocols"], list):
                logger.error("Invalid config: 'protocols' must be a list")
                return False
            if not all(isinstance(p, str) for p in config["protocols"]):
                logger.error("Invalid config: all protocols must be strings")
                return False

        if "rate_limit_delay" in config:
            try:
                float(config["rate_limit_delay"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'rate_limit_delay' must be a number")
                return False

        return True

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        """Test connectivity to DeFiLlama API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.llama.fi/protocols",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test DeFiLlama connection: {e}")
            return False

    async def collect(self, config: Dict[str, Any]) -> List[Any]:
        """Collect protocol fundamental data from DeFiLlama API."""
        protocols = config.get("protocols", self.MONITORED_PROTOCOLS)
        rate_limit_delay = config.get("rate_limit_delay", 0.1)

        logger.info(f"Collecting data for {len(protocols)} protocols")

        all_data = []
        base_url = "https://api.llama.fi"

        async with aiohttp.ClientSession() as session:
            for protocol_slug in protocols:
                try:
                    import asyncio

                    await asyncio.sleep(rate_limit_delay)

                    # Fetch protocol TVL data
                    async with session.get(
                        f"{base_url}/protocol/{protocol_slug}",
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(f"Failed to fetch {protocol_slug}: status {resp.status}")
                            continue

                        protocol_data = await resp.json()

                    # Extract current TVL
                    tvl = protocol_data.get("tvl")
                    if tvl is None or len(tvl) == 0:
                        logger.warning(f"No TVL data for {protocol_slug}")
                        continue

                    # Get the most recent TVL value
                    latest_tvl = tvl[-1] if isinstance(tvl, list) else tvl
                    current_tvl = (
                        latest_tvl.get("totalLiquidityUSD")
                        if isinstance(latest_tvl, dict)
                        else latest_tvl
                    )

                    # Try to get fees/revenue data
                    fees_24h = None
                    revenue_24h = None

                    try:
                        await asyncio.sleep(rate_limit_delay)
                        async with session.get(
                            f"{base_url}/summary/fees/{protocol_slug}",
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as resp:
                            if resp.status == 200:
                                fees_data = await resp.json()
                                if fees_data and "total24h" in fees_data:
                                    fees_24h = fees_data["total24h"]
                                if fees_data and "totalRevenue24h" in fees_data:
                                    revenue_24h = fees_data["totalRevenue24h"]
                    except Exception as e:
                        logger.debug(f"No fees data for {protocol_slug}: {e}")

                    # Create ProtocolFundamentals instance
                    data_point = ProtocolFundamentals(
                        protocol=protocol_slug,
                        tvl_usd=Decimal(str(current_tvl)) if current_tvl else None,
                        fees_24h=Decimal(str(fees_24h)) if fees_24h else None,
                        revenue_24h=Decimal(str(revenue_24h)) if revenue_24h else None,
                        collected_at=datetime.now(timezone.utc),
                    )

                    all_data.append(data_point)
                    logger.debug(f"Collected data for {protocol_slug}")

                except Exception as e:
                    logger.error(f"Failed to collect data for {protocol_slug}: {e}")
                    continue

        logger.info(f"Collected {len(all_data)}/{len(protocols)} protocols")
        return all_data


# Register the collector
from app.core.collectors.registry import CollectorRegistry

CollectorRegistry.register(GlassDefiLlama)
