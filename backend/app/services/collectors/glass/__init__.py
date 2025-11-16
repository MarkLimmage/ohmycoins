# glass ledger collectors
"""
Glass Ledger collectors for on-chain and fundamental blockchain data.

Collectors:
- DeFiLlama: Protocol TVL, fees, and revenue data
"""

from .defillama import DeFiLlamaCollector

__all__ = ["DeFiLlamaCollector"]
