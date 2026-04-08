import logging
import random
from decimal import Decimal
from typing import Any

import httpx

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import OnChainMetrics

logger = logging.getLogger(__name__)

# Ordered fallback RPC endpoints per chain
ETHEREUM_RPC_ENDPOINTS: list[str] = [
    "https://eth.llamarpc.com",
    "https://cloudflare-eth.com",
    "https://eth.drpc.org",
    "https://rpc.ankr.com/eth",
    "https://ethereum-rpc.publicnode.com",
]

SOLANA_RPC_ENDPOINTS: list[str] = [
    "https://api.mainnet-beta.solana.com",
]

CONNECTION_TIMEOUT_SECONDS = 10.0


def _get_rpc_endpoints(chain: str, config: dict[str, Any]) -> list[str]:
    """Build ordered list of RPC endpoints: custom first, then fallbacks."""
    endpoints: list[str] = []
    custom_url = config.get("rpc_url")
    if custom_url:
        endpoints.append(custom_url)

    if chain == "ethereum":
        endpoints.extend(url for url in ETHEREUM_RPC_ENDPOINTS if url not in endpoints)
    elif chain == "solana":
        endpoints.extend(url for url in SOLANA_RPC_ENDPOINTS if url not in endpoints)
    return endpoints


class GlassChainWalker(ICollector):
    @property
    def name(self) -> str:
        return "GlassChainWalker"

    @property
    def description(self) -> str:
        return (
            "Connects to public blockchain RPCs to fetch block height and gas prices."
        )

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chain": {
                    "type": "string",
                    "enum": ["ethereum", "solana"],
                    "default": "ethereum",
                },
                "rpc_url": {"type": "string"},
                "mock_mode": {"type": "boolean", "default": False},
            },
            "required": ["chain"],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "chain" not in config:
            return False
        if config["chain"] not in ["ethereum", "solana"]:
            return False
        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        if config.get("mock_mode", False):
            return True

        chain = config.get("chain", "ethereum")
        endpoints = _get_rpc_endpoints(chain, config)
        if not endpoints:
            return False

        for rpc_url in endpoints:
            try:
                timeout = httpx.Timeout(
                    CONNECTION_TIMEOUT_SECONDS, connect=CONNECTION_TIMEOUT_SECONDS
                )
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if chain == "ethereum":
                        payload = {
                            "jsonrpc": "2.0",
                            "method": "eth_blockNumber",
                            "params": [],
                            "id": 1,
                        }
                    else:
                        payload = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getBlockHeight",
                        }
                    response = await client.post(rpc_url, json=payload)
                    response.raise_for_status()
                    logger.info("Connection test succeeded via %s", rpc_url)
                    return True
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.HTTPStatusError,
            ) as e:
                logger.warning("Connection test failed for %s: %s", rpc_url, e)
                continue
            except Exception as e:
                logger.error("Unexpected error testing %s: %s", rpc_url, e)
                continue
        return False

    async def _rpc_call_with_fallback(
        self, chain: str, config: dict[str, Any], payloads: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute one or more JSON-RPC calls against the endpoint list with fallback.

        Returns a list of response JSON dicts, one per payload.
        Raises RuntimeError if all endpoints are exhausted.
        """
        endpoints = _get_rpc_endpoints(chain, config)
        last_error: Exception | None = None

        for rpc_url in endpoints:
            try:
                timeout = httpx.Timeout(
                    CONNECTION_TIMEOUT_SECONDS, connect=CONNECTION_TIMEOUT_SECONDS
                )
                async with httpx.AsyncClient(timeout=timeout) as client:
                    results: list[dict[str, Any]] = []
                    for payload in payloads:
                        resp = await client.post(rpc_url, json=payload)
                        resp.raise_for_status()
                        results.append(resp.json())
                    logger.info("RPC calls succeeded via %s for %s", rpc_url, chain)
                    return results
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.HTTPStatusError,
            ) as e:
                logger.warning("RPC endpoint %s failed for %s: %s", rpc_url, chain, e)
                last_error = e
                continue
            except Exception as e:
                logger.warning("Unexpected error from %s for %s: %s", rpc_url, chain, e)
                last_error = e
                continue

        raise RuntimeError(
            f"All RPC endpoints exhausted for {chain}. Last error: {last_error}"
        )

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        chain = config["chain"]
        mock_mode = config.get("mock_mode", False)

        block_height = 0
        gas_price = Decimal(0)

        if mock_mode:
            if chain == "ethereum":
                block_height = 19000000 + random.randint(1, 1000)
                gas_price = Decimal(random.uniform(10, 50))  # Gwei
            else:  # solana
                block_height = 200000000 + random.randint(1, 10000)
                gas_price = Decimal(random.uniform(0.000005, 0.00001))
        else:
            if chain == "ethereum":
                payloads = [
                    {
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber",
                        "params": [],
                        "id": 1,
                    },
                    {
                        "jsonrpc": "2.0",
                        "method": "eth_gasPrice",
                        "params": [],
                        "id": 2,
                    },
                ]
                responses = await self._rpc_call_with_fallback(chain, config, payloads)
                if "error" in responses[0] or "result" not in responses[0]:
                    raise RuntimeError(
                        f"RPC error for eth_blockNumber: {responses[0].get('error', 'no result key')}"
                    )
                if "error" in responses[1] or "result" not in responses[1]:
                    raise RuntimeError(
                        f"RPC error for eth_gasPrice: {responses[1].get('error', 'no result key')}"
                    )
                block_height = int(responses[0]["result"], 16)
                gas_price_wei = int(responses[1]["result"], 16)
                gas_price = Decimal(gas_price_wei) / Decimal(10**9)  # Convert to Gwei

            elif chain == "solana":
                payloads = [
                    {"jsonrpc": "2.0", "id": 1, "method": "getBlockHeight"},
                ]
                responses = await self._rpc_call_with_fallback(chain, config, payloads)
                if "error" in responses[0] or "result" not in responses[0]:
                    raise RuntimeError(
                        f"RPC error for getBlockHeight: {responses[0].get('error', 'no result key')}"
                    )
                block_height = responses[0]["result"]
                gas_price = Decimal("0.000005")  # Placeholder

        results = [
            OnChainMetrics(
                asset=chain.upper(),
                metric_name="block_height",
                metric_value=Decimal(block_height),
                source="GlassChainWalker",
            ),
            OnChainMetrics(
                asset=chain.upper(),
                metric_name="gas_price",
                metric_value=gas_price,
                source="GlassChainWalker",
            ),
        ]

        return results


# Register strategy
CollectorRegistry.register(GlassChainWalker)
