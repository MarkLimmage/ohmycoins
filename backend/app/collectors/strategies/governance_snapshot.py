"""
Snapshot governance proposals collector plugin (Catalyst Ledger).

This collector fetches active and recently closed governance proposals from
Snapshot for major DeFi protocols, mapping them to CatalystEvents for
downstream analysis.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp

from app.core.collectors.base import ICollector
from app.core.collectors.registry import CollectorRegistry
from app.models import CatalystEvents

logger = logging.getLogger(__name__)

DEFAULT_SPACES = [
    "uniswap",
    "aave.eth",
    "ens.eth",
    "gitcoindao.eth",
    "arbitrumfoundation.eth",
    "safe.eth",
    "lido-snapshot.eth",
    "starknet.eth",
]

GRAPHQL_ENDPOINT = "https://hub.snapshot.org/graphql"

# Map Snapshot space IDs to relevant crypto tickers
SPACE_CURRENCY_MAP: dict[str, list[str]] = {
    "uniswap": ["UNI"],
    "aave.eth": ["AAVE"],
    "ens.eth": ["ENS"],
    "gitcoindao.eth": ["GTC"],
    "arbitrumfoundation.eth": ["ARB"],
    "safe.eth": ["SAFE"],
    "lido-snapshot.eth": ["LDO"],
    "starknet.eth": ["STRK"],
}

PROPOSALS_QUERY = """
query($spaces: [String!], $state: String!, $createdGte: Int) {
  proposals(
    first: 20,
    skip: 0,
    where: {
      space_in: $spaces,
      state: $state,
      created_gte: $createdGte
    },
    orderBy: "created",
    orderDirection: desc
  ) {
    id
    title
    body
    choices
    start
    end
    state
    scores
    scores_total
    author
    space { id name }
    created
  }
}
"""


class SnapshotGovernanceCollector(ICollector):
    """Collector for DeFi governance proposals from Snapshot."""

    @property
    def name(self) -> str:
        return "governance_snapshot"

    @property
    def description(self) -> str:
        return "DeFi governance proposals from Snapshot"

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "spaces": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Snapshot space IDs to monitor",
                    "default": DEFAULT_SPACES,
                },
            },
            "required": [],
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        if "spaces" in config:
            if not isinstance(config["spaces"], list):
                logger.error("Invalid config: 'spaces' must be a list")
                return False
        return True

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """Test connectivity to Snapshot GraphQL API."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": '{ proposals(first: 1, where: { space: "uniswap" }) { id } }'
                }
                async with session.post(
                    GRAPHQL_ENDPOINT,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return False
                    data = await resp.json()
                    return "data" in data
        except Exception as e:
            logger.error(f"Failed to test Snapshot connection: {e}")
            return False

    async def _fetch_proposals(
        self,
        session: aiohttp.ClientSession,
        spaces: list[str],
        state: str,
        created_gte: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch proposals from Snapshot GraphQL API."""
        variables: dict[str, Any] = {
            "spaces": spaces,
            "state": state,
        }
        if created_gte is not None:
            variables["createdGte"] = created_gte
        else:
            variables["createdGte"] = 0

        payload = {"query": PROPOSALS_QUERY, "variables": variables}

        async with session.post(
            GRAPHQL_ENDPOINT,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                logger.warning(f"Snapshot API returned status {resp.status}")
                return []
            data = await resp.json()

        if "errors" in data:
            logger.warning(f"Snapshot GraphQL errors: {data['errors']}")
            return []

        return data.get("data", {}).get("proposals", [])

    def _proposal_to_catalyst(self, proposal: dict[str, Any]) -> CatalystEvents:
        """Map a Snapshot proposal to a CatalystEvents instance."""
        space = proposal.get("space", {})
        space_id = space.get("id", "unknown")

        # Truncate body to 500 chars
        body = proposal.get("body", "") or ""
        description = body[:500] if body else None

        proposal_id = proposal.get("id", "")
        url = f"https://snapshot.box/#/s:{space_id}/proposal/{proposal_id}"

        # Map space to currencies
        currencies = SPACE_CURRENCY_MAP.get(space_id, [])

        created_ts = proposal.get("created")
        if created_ts:
            detected_at = datetime.fromtimestamp(created_ts, tz=timezone.utc)
        else:
            detected_at = datetime.now(timezone.utc)

        return CatalystEvents(
            event_type="governance",
            title=proposal.get("title", "Untitled Proposal"),
            description=description,
            source="snapshot",
            currencies=currencies or None,
            impact_score=5,  # Governance proposals default to medium impact
            detected_at=detected_at,
            url=url,
            collected_at=datetime.now(timezone.utc),
        )

    async def collect(self, config: dict[str, Any]) -> list[Any]:
        """Collect active and recently closed governance proposals from Snapshot."""
        spaces = config.get("spaces", DEFAULT_SPACES)
        logger.info(
            f"Collecting Snapshot governance proposals for {len(spaces)} spaces"
        )

        all_events: list[CatalystEvents] = []
        seen_ids: set[str] = set()

        async with aiohttp.ClientSession() as session:
            # Fetch active proposals
            try:
                active_proposals = await self._fetch_proposals(
                    session, spaces, state="active"
                )
                logger.info(f"Fetched {len(active_proposals)} active proposals")
                for proposal in active_proposals:
                    pid = proposal.get("id", "")
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    all_events.append(self._proposal_to_catalyst(proposal))
            except Exception as e:
                logger.error(f"Failed to fetch active proposals: {e}")

            # Fetch recently closed proposals (last 7 days)
            try:
                seven_days_ago = int(time.time()) - (7 * 24 * 3600)
                closed_proposals = await self._fetch_proposals(
                    session, spaces, state="closed", created_gte=seven_days_ago
                )
                logger.info(
                    f"Fetched {len(closed_proposals)} recently closed proposals"
                )
                for proposal in closed_proposals:
                    pid = proposal.get("id", "")
                    if pid in seen_ids:
                        continue
                    seen_ids.add(pid)
                    all_events.append(self._proposal_to_catalyst(proposal))
            except Exception as e:
                logger.error(f"Failed to fetch closed proposals: {e}")

        logger.info(f"Collected {len(all_events)} Snapshot governance events")
        return all_events


CollectorRegistry.register(SnapshotGovernanceCollector)
