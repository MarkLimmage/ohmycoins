# mypy: ignore-errors
"""
Anomaly Detection Tools — Sprint 2.36

Tools for detecting price anomalies using Isolation Forest.
"""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_price_anomalies(
    price_data: list[dict[str, Any]],
    contamination: float = 0.05
) -> dict[str, Any]:
    """
    Detect anomalies in CoinPrice time series using Isolation Forest.

    Args:
        price_data: List of price records with 'timestamp', 'coin', 'price' keys
        contamination: Expected proportion of anomalies (default 5%)

    Returns:
        Dict with anomaly results, severity distribution, and summary
    """
    if not price_data:
        return {
            "model": "IsolationForest",
            "contamination": contamination,
            "coins_analyzed": [],
            "total_anomalies": 0,
            "anomalies": [],
            "severity_distribution": {},
            "summary": "No price data provided for anomaly detection."
        }

    # Convert to DataFrame
    df = pd.DataFrame(price_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Handle different price data formats
    # Support both 'price' and 'last' (from PriceData5Min)
    if "price" not in df.columns and "last" in df.columns:
        df["price"] = df["last"]

    # Handle both 'coin' and 'coin_type' formats
    if "coin" not in df.columns and "coin_type" in df.columns:
        df["coin"] = df["coin_type"]

    # Group by coin and detect anomalies per coin
    coins_analyzed = df["coin"].unique().tolist()
    all_anomalies = []
    severity_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for coin in coins_analyzed:
        coin_data = df[df["coin"] == coin].copy()

        if len(coin_data) < 5:
            # Not enough data for meaningful anomaly detection
            continue

        # Feature engineering: price, price change %, volume (if available)
        features = []
        feature_names = []

        # Always include price
        features.append(coin_data["price"].values)
        feature_names.append("price")

        # Price change percentage
        price_change_pct = coin_data["price"].pct_change().fillna(0).values
        features.append(price_change_pct)
        feature_names.append("price_change_pct")

        # Volume if available
        if "volume" in coin_data.columns and coin_data["volume"].notna().any():
            features.append(coin_data["volume"].fillna(0).values)
            feature_names.append("volume")

        # Prepare feature matrix
        X = np.column_stack(features)

        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=min(contamination, 0.5),
            random_state=42
        )
        predictions = iso_forest.fit_predict(X)
        scores = iso_forest.score_samples(X)

        # Identify anomalies
        for idx, (is_anomaly, score) in enumerate(zip(predictions, scores)):
            if is_anomaly == -1:  # -1 indicates anomaly
                # Determine severity based on score threshold
                if score < -0.9:
                    severity = "HIGH"
                elif score < -0.7:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

                severity_distribution[severity] += 1

                all_anomalies.append({
                    "timestamp": coin_data.iloc[idx]["timestamp"].isoformat(),
                    "coin": coin,
                    "price": float(coin_data.iloc[idx]["price"]),
                    "anomaly_score": float(score),
                    "is_anomaly": True,
                    "severity": severity,
                })

    # Generate summary
    total_anomalies = len(all_anomalies)
    if total_anomalies > 0:
        high_count = severity_distribution.get("HIGH", 0)
        summary = f"{total_anomalies} anomalies detected across {len(coins_analyzed)} coins. {high_count} HIGH severity events require attention."
    else:
        summary = f"No anomalies detected in {len(coins_analyzed)} coins analyzed."

    return {
        "model": "IsolationForest",
        "contamination": contamination,
        "coins_analyzed": coins_analyzed,
        "total_anomalies": total_anomalies,
        "anomalies": all_anomalies,
        "severity_distribution": severity_distribution,
        "summary": summary,
    }
