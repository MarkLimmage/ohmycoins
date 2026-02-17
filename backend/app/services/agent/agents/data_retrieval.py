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
            description="Fetches comprehensive cryptocurrency data including price, sentiment, on-chain metrics, and catalyst events"
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
        if self.session is None:
            state["error"] = "Database session not configured"
            state["data_retrieved"] = False
            return state

        try:
            # Parse user goal to determine what data to fetch
            user_goal = state.get("user_goal", "")
            retrieval_params = state.get("retrieval_params", {})

            # Default time range: last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=retrieval_params.get("days", 30))

            # Determine coin type from goal or params
            coin_type = retrieval_params.get("coin_type", "BTC")

            # Initialize data dictionary
            retrieved_data: dict[str, Any] = {}

            # Always fetch available coins
            retrieved_data["available_coins"] = await get_available_coins(self.session)

            # Fetch data statistics
            retrieved_data["data_statistics"] = await get_data_statistics(
                self.session,
                coin_type=coin_type
            )

            # Fetch price data if requested or by default
            if "price" in user_goal.lower() or retrieval_params.get("include_price", True):
                retrieved_data["price_data"] = await fetch_price_data(
                    self.session,
                    coin_type=coin_type,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Fetch sentiment data if requested
            if "sentiment" in user_goal.lower() or retrieval_params.get("include_sentiment", False):
                currencies = retrieval_params.get("currencies", [coin_type])
                retrieved_data["sentiment_data"] = await fetch_sentiment_data(
                    self.session,
                    start_date=start_date,
                    end_date=end_date,
                    currencies=currencies,
                )

            # Fetch on-chain metrics if requested
            if "on-chain" in user_goal.lower() or "onchain" in user_goal.lower() or retrieval_params.get("include_onchain", False):
                retrieved_data["on_chain_metrics"] = await fetch_on_chain_metrics(
                    self.session,
                    asset=coin_type,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Fetch catalyst events if requested
            if "catalyst" in user_goal.lower() or "event" in user_goal.lower() or retrieval_params.get("include_catalysts", False):
                currencies = retrieval_params.get("currencies", [coin_type])
                retrieved_data["catalyst_events"] = await fetch_catalyst_events(
                    self.session,
                    start_date=start_date,
                    end_date=end_date,
                    currencies=currencies,
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
