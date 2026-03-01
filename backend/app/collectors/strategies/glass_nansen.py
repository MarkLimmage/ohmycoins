"""
Nansen API collector plugin for smart money wallet tracking (Glass Ledger).

This collector fetches on-chain smart money wallet flows and behaviors from
the Nansen API, helping track what successful traders are buying and selling.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import SmartMoneyFlow

logger = logging.getLogger(__name__)


class GlassNansen(ICollector):
    """Collector for smart money wallet tracking from Nansen API."""

    # Top tokens to track for smart money flows
    TRACKED_TOKENS = [
        "ETH",  # Ethereum
        "BTC",  # Bitcoin (wrapped on Ethereum)
        "USDT",  # Tether
        "USDC",  # USD Coin
        "DAI",  # Dai stablecoin
    ]

    @property
    def name(self) -> str:
        return "glass_nansen"

    @property
    def description(self) -> str:
        return "Smart money wallet flow tracking from Nansen API"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tokens to track",
                    "default": self.TRACKED_TOKENS,
                },
                "rate_limit_delay": {
                    "type": "number",
                    "description": "Delay between requests in seconds",
                    "default": 5.0,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "tokens" in config:
            if not isinstance(config["tokens"], list):
                logger.error("Invalid config: 'tokens' must be a list")
                return False

        if "rate_limit_delay" in config:
            try:
                float(config["rate_limit_delay"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'rate_limit_delay' must be a number")
                return False

        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to Nansen API."""
        api_key = os.getenv("NANSEN_API_KEY")
        if not api_key:
            logger.warning("NANSEN_API_KEY not set")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}
                async with session.get(
                    "https://api.nansen.ai/v1/smart-money/flows/ETH",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to test Nansen connection: {e}")
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect smart money wallet flows from Nansen API."""
        api_key = os.getenv("NANSEN_API_KEY")
        if not api_key:
            logger.warning("NANSEN_API_KEY not configured. Skipping collection.")
            return []

        tokens = config.get("tokens", self.TRACKED_TOKENS)
        rate_limit_delay = config.get("rate_limit_delay", 5.0)

        logger.info(f"Collecting smart money flows for {len(tokens)} tokens")

        collected_data = []

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}

            for token in tokens:
                try:
                    await asyncio.sleep(rate_limit_delay)

                    url = f"https://api.nansen.ai/v1/smart-money/flows/{token}"

                    async with session.get(
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(
                                f"Failed to fetch {token}: status {resp.status}"
                            )
                            continue

                        flow_data = await resp.json()

                    # Extract flow information
                    if not flow_data:
                        logger.warning(f"No flow data for {token}")
                        continue

                    # Parse the response structure from Nansen
                    net_flow = flow_data.get("net_flow_usd", 0)
                    buying_count = flow_data.get("buying_wallet_count", 0)
                    selling_count = flow_data.get("selling_wallet_count", 0)
                    buying_wallets = flow_data.get("buying_wallets", [])
                    selling_wallets = flow_data.get("selling_wallets", [])

                    # Create SmartMoneyFlow instance
                    data_point = SmartMoneyFlow(
                        token=token,
                        net_flow_usd=Decimal(str(net_flow)) if net_flow else Decimal(0),
                        buying_wallet_count=buying_count,
                        selling_wallet_count=selling_count,
                        buying_wallets=buying_wallets if buying_wallets else None,
                        selling_wallets=selling_wallets if selling_wallets else None,
                        collected_at=datetime.now(timezone.utc),
                    )

                    collected_data.append(data_point)
                    logger.debug(f"Collected smart money flow for {token}")

                except Exception as e:
                    logger.error(f"Failed to collect data for {token}: {e}")
                    continue

        logger.info(f"Collected {len(collected_data)}/{len(tokens)} smart money flows")
        return collected_data


CollectorRegistry.register(GlassNansen)
