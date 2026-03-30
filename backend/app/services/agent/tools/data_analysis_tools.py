# mypy: ignore-errors
"""
Data Analysis Tools - Week 3-4 Implementation

Tools for DataAnalystAgent to analyze cryptocurrency data and generate insights.
"""

from typing import Any

import numpy as np
import pandas as pd
from ta import add_all_ta_features


def calculate_technical_indicators(
    price_data: list[dict[str, Any]],
    indicators: list[str] | None = None,
) -> pd.DataFrame:
    """
    Calculate technical indicators for price data.

    Args:
        price_data: List of price data dictionaries with timestamp, bid, ask, last
        indicators: Optional list of specific indicators to calculate
                   If None, calculates common indicators (SMA, EMA, RSI, MACD, BB)

    Returns:
        DataFrame with price data and calculated indicators
    """
    # Convert to DataFrame
    df = pd.DataFrame(price_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Rename columns to match ta library conventions
    df["close"] = df["last"]
    df["high"] = df["ask"]
    df["low"] = df["bid"]
    df["volume"] = 0  # Volume not available, use 0 as placeholder

    # Fill any NaN values with 0 instead of dropping rows
    # This preserves all data points while ensuring no NaN in calculations
    df = df.fillna(0)

    if len(df) < 20:
        # Not enough data for meaningful indicators
        return df

    if indicators is None or "all" in indicators:
        # Add all technical indicators
        df = add_all_ta_features(
            df,
            open="close",
            high="high",
            low="low",
            close="close",
            volume="volume",
            fillna=True,
        )
    else:
        # Add specific indicators (simplified implementation)
        # Common indicators
        if "sma_20" in indicators:
            df["sma_20"] = df["close"].rolling(window=20).mean()

        if "ema_20" in indicators:
            df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()

        if "rsi" in indicators:
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

    return df


def analyze_sentiment_trends(
    sentiment_data: dict[str, Any],
    time_window: str = "24h",
) -> dict[str, Any]:
    """
    Analyze sentiment trends from news and social media.

    Args:
        sentiment_data: Dictionary with news_sentiment and social_sentiment lists
        time_window: Time window for trend analysis (e.g., '24h', '7d', '30d')

    Returns:
        Dictionary with sentiment analysis results
    """
    news = sentiment_data.get("news_sentiment", [])
    social = sentiment_data.get("social_sentiment", [])

    # Convert time window to hours
    {
        "24h": 24,
        "7d": 168,
        "30d": 720,
    }.get(time_window, 24)

    # Aggregate sentiment scores
    news_sentiments = [
        n["sentiment_score"] for n in news if n["sentiment_score"] is not None
    ]
    social_sentiments = []

    # Map social sentiment to numeric scores
    sentiment_map = {
        "positive": 1.0,
        "neutral": 0.0,
        "negative": -1.0,
    }
    for s in social:
        if s["sentiment"] in sentiment_map:
            social_sentiments.append(sentiment_map[s["sentiment"]])

    results = {
        "time_window": time_window,
        "news_sentiment": {
            "count": len(news),
            "avg_score": np.mean(news_sentiments) if news_sentiments else 0.0,
            "std_score": np.std(news_sentiments) if len(news_sentiments) > 1 else 0.0,
            "positive_ratio": len([s for s in news_sentiments if s > 0])
            / len(news_sentiments)
            if news_sentiments
            else 0.0,
        },
        "social_sentiment": {
            "count": len(social),
            "avg_score": np.mean(social_sentiments) if social_sentiments else 0.0,
            "std_score": np.std(social_sentiments)
            if len(social_sentiments) > 1
            else 0.0,
            "positive_ratio": len([s for s in social_sentiments if s > 0])
            / len(social_sentiments)
            if social_sentiments
            else 0.0,
        },
        "overall_sentiment": {
            "all_scores": news_sentiments + social_sentiments,
            "avg_score": np.mean(news_sentiments + social_sentiments)
            if (news_sentiments or social_sentiments)
            else 0.0,
            "trend": "bullish"
            if np.mean(news_sentiments + social_sentiments) > 0.2
            else "bearish"
            if np.mean(news_sentiments + social_sentiments) < -0.2
            else "neutral",
        },
    }

    return results


def analyze_on_chain_signals(
    on_chain_data: list[dict[str, Any]],
    lookback_period: int = 30,
) -> dict[str, Any]:
    """
    Analyze on-chain metrics for trading signals.

    Args:
        on_chain_data: List of on-chain metric dictionaries
        lookback_period: Number of days to look back for trend analysis

    Returns:
        Dictionary with on-chain analysis results
    """
    if not on_chain_data:
        return {
            "status": "no_data",
            "message": "No on-chain data available",
        }

    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(on_chain_data)
    df["collected_at"] = pd.to_datetime(df["collected_at"])
    df = df.sort_values("collected_at")

    # Group by metric name
    metrics_analysis = {}
    for metric_name in df["metric_name"].unique():
        metric_df = df[df["metric_name"] == metric_name].copy()

        if len(metric_df) < 2:
            continue

        # Calculate trend
        values = metric_df["metric_value"].values
        trend = "increasing" if values[-1] > values[0] else "decreasing"

        metrics_analysis[metric_name] = {
            "latest_value": float(values[-1]),
            "first_value": float(values[0]),
            "trend": trend,
            "change_percent": ((values[-1] - values[0]) / values[0] * 100)
            if values[0] != 0
            else 0,
            "avg_value": float(np.mean(values)),
        }

    return {
        "lookback_period_days": lookback_period,
        "metrics": metrics_analysis,
        "data_points": len(on_chain_data),
    }


def detect_catalyst_impact(
    catalyst_events: list[dict[str, Any]],
    price_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Detect impact of catalyst events on price movements.

    Args:
        catalyst_events: List of catalyst event dictionaries
        price_data: List of price data dictionaries

    Returns:
        Dictionary with catalyst impact analysis
    """
    if not catalyst_events or not price_data:
        return {
            "status": "insufficient_data",
            "events_analyzed": 0,
        }

    # Convert to DataFrames
    events_df = pd.DataFrame(catalyst_events)
    events_df["detected_at"] = pd.to_datetime(events_df["detected_at"])

    price_df = pd.DataFrame(price_data)
    price_df["timestamp"] = pd.to_datetime(price_df["timestamp"])
    price_df = price_df.sort_values("timestamp")

    impact_analysis = []

    for _, event in events_df.iterrows():
        event_time = event["detected_at"]

        # Get price before event (1 hour window)
        before_prices = price_df[
            (price_df["timestamp"] >= event_time - pd.Timedelta(hours=1))
            & (price_df["timestamp"] < event_time)
        ]

        # Get price after event (1 hour window)
        after_prices = price_df[
            (price_df["timestamp"] >= event_time)
            & (price_df["timestamp"] <= event_time + pd.Timedelta(hours=1))
        ]

        if len(before_prices) > 0 and len(after_prices) > 0:
            before_avg = before_prices["last"].mean()
            after_avg = after_prices["last"].mean()
            price_change = (
                ((after_avg - before_avg) / before_avg * 100) if before_avg != 0 else 0
            )

            impact_analysis.append(
                {
                    "event_type": event["event_type"],
                    "title": event["title"],
                    "impact_score": event["impact_score"],
                    "price_change_percent": float(price_change),
                    "detected_at": event["detected_at"].isoformat(),
                }
            )

    return {
        "events_analyzed": len(impact_analysis),
        "impacts": impact_analysis,
        "avg_impact": np.mean([i["price_change_percent"] for i in impact_analysis])
        if impact_analysis
        else 0,
    }


def clean_data(
    data: pd.DataFrame | list[dict[str, Any]],
    remove_outliers: bool = True,
    fill_missing: bool = True,
) -> pd.DataFrame:
    """
    Clean and preprocess data for analysis.

    Args:
        data: DataFrame or list of dictionaries to clean
        remove_outliers: Whether to remove outliers using IQR method
        fill_missing: Whether to fill missing values

    Returns:
        Cleaned DataFrame
    """
    # Convert to DataFrame if needed
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    if len(df) == 0:
        return df

    # Fill missing values
    if fill_missing:
        # Forward fill then backward fill
        df = df.fillna(method="ffill").fillna(method="bfill")

    # Remove outliers using IQR method
    if remove_outliers:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

    return df


def perform_eda(
    data: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Perform exploratory data analysis on a dataset.

    Args:
        data: DataFrame or list of dictionaries to analyze

    Returns:
        Dictionary with EDA results including summary statistics and insights
    """
    # Convert to DataFrame if needed
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    if len(df) == 0:
        return {
            "status": "no_data",
            "message": "No data available for EDA",
        }

    # Basic statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    eda_results = {
        "shape": {
            "rows": len(df),
            "columns": len(df.columns),
        },
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_statistics": {},
    }

    # Summary statistics for numeric columns
    for col in numeric_cols:
        eda_results["summary_statistics"][col] = {
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "std": float(df[col].std()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "q25": float(df[col].quantile(0.25)),
            "q75": float(df[col].quantile(0.75)),
        }

    # Flat basic_stats — prioritise 'close' / 'last' for the headline summary
    close_col = (
        "close" if "close" in df.columns else ("last" if "last" in df.columns else None)
    )
    basic: dict[str, Any] = {
        "rows": len(df),
        "columns": len(df.columns),
    }
    # Date range
    for tc in ("timestamp", "date"):
        if tc in df.columns:
            ts = pd.to_datetime(df[tc], errors="coerce").dropna()
            if len(ts) > 0:
                basic["date_start"] = str(ts.min())[:19]
                basic["date_end"] = str(ts.max())[:19]
            break

    if close_col and close_col in numeric_cols:
        s = eda_results["summary_statistics"][close_col]
        basic["close_mean"] = s["mean"]
        basic["close_std"] = s["std"]
        basic["close_min"] = s["min"]
        basic["close_max"] = s["max"]
        basic["close_median"] = s["median"]

    eda_results["basic_stats"] = basic

    return eda_results


def perform_correlation_analysis(
    price_df: pd.DataFrame,
    sentiment_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Compute correlation between price metrics and other data series.

    Args:
        price_df: DataFrame with price data (must have 'close' or 'last' column).
        sentiment_data: Optional dict with 'news_sentiment' / 'social_sentiment' lists.

    Returns:
        Dictionary with correlation results.
    """
    results: dict[str, Any] = {"correlations": [], "method": "pearson"}

    if len(price_df) < 5:
        results["note"] = "Insufficient data for meaningful correlation"
        return results

    # Ensure 'close' column exists
    if "close" not in price_df.columns and "last" in price_df.columns:
        price_df = price_df.copy()
        price_df["close"] = price_df["last"]

    # --- Price self-correlation matrix ---
    numeric_cols = price_df.select_dtypes(include="number").columns.tolist()
    # Limit to first 20 columns to avoid huge matrices
    numeric_cols = numeric_cols[:20]

    if len(numeric_cols) >= 2:
        corr_matrix = price_df[numeric_cols].corr(method="pearson")
        results["price_correlation_matrix"] = {
            col: {k: round(v, 4) for k, v in row.items()}
            for col, row in corr_matrix.to_dict().items()
        }

        # Extract top 10 strongest off-diagonal correlations
        top_pairs: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for i, c1 in enumerate(numeric_cols):
            for c2 in numeric_cols[i + 1 :]:
                if (c1, c2) not in seen:
                    seen.add((c1, c2))
                    val = corr_matrix.loc[c1, c2]
                    if not np.isnan(val):
                        top_pairs.append(
                            {"pair": f"{c1} vs {c2}", "r": round(float(val), 4)}
                        )
        top_pairs.sort(key=lambda x: abs(x["r"]), reverse=True)
        results["top_correlations"] = top_pairs[:10]

    # --- Price vs sentiment correlation ---
    if sentiment_data:
        sentiment_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        # Build daily sentiment scores
        news = sentiment_data.get("news_sentiment", [])
        social = sentiment_data.get("social_sentiment", [])

        sentiment_scores: list[dict[str, Any]] = []
        for item in news:
            if item.get("sentiment_score") is not None and item.get("published_at"):
                sentiment_scores.append(
                    {
                        "date": str(item["published_at"])[:10],
                        "score": float(item["sentiment_score"]),
                    }
                )
        for item in social:
            if item.get("sentiment") and item.get("collected_at"):
                sentiment_scores.append(
                    {
                        "date": str(item["collected_at"])[:10],
                        "score": sentiment_map.get(item["sentiment"], 0.0),
                    }
                )

        if len(sentiment_scores) >= 5 and "close" in price_df.columns:
            sent_df = pd.DataFrame(sentiment_scores)
            sent_df["date"] = pd.to_datetime(sent_df["date"])
            daily_sent = sent_df.groupby("date")["score"].mean().reset_index()

            # Build daily close prices
            pdf = price_df.copy()
            if "timestamp" in pdf.columns:
                pdf["date"] = pd.to_datetime(pdf["timestamp"]).dt.normalize()
            elif pdf.index.name == "timestamp" or hasattr(pdf.index, "date"):
                pdf["date"] = pd.to_datetime(pdf.index).normalize()
            else:
                daily_sent = pd.DataFrame()  # can't align

            if len(daily_sent) > 0 and "date" in pdf.columns:
                daily_price = pdf.groupby("date")["close"].mean().reset_index()
                merged = pd.merge(daily_price, daily_sent, on="date", how="inner")
                if len(merged) >= 5:
                    r_pearson = float(
                        merged["close"].corr(merged["score"], method="pearson")
                    )
                    r_spearman = float(
                        merged["close"].corr(merged["score"], method="spearman")
                    )
                    results["price_sentiment_correlation"] = {
                        "pearson_r": round(r_pearson, 4)
                        if not np.isnan(r_pearson)
                        else None,
                        "spearman_r": round(r_spearman, 4)
                        if not np.isnan(r_spearman)
                        else None,
                        "data_points": len(merged),
                    }
                else:
                    results["price_sentiment_correlation"] = {
                        "note": f"Only {len(merged)} overlapping days — too few for reliable correlation",
                    }
        elif not sentiment_scores:
            results["price_sentiment_correlation"] = {
                "note": "No sentiment data available for correlation",
            }

    return results
