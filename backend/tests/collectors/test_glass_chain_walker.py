"""Unit tests for GlassChainWalker RPC fallback logic."""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.collectors.strategies.glass_chain_walker import (
    CONNECTION_TIMEOUT_SECONDS,
    ETHEREUM_RPC_ENDPOINTS,
    SOLANA_RPC_ENDPOINTS,
    GlassChainWalker,
    _get_rpc_endpoints,
)


@pytest.fixture
def walker():
    return GlassChainWalker()


# ---------------------------------------------------------------------------
# Helper: build a fake httpx.Response
# ---------------------------------------------------------------------------

def _make_response(json_body: dict, status_code: int = 200) -> httpx.Response:
    resp = httpx.Response(status_code=status_code, json=json_body)
    return resp


# ---------------------------------------------------------------------------
# _get_rpc_endpoints
# ---------------------------------------------------------------------------


class TestGetRpcEndpoints:
    def test_ethereum_defaults(self):
        endpoints = _get_rpc_endpoints("ethereum", {})
        assert endpoints == ETHEREUM_RPC_ENDPOINTS

    def test_solana_defaults(self):
        endpoints = _get_rpc_endpoints("solana", {})
        assert endpoints == SOLANA_RPC_ENDPOINTS

    def test_custom_rpc_url_takes_priority(self):
        custom = "https://my-custom-rpc.example.com"
        endpoints = _get_rpc_endpoints("ethereum", {"rpc_url": custom})
        assert endpoints[0] == custom
        # Fallbacks still present after the custom URL
        assert len(endpoints) == len(ETHEREUM_RPC_ENDPOINTS) + 1

    def test_custom_url_not_duplicated_if_already_in_list(self):
        # If user provides one of the defaults, it shouldn't appear twice
        custom = ETHEREUM_RPC_ENDPOINTS[0]
        endpoints = _get_rpc_endpoints("ethereum", {"rpc_url": custom})
        assert endpoints.count(custom) == 1
        assert endpoints[0] == custom


# ---------------------------------------------------------------------------
# collect() fallback behaviour
# ---------------------------------------------------------------------------


class TestCollectFallback:
    @pytest.mark.asyncio
    async def test_fallback_to_second_endpoint(self, walker):
        """First RPC raises ConnectError; second returns valid data."""
        call_count = 0

        async def fake_post(url, *, json, **kwargs):
            nonlocal call_count
            call_count += 1
            # First endpoint always fails
            if ETHEREUM_RPC_ENDPOINTS[0] in str(url):
                raise httpx.ConnectError("Connection refused")
            # Second endpoint succeeds
            if json.get("method") == "eth_blockNumber":
                return _make_response({"jsonrpc": "2.0", "id": 1, "result": "0x1234"})
            if json.get("method") == "eth_gasPrice":
                return _make_response({"jsonrpc": "2.0", "id": 2, "result": "0x3B9ACA00"})
            raise AssertionError(f"Unexpected method: {json}")

        with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = fake_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            results = await walker.collect({"chain": "ethereum"})

        assert len(results) == 2
        block = next(r for r in results if r.metric_name == "block_height")
        assert block.metric_value == Decimal(0x1234)

    @pytest.mark.asyncio
    async def test_all_endpoints_fail(self, walker):
        """All RPCs fail — collector should raise RuntimeError."""

        async def fail_post(url, *, json, **kwargs):
            raise httpx.ConnectError("Connection refused")

        with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = fail_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="All RPC endpoints exhausted"):
                await walker.collect({"chain": "ethereum"})

    @pytest.mark.asyncio
    async def test_custom_rpc_url_takes_priority(self, walker):
        """When rpc_url is set in config, it's tried before fallbacks."""
        custom_url = "https://my-super-rpc.example.com"
        called_urls: list[str] = []

        async def tracking_post(url, *, json, **kwargs):
            called_urls.append(str(url))
            if json.get("method") == "eth_blockNumber":
                return _make_response({"jsonrpc": "2.0", "id": 1, "result": "0xABCD"})
            if json.get("method") == "eth_gasPrice":
                return _make_response({"jsonrpc": "2.0", "id": 2, "result": "0x3B9ACA00"})
            raise AssertionError(f"Unexpected method: {json}")

        with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = tracking_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            results = await walker.collect({"chain": "ethereum", "rpc_url": custom_url})

        # The custom URL should be the one that was called (successfully on first try)
        assert all(custom_url in u for u in called_urls)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_timeout_handling(self, walker):
        """RPC that times out should be skipped; next endpoint should be tried."""

        async def timeout_then_ok(url, *, json, **kwargs):
            if ETHEREUM_RPC_ENDPOINTS[0] in str(url):
                raise httpx.TimeoutException("Read timed out")
            if json.get("method") == "eth_blockNumber":
                return _make_response({"jsonrpc": "2.0", "id": 1, "result": "0xFF"})
            if json.get("method") == "eth_gasPrice":
                return _make_response({"jsonrpc": "2.0", "id": 2, "result": "0x1"})
            raise AssertionError(f"Unexpected method: {json}")

        with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = timeout_then_ok
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            results = await walker.collect({"chain": "ethereum"})

        assert len(results) == 2
        block = next(r for r in results if r.metric_name == "block_height")
        assert block.metric_value == Decimal(0xFF)

    @pytest.mark.asyncio
    async def test_connection_timeout_is_set(self, walker):
        """Verify the httpx.Timeout is created with the configured timeout."""
        timeouts_used: list = []

        original_timeout_init = httpx.Timeout.__init__

        with patch("app.collectors.strategies.glass_chain_walker.httpx.Timeout") as mock_timeout:
            mock_timeout.return_value = httpx.Timeout(CONNECTION_TIMEOUT_SECONDS, connect=CONNECTION_TIMEOUT_SECONDS)

            async def ok_post(url, *, json, **kwargs):
                if json.get("method") == "eth_blockNumber":
                    return _make_response({"jsonrpc": "2.0", "id": 1, "result": "0x1"})
                if json.get("method") == "eth_gasPrice":
                    return _make_response({"jsonrpc": "2.0", "id": 2, "result": "0x1"})
                raise AssertionError(f"Unexpected method: {json}")

            with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
                mock_client = AsyncMock()
                mock_client.post = ok_post
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_cls.return_value = mock_client

                await walker.collect({"chain": "ethereum"})

            mock_timeout.assert_called_with(CONNECTION_TIMEOUT_SECONDS, connect=CONNECTION_TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# test_connection() with fallback
# ---------------------------------------------------------------------------


class TestTestConnection:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_true(self, walker):
        result = await walker.test_connection({"chain": "ethereum", "mock_mode": True})
        assert result is True

    @pytest.mark.asyncio
    async def test_all_fail_returns_false(self, walker):
        async def fail_post(url, *, json, **kwargs):
            raise httpx.ConnectError("refused")

        with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = fail_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            result = await walker.test_connection({"chain": "ethereum"})

        assert result is False

    @pytest.mark.asyncio
    async def test_second_endpoint_succeeds(self, walker):
        async def second_ok(url, *, json, **kwargs):
            if ETHEREUM_RPC_ENDPOINTS[0] in str(url):
                raise httpx.ConnectError("refused")
            return _make_response({"jsonrpc": "2.0", "id": 1, "result": "0x1"})

        with patch("app.collectors.strategies.glass_chain_walker.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = second_ok
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            result = await walker.test_connection({"chain": "ethereum"})

        assert result is True


# ---------------------------------------------------------------------------
# Mock mode
# ---------------------------------------------------------------------------


class TestMockMode:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_data(self, walker):
        results = await walker.collect({"chain": "ethereum", "mock_mode": True})
        assert len(results) == 2
        assert results[0].asset == "ETHEREUM"
        assert results[0].source == "GlassChainWalker"

    @pytest.mark.asyncio
    async def test_mock_mode_solana(self, walker):
        results = await walker.collect({"chain": "solana", "mock_mode": True})
        assert len(results) == 2
        assert results[0].asset == "SOLANA"
