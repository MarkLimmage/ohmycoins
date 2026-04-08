"""Quick smoke test — requires network access."""

import asyncio

import pytest

from app.collectors.strategies.glass_chain_walker import GlassChainWalker


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ethereum_rpc_reachable():
    """At least one public Ethereum RPC should respond."""
    collector = GlassChainWalker()
    result = await collector.collect({"chain": "ethereum"})
    assert len(result) > 0, "Should return at least one on-chain metric"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_solana_rpc_reachable():
    """Solana public RPC should respond."""
    collector = GlassChainWalker()
    result = await collector.collect({"chain": "solana"})
    assert len(result) > 0
