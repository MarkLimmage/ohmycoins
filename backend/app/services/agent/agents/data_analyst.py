"""
Data Analyst Agent - Analyzes cryptocurrency data and generates insights.

Week 3-4 implementation: New agent for comprehensive data analysis.
"""

from typing import Any

import pandas as pd

from ..tools import (
    analyze_on_chain_signals,
    analyze_sentiment_trends,
    calculate_technical_indicators,
    detect_catalyst_impact,
    detect_price_anomalies,
    perform_correlation_analysis,
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
        # Initialize pending events for this execution step
        state["pending_events"] = []

        try:
            await self.emit_event(
                state,
                "stream_chat",
                "EXPLORATION",
                {"message": "I'm starting the data analysis phase to identify patterns and signals.", "sender": "DataAnalystAgent"},
            )
            await self.emit_event(
                state,
                "status_update",
                "EXPLORATION",
                {
                    "status": "ACTIVE",
                    "message": "Initializing analysis pipeline...",
                    "task_id": "compute_technical_indicators"
                },
            )

            # Get retrieved data from previous agent
            retrieved_data = state.get("retrieved_data", {})

            if not retrieved_data:
                state["error"] = "No data available for analysis"
                state["analysis_completed"] = False
                await self.emit_event(
                    state, "error", "EXPLORATION", {"error": "No data available"}
                )
                return state

            user_goal = state.get("user_goal", "")
            analysis_params = state.get("analysis_params", {})

            # Initialize analysis results
            analysis_results: dict[str, Any] = {}

            # Perform EDA on available data
            if "eda" in user_goal.lower() or analysis_params.get("include_eda", True):
                analysis_results["exploratory_analysis"] = {}

                if "price_data" in retrieved_data and retrieved_data["price_data"]:
                    await self.emit_event(
                        state,
                        "stream_chat",
                        "EXPLORATION",
                        {"message": "Performing seasonal decomposition and trend analysis...", "sender": "DataAnalystAgent"},
                    )
                    await self.emit_event(
                        state,
                        "status_update",
                        "EXPLORATION",
                        {"status": "ACTIVE", "message": "Running EDA on price metrics...", "task_id": "perform_eda"},
                    )
                    analysis_results["exploratory_analysis"]["price_eda"] = perform_eda(
                        retrieved_data["price_data"]
                    )
                    await self.emit_event(
                        state,
                        "status_update",
                        "EXPLORATION",
                        {"status": "DONE", "message": "EDA complete", "task_id": "perform_eda"},
                    )

            # Calculate technical indicators if price data available
            if "price_data" in retrieved_data and retrieved_data["price_data"]:
                indicators_to_calc = analysis_params.get("indicators", None)

                if (
                    "indicator" in user_goal.lower()
                    or "technical" in user_goal.lower()
                    or analysis_params.get("include_indicators", True)
                ):
                    await self.emit_event(
                        state,
                        "status_update",
                        "EXPLORATION",
                        {"status": "ACTIVE", "message": "Computing technical indicators...", "task_id": "compute_indicators"},
                    )
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
                    await self.emit_event(
                        state,
                        "status_update",
                        "EXPLORATION",
                        {"status": "DONE", "message": f"Indicators: {len(df_with_indicators.columns)} columns, {len(df_with_indicators)} points", "task_id": "compute_indicators"},
                    )

            # Analyze sentiment trends if sentiment data available
            sentiment_data_raw = retrieved_data.get("sentiment_data", {})
            has_sentiment = (
                len(sentiment_data_raw.get("news_sentiment", [])) > 0
                or len(sentiment_data_raw.get("social_sentiment", [])) > 0
            ) if isinstance(sentiment_data_raw, dict) else bool(sentiment_data_raw)
            if has_sentiment:
                time_window = analysis_params.get("sentiment_window", "24h")

                if "sentiment" in user_goal.lower() or analysis_params.get(
                    "include_sentiment", True
                ):
                    await self.emit_event(
                        state,
                        "status_update",
                        "EXPLORATION",
                        {"status": "ACTIVE", "message": "Analysing sentiment trends...", "task_id": "analyse_sentiment"},
                    )
                    analysis_results["sentiment_analysis"] = analyze_sentiment_trends(
                        sentiment_data_raw, time_window=time_window
                    )
                    await self.emit_event(
                        state,
                        "status_update",
                        "EXPLORATION",
                        {"status": "DONE", "message": "Sentiment analysis complete", "task_id": "analyse_sentiment"},
                    )
            else:
                # No actual sentiment data — record unavailability if goal expected it
                scope = state.get("scope_interpretation", {})
                analysis_type = scope.get("analysis_type", "")
                if "sentiment" in user_goal.lower() or "sentiment" in analysis_type.lower():
                    analysis_results["sentiment_analysis"] = {
                        "overall_sentiment": {"trend": "unavailable", "avg_score": None},
                        "news_sentiment": {"count": 0, "avg_score": 0.0},
                        "social_sentiment": {"count": 0, "avg_score": 0.0},
                        "note": "No sentiment data available for analysis",
                    }

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

            # Sprint 2.36: Anomaly Detection
            if "price_data" in retrieved_data and retrieved_data["price_data"]:
                if "anomaly" in user_goal.lower() or analysis_params.get(
                    "include_anomaly_detection", True
                ):
                    anomaly_result = detect_price_anomalies(
                        retrieved_data["price_data"],
                        contamination=analysis_params.get(
                            "anomaly_contamination", 0.05
                        ),
                    )
                    analysis_results["anomaly_detection"] = anomaly_result
                    state["anomaly_detected"] = (
                        anomaly_result.get("total_anomalies", 0) > 0
                    )
                    state["anomaly_summary"] = anomaly_result.get("summary", "")

            # Correlation analysis — run when analysis_type mentions "correlation"
            scope = state.get("scope_interpretation", {})
            analysis_type = scope.get("analysis_type", "")
            if (
                "correlation" in analysis_type.lower()
                or "correlation" in user_goal.lower()
            ):
                await self.emit_event(
                    state,
                    "status_update",
                    "EXPLORATION",
                    {"status": "ACTIVE", "message": "Computing correlations...", "task_id": "compute_correlations"},
                )
                # Build price DataFrame for correlation
                price_data_list = retrieved_data.get("price_data", [])
                corr_price_df = pd.DataFrame(price_data_list) if price_data_list else pd.DataFrame()
                if not corr_price_df.empty and "last" in corr_price_df.columns:
                    corr_price_df["close"] = corr_price_df["last"]

                corr_sentiment = sentiment_data_raw if has_sentiment else None
                correlation_results = perform_correlation_analysis(
                    corr_price_df, sentiment_data=corr_sentiment
                )
                analysis_results["correlation_analysis"] = correlation_results
                await self.emit_event(
                    state,
                    "status_update",
                    "EXPLORATION",
                    {"status": "DONE", "message": "Correlation analysis complete", "task_id": "compute_correlations"},
                )

            # Generate insights summary
            insights = self._generate_insights(analysis_results, user_goal)

            # Update state
            state["analysis_completed"] = True
            state["analysis_results"] = analysis_results
            state["insights"] = insights
            state["message"] = "Data analysis completed successfully"

            # Emit findings to user
            if insights:
                findings_text = "\n".join(f"- {i}" for i in insights)
                await self.emit_event(
                    state,
                    "stream_chat",
                    "EXPLORATION",
                    {
                        "message": f"Analysis complete. Key findings:\n{findings_text}",
                        "sender": "DataAnalystAgent",
                    },
                )

            # --- Emit exploration render_output with analysis summary ---
            out_lines = ["## Exploration Results\n"]

            # Technical indicators
            if "technical_indicators" in analysis_results:
                ti = analysis_results["technical_indicators"]
                out_lines.append(f"### Technical Indicators")
                out_lines.append(f"- **Data points**: {ti.get('data_points', 0):,}")
                out_lines.append(f"- **Indicators calculated**: {len(ti.get('columns', []))}")
                latest = ti.get("latest_values", {})
                if latest:
                    selected = {k: v for k, v in latest.items() if k in ("rsi", "macd", "bb_upper", "bb_lower", "sma_20", "ema_12")}
                    if selected:
                        out_lines.append("| Indicator | Latest Value |")
                        out_lines.append("|-----------|-------------|")
                        for k, v in selected.items():
                            out_lines.append(f"| {k.upper()} | {v:.4f} |" if isinstance(v, float) else f"| {k.upper()} | {v} |")
                out_lines.append("")

            # EDA
            if "exploratory_analysis" in analysis_results:
                eda = analysis_results["exploratory_analysis"]
                price_eda = eda.get("price_eda", {})
                if price_eda:
                    out_lines.append("### Exploratory Data Analysis")
                    stats = price_eda.get("basic_stats", {})
                    if not stats:
                        # Fallback: flatten summary_statistics for 'close' or first column
                        summary = price_eda.get("summary_statistics", {})
                        shape = price_eda.get("shape", {})
                        stats = {}
                        if shape:
                            stats["rows"] = shape.get("rows", "N/A")
                            stats["columns"] = shape.get("columns", "N/A")
                        for col_key in ("close", "last"):
                            if col_key in summary:
                                for metric, val in summary[col_key].items():
                                    stats[f"{col_key}_{metric}"] = val
                                break
                    if stats:
                        out_lines.append("| Metric | Value |")
                        out_lines.append("|--------|-------|")
                        for k, v in list(stats.items())[:12]:
                            out_lines.append(f"| {k} | {v:.4f} |" if isinstance(v, float) else f"| {k} | {v} |")
                    else:
                        out_lines.append("_No numeric statistics available._")
                    out_lines.append("")

            # Sentiment
            if "sentiment_analysis" in analysis_results:
                sa = analysis_results["sentiment_analysis"]
                overall = sa.get("overall_sentiment", {})
                news = sa.get("news_sentiment", {})
                social = sa.get("social_sentiment", {})
                out_lines.append("### Sentiment Analysis")
                out_lines.append(f"- **Trend**: {overall.get('trend', 'N/A')} (score: {overall.get('avg_score', 0):.3f})")
                out_lines.append(f"- **News articles**: {news.get('count', 0)}")
                out_lines.append(f"- **Social posts**: {social.get('count', 0)}")
                out_lines.append("")

            # Anomaly detection
            if "anomaly_detection" in analysis_results:
                ad = analysis_results["anomaly_detection"]
                out_lines.append("### Anomaly Detection")
                out_lines.append(f"- **Model**: {ad.get('model', 'IsolationForest')}")
                out_lines.append(f"- **Total anomalies**: {ad.get('total_anomalies', 0)}")
                out_lines.append("")

            # On-chain / Catalyst
            if "on_chain_signals" in analysis_results:
                out_lines.append("### On-Chain Signals")
                out_lines.append(f"- Metrics analysed: {len(analysis_results['on_chain_signals'].get('metrics', {}))}")
                out_lines.append("")

            if "catalyst_impact" in analysis_results:
                ci = analysis_results["catalyst_impact"]
                out_lines.append("### Catalyst Impact")
                out_lines.append(f"- Events analysed: {ci.get('events_analyzed', 0)}")
                out_lines.append("")

            # Correlation
            if "correlation_analysis" in analysis_results:
                ca = analysis_results["correlation_analysis"]
                out_lines.append("### Correlation Analysis")
                out_lines.append(f"- **Method**: {ca.get('method', 'pearson')}")
                top = ca.get("top_correlations", [])
                if top:
                    out_lines.append("| Pair | r |")
                    out_lines.append("|------|--:|")
                    for pair in top[:5]:
                        out_lines.append(f"| {pair['pair']} | {pair['r']:.4f} |")
                psc = ca.get("price_sentiment_correlation", {})
                if psc and psc.get("pearson_r") is not None:
                    out_lines.append(f"- **Price–Sentiment Pearson r**: {psc['pearson_r']}")
                    out_lines.append(f"- **Price–Sentiment Spearman r**: {psc.get('spearman_r', 'N/A')}")
                elif psc.get("note"):
                    out_lines.append(f"- {psc['note']}")
                out_lines.append("")

            await self.emit_event(
                state,
                "render_output",
                "EXPLORATION",
                {
                    "mime_type": "text/markdown",
                    "content": "\n".join(out_lines),
                },
            )

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
            news = sa.get("news_sentiment", {})
            social = sa.get("social_sentiment", {})
            trend = overall.get("trend", "neutral")
            avg_score = overall.get("avg_score", 0.0)

            # Always report sentiment statistics when data exists
            news_count = news.get("count", 0)
            social_count = social.get("count", 0)
            total_sources = news_count + social_count
            if total_sources > 0:
                parts = []
                if news_count > 0:
                    parts.append(f"{news_count} news articles (avg score: {news.get('avg_score', 0):.3f}, {news.get('positive_ratio', 0)*100:.0f}% positive)")
                if social_count > 0:
                    parts.append(f"{social_count} social posts (avg score: {social.get('avg_score', 0):.3f})")
                insights.append(f"Sentiment data: {', '.join(parts)}")

            if trend == "bullish":
                insights.append(f"Overall sentiment is bullish (score: {avg_score:.3f}), positive market outlook")
            elif trend == "bearish":
                insights.append(f"Overall sentiment is bearish (score: {avg_score:.3f}), cautious market outlook")
            else:
                insights.append(f"Overall sentiment is neutral (score: {avg_score:.3f}), no strong directional bias")

            # Report score dispersion if available
            std = news.get("std_score", 0.0)
            if std > 0.3 and news_count > 5:
                insights.append(f"High sentiment dispersion (std: {std:.3f}) — mixed signals among sources")

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
