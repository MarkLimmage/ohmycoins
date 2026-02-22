from typing import Any, Dict, List
import random
import logging
import httpx
from decimal import Decimal

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import OnChainMetrics

logger = logging.getLogger(__name__)

class GlassChainWalker(ICollector):
    @property
    def name(self) -> str:
        return "GlassChainWalker"

    @property
    def description(self) -> str:
        return "Connects to public blockchain RPCs to fetch block height and gas prices."

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chain": {"type": "string", "enum": ["ethereum", "solana"], "default": "ethereum"},
                "rpc_url": {"type": "string", "default": "https://eth.llamarpc.com"},
                "mock_mode": {"type": "boolean", "default": True}
            },
            "required": ["chain"]
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        if "chain" not in config:
            return False
        if config["chain"] not in ["ethereum", "solana"]:
            return False
        return True

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        if config.get("mock_mode", False):
            return True
        
        rpc_url = config.get("rpc_url")
        if not rpc_url:
             return False

        try:
             async with httpx.AsyncClient() as client:
                 if config["chain"] == "ethereum":
                     payload = {
                         "jsonrpc": "2.0",
                         "method": "eth_blockNumber",
                         "params": [],
                         "id": 1
                     }
                     response = await client.post(rpc_url, json=payload, timeout=5.0)
                     response.raise_for_status()
                     return True
                 elif config["chain"] == "solana":
                     payload = {
                         "jsonrpc": "2.0",
                         "id": 1,
                         "method": "getBlockHeight"
                     }
                     response = await client.post(rpc_url, json=payload, timeout=5.0)
                     response.raise_for_status()
                     return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
        return False

    async def collect(self, config: Dict[str, Any]) -> List[Any]:
        results = []
        chain = config["chain"]
        mock_mode = config.get("mock_mode", False)
        rpc_url = config.get("rpc_url", "https://eth.llamarpc.com" if chain == "ethereum" else "https://api.mainnet-beta.solana.com")

        block_height = 0
        gas_price = Decimal(0)

        if mock_mode:
            # Simulate plausible data
            if chain == "ethereum":
                block_height = 19000000 + random.randint(1, 1000)
                gas_price = Decimal(random.uniform(10, 50)) # Gwei
            else: # solana
                block_height = 200000000 + random.randint(1, 10000)
                gas_price = Decimal(random.uniform(0.000005, 0.00001)) # SOL (lamports usually but let's say "price")
        else:
            try:
                async with httpx.AsyncClient() as client:
                    if chain == "ethereum":
                        # Fetch Block Number
                        payload = {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}
                        resp = await client.post(rpc_url, json=payload, timeout=10.0)
                        data = resp.json()
                        block_height = int(data["result"], 16)
                        
                        # Fetch Gas Price
                        payload_gas = {"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}
                        resp_gas = await client.post(rpc_url, json=payload_gas, timeout=10.0)
                        data_gas = resp_gas.json()
                        gas_price_wei = int(data_gas["result"], 16)
                        gas_price = Decimal(gas_price_wei) / Decimal(10**9) # Convert to Gwei

                    elif chain == "solana":
                        # Fetch Block Height
                        payload = {"jsonrpc": "2.0", "id": 1, "method": "getBlockHeight"}
                        resp = await client.post(rpc_url, json=payload, timeout=10.0)
                        data = resp.json()
                        block_height = data["result"]
                        
                        # Solana doesn't have "gas price" in the same way, maybe use a fixed mock or fetch fees if possible
                        # For now, let's just mock gas/fee or skip
                        gas_price = Decimal(0.000005) # Placeholder
            
            except Exception as e:
                logger.error(f"Failed to collect from {chain} RPC: {e}")
                # Fallback to mock in case of failure? Or re-raise?
                # Instruction says: "Mock Mode: If RPC fails or is rate-limited, simulate plausible block data."
                logger.warning("Falling back to mock data due to error.")
                if chain == "ethereum":
                    block_height = 19000000 + random.randint(1, 1000)
                    gas_price = Decimal(random.uniform(10, 50))
                else:
                    block_height = 200000000 + random.randint(1, 10000)
                    gas_price = Decimal(random.uniform(0.000005, 0.00001))

        # Create OnChainMetrics entries
        # Need to know the field names in OnChainMetrics model. 
        # Using grep_search I saw:
        # asset: str
        # metric_name: str
        # metric_value: Decimal
        
        results.append(OnChainMetrics(
            asset=chain.upper(),
            metric_name="block_height",
            metric_value=Decimal(block_height)
        ))
         
        results.append(OnChainMetrics(
            asset=chain.upper(),
            metric_name="gas_price",
            metric_value=gas_price
        ))

        return results

# Register strategy
CollectorRegistry.register(GlassChainWalker)
