"""
Nansen Smart Money netflow collector plugin (Glass Ledger).

Fetches smart money net-flow data from the Nansen API and stores it as
SmartMoneyFlow model instances. Tracks what successful/smart wallets are
buying and selling across tracked tokens.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from app.core.collectors.base import ICollector
from app.models import SmartMoneyFlow

logger = logging.getLogger(__name__)

NANSEN_BASE_URL = "https://api.nansen.ai/api/v1"
REQUEST_TIMEOUT = 30.0
TOTAL_TIMEOUT = 120.0
MAX_PAGES = 10
BACKOFF_BASE = 1.0
BACKOFF_MAX = 16.0
MAX_RETRIES = 3


class GlassNansen(ICollector):
    """Collector for smart money wallet flows from Nansen API."""

    TRACKED_TOKENS = [
        "LINK",
        "ARKM",
        "AAVE",
        "PUFFER",
        "BIO",
        "CYBER",
        "MAVIA",
        "GEAR",
        "REZ",
        "DAO",
    ]

    @property
    def name(self) -> str:
        return "glass_nansen"

    @property
    def description(self) -> str:
        return "Smart money wallet flows from Nansen API"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Nansen API key (falls back to NANSEN_API_KEY env var)",
                },
                "chains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Blockchain networks to query",
                    "default": ["ethereum"],
                },
                "tokens": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Token symbols to track",
                    "default": self.TRACKED_TOKENS,
                    "examples": ["LINK", "ARKM", "AAVE", "PUFFER"],
                },
                "rate_limit_delay": {
                    "type": "number",
                    "description": "Delay between paginated requests in seconds",
                    "default": 0.1,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "chains" in config:
            if not isinstance(config["chains"], list):
                logger.error("Invalid config: 'chains' must be a list")
                return False
            if not all(isinstance(c, str) for c in config["chains"]):
                logger.error("Invalid config: all chains must be strings")
                return False

        if "tokens" in config:
            if not isinstance(config["tokens"], list):
                logger.error("Invalid config: 'tokens' must be a list")
                return False
            if not all(isinstance(t, str) for t in config["tokens"]):
                logger.error("Invalid config: all tokens must be strings")
                return False

        if "rate_limit_delay" in config:
            try:
                float(config["rate_limit_delay"])
            except (ValueError, TypeError):
                logger.error("Invalid config: 'rate_limit_delay' must be a number")
                return False

        return True

    def _resolve_api_key(self, config: dict[str, Any]) -> str | None:
        """Resolve API key from config first, then environment variable."""
        return config.get("api_key") or os.getenv("NANSEN_API_KEY")

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to Nansen API with a minimal request."""
        api_key = self._resolve_api_key(config)
        if not api_key:
            logger.warning("No Nansen API key available for connection test")
            return False

        try:
            timeout = httpx.Timeout(REQUEST_TIMEOUT, connect=REQUEST_TIMEOUT)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{NANSEN_BASE_URL}/smart-money/netflow",
                    headers={"apikey": api_key},
                    json={
                        "chains": ["ethereum"],
                        "filters": {
                            "include_smart_money_labels": ["Fund", "Smart Trader"],
                            "include_stablecoins": False,
                        },
                        "pagination": {"page": 1, "per_page": 1},
                        "order_by": [
                            {"field": "net_flow_24h_usd", "direction": "DESC"}
                        ],
                    },
                )
                if response.status_code == 200:
                    logger.info("Nansen API connection test succeeded")
                    return True
                logger.warning(
                    "Nansen API connection test failed: status %d", response.status_code
                )
                return False
        except Exception as e:
            logger.error("Failed to test Nansen connection: %s", e)
            return False

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect smart money netflow data from Nansen API."""
        api_key = self._resolve_api_key(config)
        if not api_key:
            logger.warning(
                "No Nansen API key configured — skipping collection. "
                "Set NANSEN_API_KEY env var or pass api_key in config."
            )
            return []

        chains = config.get("chains", ["ethereum"])
        tracked_tokens = {t.upper() for t in config.get("tokens", self.TRACKED_TOKENS)}
        rate_limit_delay = config.get("rate_limit_delay", 0.1)

        logger.info(
            "Collecting Nansen smart money netflow for chains=%s, tokens=%s",
            chains,
            tracked_tokens,
        )

        all_data: list[Any] = []
        try:
            await asyncio.wait_for(
                self._collect_all(
                    api_key, chains, tracked_tokens, rate_limit_delay, all_data
                ),
                timeout=TOTAL_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Nansen collection timed out after %.0fs, returning %d records",
                TOTAL_TIMEOUT,
                len(all_data),
            )

        logger.info("Collected %d smart money flow records", len(all_data))
        return all_data

    async def _collect_all(
        self,
        api_key: str,
        chains: list[str],
        tracked_tokens: set[str],
        rate_limit_delay: float,
        all_data: list[Any],
    ) -> None:
        """Inner collection loop, separated so wait_for can wrap it."""
        timeout = httpx.Timeout(REQUEST_TIMEOUT, connect=REQUEST_TIMEOUT)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for chain in chains:
                page = 1
                while page <= MAX_PAGES:
                    try:
                        if page > 1:
                            await asyncio.sleep(rate_limit_delay)

                        response_data = await self._fetch_page(
                            client, api_key, chain, page
                        )
                        if response_data is None:
                            break

                        items = response_data.get("data", [])
                        collected_at = datetime.now(timezone.utc)

                        for item in items:
                            symbol = (item.get("token_symbol") or "").upper()
                            if symbol not in tracked_tokens:
                                continue

                            net_flow = item.get("net_flow_24h_usd", 0.0)
                            trader_count = item.get("trader_count", 0)

                            flow = SmartMoneyFlow(
                                token=symbol,
                                net_flow_usd=Decimal(str(net_flow)),
                                buying_wallet_count=(
                                    trader_count if net_flow > 0 else 0
                                ),
                                selling_wallet_count=(
                                    trader_count if net_flow < 0 else 0
                                ),
                                buying_wallets=None,
                                selling_wallets=None,
                                collected_at=collected_at,
                            )
                            all_data.append(flow)

                        pagination = response_data.get("pagination", {})
                        if pagination.get("is_last_page", True):
                            break
                        page += 1

                    except Exception as e:
                        logger.error(
                            "Failed to collect Nansen data for chain=%s page=%d: %s",
                            chain,
                            page,
                            e,
                        )
                        break

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        chain: str,
        page: int,
    ) -> dict[str, Any] | None:
        """Fetch a single page of netflow data with retry and backoff on 429."""
        body = {
            "chains": [chain],
            "filters": {
                "include_smart_money_labels": ["Fund", "Smart Trader"],
                "include_stablecoins": False,
            },
            "pagination": {"page": page, "per_page": 100},
            "order_by": [{"field": "net_flow_24h_usd", "direction": "DESC"}],
        }

        backoff = BACKOFF_BASE
        for attempt in range(MAX_RETRIES + 1):
            response = await client.post(
                f"{NANSEN_BASE_URL}/smart-money/netflow",
                headers={"apikey": api_key},
                json=body,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "Nansen rate limited (429), backing off %.1fs (attempt %d/%d)",
                        backoff,
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, BACKOFF_MAX)
                    continue
                logger.error("Nansen rate limit exceeded after %d retries", MAX_RETRIES)
                return None

            if response.status_code in (401, 403):
                logger.error(
                    "Nansen API auth error (%d): %s",
                    response.status_code,
                    response.text,
                )
                return None

            logger.warning(
                "Nansen API returned status %d for chain=%s page=%d: %s",
                response.status_code,
                chain,
                page,
                response.text,
            )
            return None

        return None


# Register the collector
from app.core.collectors.registry import CollectorRegistry  # noqa: E402

CollectorRegistry.register(GlassNansen)
