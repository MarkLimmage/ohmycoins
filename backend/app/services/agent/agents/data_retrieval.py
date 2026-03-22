"""
Data Retrieval Agent - Fetches cryptocurrency data from database.

Week 3-4 implementation: Enhanced with comprehensive data retrieval tools.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session

from ..tools import (
    fetch_catalyst_events,
    fetch_on_chain_metrics,
    fetch_price_data,
    fetch_sentiment_data,
    get_available_coins,
    get_data_statistics,
)
from .base import BaseAgent


class DataRetrievalAgent(BaseAgent):
    """
    Agent responsible for retrieving data from the database.

    Enhanced Week 3-4 Implementation with Tools:
    - fetch_price_data: Query price_data_5min table
    - fetch_sentiment_data: Fetch news and social sentiment (Phase 2.5)
    - fetch_on_chain_metrics: Fetch on-chain metrics (Phase 2.5)
    - fetch_catalyst_events: Fetch catalyst events (Phase 2.5)
    - get_available_coins: List all available cryptocurrencies
    - get_data_statistics: Get data coverage statistics
    """

    def __init__(self, session: Session | None = None) -> None:
        """
        Initialize the data retrieval agent.

        Args:
            session: Optional database session (can be set later)
        """
        super().__init__(
            name="DataRetrievalAgent",
            description="Fetches comprehensive cryptocurrency data including price, sentiment, on-chain metrics, and catalyst events",
        )
        self.session = session

    def set_session(self, session: Session) -> None:
        """
        Set the database session for the agent.

        Args:
            session: Database session
        """
        self.session = session

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute data retrieval based on user goal.

        Args:
            state: Current workflow state with user_goal and optional parameters

        Returns:
            Updated state with retrieved data
        """
        # Initialize pending events for this execution step
        state["pending_events"] = []

        if self.session is None:
            state["error"] = "Database session not configured"
            state["data_retrieved"] = False
            await self.emit_event(
                state,
                "error",
                "DATA_ACQUISITION",
                {"error": "Database session not configured"},
            )
            return state

        try:
            await self.emit_event(
                state,
                "status_update",
                "DATA_ACQUISITION",
                {
                    "status": "ACTIVE",
                    "message": "Starting data retrieval...",
                    "task_id": "fetch_price_data"
                },
            )

            # Parse user goal to determine what data to fetch
            user_goal = state.get("user_goal", "")
            retrieval_params = state.get("retrieval_params", {})

            # Default time range: last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=retrieval_params.get("days", 30))

            # Determine coin type from goal or params (normalise to lowercase)
            coin_type = retrieval_params.get("coin_type", "BTC").lower()

            # Emit conversational update (stream_chat)
            await self.emit_event(
                state,
                "stream_chat",
                "DATA_ACQUISITION",
                {
                    "message": f"I'm initiating data retrieval for {coin_type}. Checking available datasets for the last {retrieval_params.get('days', 30)} days...",
                    "sender": "DataRetrievalAgent"
                },
            )

            # Initialize data dictionary
            retrieved_data: dict[str, Any] = {}

            # Always fetch available coins
            retrieved_data["available_coins"] = await get_available_coins(self.session)

            # Fetch data statistics
            await self.emit_event(
                state,
                "status_update",
                "DATA_ACQUISITION",
                {
                    "status": "ACTIVE",
                    "message": f"Fetching statistics for {coin_type}...",
                    "task_id": "fetch_price_data"
                },
            )
            retrieved_data["data_statistics"] = await get_data_statistics(
                self.session, coin_type=coin_type
            )

            # Fetch price data if requested or by default
            if "price" in user_goal.lower() or retrieval_params.get(
                "include_price", True
            ):
                await self.emit_event(
                    state,
                    "stream_chat",
                    "DATA_ACQUISITION",
                    {"message": "Querying historical OHLCV price data...", "sender": "DataRetrievalAgent"},
                )
                await self.emit_event(
                    state,
                    "status_update",
                    "DATA_ACQUISITION",
                    {
                        "status": "ACTIVE",
                        "message": f"Fetching {retrieval_params.get('days', 30)} days of {coin_type} price data",
                        "task_id": "fetch_price_data"
                    },
                )
                retrieved_data["price_data"] = await fetch_price_data(
                    self.session,
                    coin_type=coin_type,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Fetch sentiment data if requested
            if "sentiment" in user_goal.lower() or retrieval_params.get(
                "include_sentiment", False
            ):
                currencies = retrieval_params.get("currencies", [coin_type])
                retrieved_data["sentiment_data"] = await fetch_sentiment_data(
                    self.session,
                    start_date=start_date,
                    end_date=end_date,
                    currencies=currencies,
                )

            # Fetch on-chain metrics if requested
            if (
                "on-chain" in user_goal.lower()
                or "onchain" in user_goal.lower()
                or retrieval_params.get("include_onchain", False)
            ):
                retrieved_data["on_chain_metrics"] = await fetch_on_chain_metrics(
                    self.session,
                    asset=coin_type,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Fetch catalyst events if requested
            if (
                "catalyst" in user_goal.lower()
                or "event" in user_goal.lower()
                or retrieval_params.get("include_catalysts", False)
            ):
                currencies = retrieval_params.get("currencies", [coin_type])
                retrieved_data["catalyst_events"] = await fetch_catalyst_events(
                    self.session,
                    start_date=start_date,
                    end_date=end_date,
                    currencies=currencies,
                )

            # --- Build outcome summary for StageOutputs panel ---
            summary_lines = ["## Data Acquisition Results\n"]
            summary_lines.append(
                f"**Coin**: `{coin_type}` &nbsp; "
                f"**Period**: {start_date.strftime('%Y-%m-%d')} → "
                f"{end_date.strftime('%Y-%m-%d')} "
                f"({retrieval_params.get('days', 30)} days)\n"
            )
            summary_lines.append("| Dataset | Rows | Notes |")
            summary_lines.append("|---------|-----:|-------|")

            if "price_data" in retrieved_data:
                n = len(retrieved_data["price_data"])
                note = "" if n > 0 else "⚠ No rows returned"
                summary_lines.append(f"| Price (5 min) | {n:,} | {note} |")

            if "sentiment_data" in retrieved_data:
                sd = retrieved_data["sentiment_data"]
                news_n = len(sd.get("news_sentiment", []))
                social_n = len(sd.get("social_sentiment", []))
                summary_lines.append(f"| News sentiment | {news_n:,} | |")
                summary_lines.append(f"| Social sentiment | {social_n:,} | |")

            if "on_chain_metrics" in retrieved_data:
                n = len(retrieved_data["on_chain_metrics"])
                summary_lines.append(f"| On-chain metrics | {n:,} | |")

            if "catalyst_events" in retrieved_data:
                n = len(retrieved_data["catalyst_events"])
                summary_lines.append(f"| Catalyst events | {n:,} | |")

            # DB coverage from statistics
            ds = retrieved_data.get("data_statistics", {})
            ps = ds.get("price_data", {})
            if ps.get("earliest_timestamp") and ps.get("latest_timestamp"):
                summary_lines.append(
                    f"\n**DB coverage**: "
                    f"{ps['earliest_timestamp'][:10]} → {ps['latest_timestamp'][:10]} "
                    f"({ps['total_records']:,} total price records)"
                )

            coins = retrieved_data.get("available_coins", [])
            if coins:
                summary_lines.append(
                    f"\n**Available coins**: {', '.join(f'`{c}`' for c in coins)}"
                )

            await self.emit_event(
                state,
                "render_output",
                "DATA_ACQUISITION",
                {
                    "mime_type": "text/markdown",
                    "content": "\n".join(summary_lines),
                },
            )

            # Update state
            state["data_retrieved"] = True
            state["retrieved_data"] = retrieved_data
            state["message"] = f"Successfully retrieved data for {coin_type}"

            # Add metadata
            state["retrieval_metadata"] = {
                "coin_type": coin_type,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data_types": list(retrieved_data.keys()),
            }

        except Exception as e:
            state["error"] = f"Data retrieval failed: {str(e)}"
            state["data_retrieved"] = False

        return state
