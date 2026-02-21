"""
Data Analyst Agent - Analyzes cryptocurrency data and generates insights.

Week 3-4 implementation: New agent for comprehensive data analysis.
"""

from typing import Any

from ..tools import (
    analyze_on_chain_signals,
    analyze_sentiment_trends,
    calculate_technical_indicators,
    detect_catalyst_impact,
    perform_eda,
)
from .base import BaseAgent


class DataAnalystAgent(BaseAgent):
    """
    Agent responsible for analyzing cryptocurrency data.

    Week 3-4 Implementation Tools:
    - calculate_technical_indicators: Compute RSI, MACD, Bollinger Bands, etc.
    - analyze_sentiment_trends: Analyze sentiment from news and social media
    - analyze_on_chain_signals: Analyze on-chain metrics for trading signals
    - detect_catalyst_impact: Detect impact of events on price movements
    - clean_data: Clean and preprocess data
    - perform_eda: Perform exploratory data analysis
    """

    def __init__(self) -> None:
        """Initialize the data analyst agent."""
        super().__init__(
            name="DataAnalystAgent",
            description="Analyzes cryptocurrency data and generates actionable insights",
        )

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute data analysis based on retrieved data and user goal.

        Args:
            state: Current workflow state with retrieved_data

        Returns:
            Updated state with analysis results
        """
        try:
            # Get retrieved data from previous agent
            retrieved_data = state.get("retrieved_data", {})

            if not retrieved_data:
                state["error"] = "No data available for analysis"
                state["analysis_completed"] = False
                return state

            user_goal = state.get("user_goal", "")
            analysis_params = state.get("analysis_params", {})

            # Initialize analysis results
            analysis_results: dict[str, Any] = {}

            # Perform EDA on available data
            if "eda" in user_goal.lower() or analysis_params.get("include_eda", True):
                analysis_results["exploratory_analysis"] = {}

                if "price_data" in retrieved_data and retrieved_data["price_data"]:
                    analysis_results["exploratory_analysis"]["price_eda"] = perform_eda(
                        retrieved_data["price_data"]
                    )

            # Calculate technical indicators if price data available
            if "price_data" in retrieved_data and retrieved_data["price_data"]:
                indicators_to_calc = analysis_params.get("indicators", None)

                if (
                    "indicator" in user_goal.lower()
                    or "technical" in user_goal.lower()
                    or analysis_params.get("include_indicators", True)
                ):
                    # Calculate indicators
                    df_with_indicators = calculate_technical_indicators(
                        retrieved_data["price_data"], indicators=indicators_to_calc
                    )

                    # Convert DataFrame to dict for storage
                    analysis_results["technical_indicators"] = {
                        "columns": list(df_with_indicators.columns),
                        "data_points": len(df_with_indicators),
                        "latest_values": df_with_indicators.iloc[-1].to_dict()
                        if len(df_with_indicators) > 0
                        else {},
                        "summary": {
                            col: {
                                "mean": float(df_with_indicators[col].mean()),
                                "std": float(df_with_indicators[col].std()),
                            }
                            for col in df_with_indicators.select_dtypes(
                                include=["number"]
                            ).columns
                        },
                    }

            # Analyze sentiment trends if sentiment data available
            if "sentiment_data" in retrieved_data and retrieved_data["sentiment_data"]:
                time_window = analysis_params.get("sentiment_window", "24h")

                if "sentiment" in user_goal.lower() or analysis_params.get(
                    "include_sentiment", True
                ):
                    analysis_results["sentiment_analysis"] = analyze_sentiment_trends(
                        retrieved_data["sentiment_data"], time_window=time_window
                    )

            # Analyze on-chain signals if on-chain data available
            if (
                "on_chain_metrics" in retrieved_data
                and retrieved_data["on_chain_metrics"]
            ):
                lookback = analysis_params.get("onchain_lookback", 30)

                if (
                    "on-chain" in user_goal.lower()
                    or "onchain" in user_goal.lower()
                    or analysis_params.get("include_onchain", True)
                ):
                    analysis_results["on_chain_signals"] = analyze_on_chain_signals(
                        retrieved_data["on_chain_metrics"], lookback_period=lookback
                    )

            # Detect catalyst impact if both catalyst and price data available
            if (
                "catalyst_events" in retrieved_data
                and retrieved_data["catalyst_events"]
                and "price_data" in retrieved_data
                and retrieved_data["price_data"]
            ):
                if (
                    "catalyst" in user_goal.lower()
                    or "event" in user_goal.lower()
                    or analysis_params.get("include_catalyst_impact", True)
                ):
                    analysis_results["catalyst_impact"] = detect_catalyst_impact(
                        retrieved_data["catalyst_events"], retrieved_data["price_data"]
                    )

            # Generate insights summary
            insights = self._generate_insights(analysis_results, user_goal)

            # Update state
            state["analysis_completed"] = True
            state["analysis_results"] = analysis_results
            state["insights"] = insights
            state["message"] = "Data analysis completed successfully"

        except Exception as e:
            state["error"] = f"Data analysis failed: {str(e)}"
            state["analysis_completed"] = False

        return state

    def _generate_insights(
        self, analysis_results: dict[str, Any], user_goal: str
    ) -> list[str]:
        """
        Generate actionable insights from analysis results.

        Args:
            analysis_results: Dictionary of analysis results
            user_goal: User's goal for analysis

        Returns:
            List of insight strings
        """
        insights = []

        # Technical indicator insights
        if "technical_indicators" in analysis_results:
            ti = analysis_results["technical_indicators"]
            latest = ti.get("latest_values", {})

            if "rsi" in latest:
                rsi_value = latest["rsi"]
                if rsi_value > 70:
                    insights.append(
                        f"RSI is overbought at {rsi_value:.2f}, potential sell signal"
                    )
                elif rsi_value < 30:
                    insights.append(
                        f"RSI is oversold at {rsi_value:.2f}, potential buy signal"
                    )

        # Sentiment insights
        if "sentiment_analysis" in analysis_results:
            sa = analysis_results["sentiment_analysis"]
            overall = sa.get("overall_sentiment", {})
            trend = overall.get("trend", "neutral")

            if trend == "bullish":
                insights.append("Overall sentiment is bullish, positive market outlook")
            elif trend == "bearish":
                insights.append("Overall sentiment is bearish, cautious market outlook")

        # On-chain insights
        if "on_chain_signals" in analysis_results:
            ocs = analysis_results["on_chain_signals"]
            metrics = ocs.get("metrics", {})

            # Look for significant trends
            for metric_name, metric_data in metrics.items():
                if abs(metric_data.get("change_percent", 0)) > 20:
                    trend = metric_data.get("trend", "stable")
                    change = metric_data.get("change_percent", 0)
                    insights.append(f"{metric_name} is {trend} by {abs(change):.1f}%")

        # Catalyst impact insights
        if "catalyst_impact" in analysis_results:
            ci = analysis_results["catalyst_impact"]
            events_analyzed = ci.get("events_analyzed", 0)
            avg_impact = ci.get("avg_impact", 0)

            if events_analyzed > 0:
                if abs(avg_impact) > 5:
                    direction = "positive" if avg_impact > 0 else "negative"
                    insights.append(
                        f"Recent catalyst events had {direction} impact (avg {avg_impact:.2f}% price change)"
                    )

        if not insights:
            insights.append(
                "Analysis completed. No significant patterns detected in current timeframe."
            )

        return insights
