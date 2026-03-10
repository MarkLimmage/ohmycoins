# mypy: ignore-errors
"""Backtesting engine for historical strategy simulation."""

import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlmodel import Session, select

from app.models import Algorithm, BacktestRun, PriceData5Min
from app.services.trading.metrics import calculate_backtest_metrics

logger = logging.getLogger(__name__)


def generate_features(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate features from price history for ML model predictions.

    Adds: SMA_10, SMA_50, RSI_14, returns_1d, returns_5d, volatility_20d, volume_ma_10
    """
    df = prices_df.copy()

    # Use 'last' price as the main price column
    price = df["last"]

    # Moving averages
    df["SMA_10"] = price.rolling(window=10, min_periods=1).mean()
    df["SMA_50"] = price.rolling(window=50, min_periods=1).mean()

    # Returns
    df["returns_1d"] = price.pct_change(periods=1).fillna(0)
    df["returns_5d"] = price.pct_change(periods=5).fillna(0)

    # Volatility (20-period rolling std of returns)
    df["volatility_20d"] = df["returns_1d"].rolling(window=20, min_periods=1).std().fillna(0)

    # RSI 14
    delta = price.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss.replace(0, float("inf"))
    df["RSI_14"] = 100 - (100 / (1 + rs))
    df["RSI_14"] = df["RSI_14"].fillna(50)

    # Volume MA (use bid-ask spread as volume proxy since PriceData5Min has no volume)
    df["spread"] = df["ask"] - df["bid"]
    df["volume_ma_10"] = df["spread"].rolling(window=10, min_periods=1).mean()

    return df


class BacktestEngine:
    """Engine for running historical backtests on algorithms."""

    def __init__(self, session: Session):
        self.session = session

    def run(
        self,
        algorithm_id: uuid.UUID,
        coin_type: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: Decimal,
        user_id: uuid.UUID,
    ) -> BacktestRun:
        """Run a backtest and return the persisted BacktestRun."""
        # Create the run record
        backtest_run = BacktestRun(
            user_id=user_id,
            algorithm_id=algorithm_id,
            coin_type=coin_type,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            status="running",
        )
        self.session.add(backtest_run)
        self.session.commit()
        self.session.refresh(backtest_run)

        try:
            # Load algorithm
            algorithm = self.session.get(Algorithm, algorithm_id)
            if not algorithm:
                raise ValueError(f"Algorithm {algorithm_id} not found")

            # Query price data
            statement = (
                select(PriceData5Min)
                .where(PriceData5Min.coin_type == coin_type)
                .where(PriceData5Min.timestamp >= start_date)
                .where(PriceData5Min.timestamp <= end_date)
                .order_by(PriceData5Min.timestamp)
            )
            prices = self.session.exec(statement).all()

            if not prices:
                raise ValueError(f"No price data found for {coin_type} between {start_date} and {end_date}")

            # Convert to DataFrame
            prices_df = pd.DataFrame(
                [
                    {
                        "timestamp": p.timestamp,
                        "bid": float(p.bid),
                        "ask": float(p.ask),
                        "last": float(p.last),
                    }
                    for p in prices
                ]
            )
            prices_df = prices_df.sort_values("timestamp").reset_index(drop=True)

            # Determine strategy type and run simulation
            if algorithm.algorithm_type == "ml_model" and algorithm.artifact_id:
                trades, equity_curve = self._run_ml_backtest(
                    algorithm, prices_df, float(initial_capital)
                )
            else:
                trades, equity_curve = self._run_rule_based_backtest(
                    algorithm, prices_df, float(initial_capital)
                )

            # Calculate metrics
            equity_values = [e["equity"] for e in equity_curve]
            metrics = calculate_backtest_metrics(equity_values, trades)

            # Update run
            backtest_run.status = "completed"
            backtest_run.results_json = json.dumps(metrics)
            backtest_run.equity_curve_json = json.dumps(equity_curve)
            backtest_run.trade_log_json = json.dumps(trades)
            backtest_run.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            backtest_run.status = "failed"
            backtest_run.error_message = str(e)
            backtest_run.completed_at = datetime.now(timezone.utc)

        self.session.add(backtest_run)
        self.session.commit()
        self.session.refresh(backtest_run)
        return backtest_run

    def _run_ml_backtest(
        self,
        algorithm: Algorithm,
        prices_df: pd.DataFrame,
        initial_capital: float,
    ) -> tuple[list[dict], list[dict]]:
        """Run backtest using ML model predictions."""
        from app.services.agent.playground import ModelPlaygroundService

        # Load model
        playground = ModelPlaygroundService()
        model, scaler, metadata = playground.load_model(algorithm.artifact_id, self.session)

        # Generate features
        features_df = generate_features(prices_df)
        feature_columns = metadata.get("feature_columns", [])

        # If no feature columns in metadata, use default generated features
        if not feature_columns:
            feature_columns = [
                "SMA_10", "SMA_50", "RSI_14", "returns_1d",
                "returns_5d", "volatility_20d", "volume_ma_10",
            ]

        # Simulate
        cash = initial_capital
        holdings = 0.0
        trades: list[dict[str, Any]] = []
        equity_curve: list[dict[str, Any]] = []

        # Need enough data for feature generation
        start_idx = 50  # Skip first 50 rows for feature warmup

        for i in range(start_idx, len(features_df)):
            row = features_df.iloc[i]
            price = row["last"]
            timestamp = str(row["timestamp"])

            # Build feature dict for prediction
            feature_values = {col: float(row.get(col, 0.0)) for col in feature_columns if col in row.index}

            # Get prediction
            try:
                df_pred = pd.DataFrame([feature_values])
                if scaler is not None:
                    df_pred = pd.DataFrame(scaler.transform(df_pred), columns=list(feature_values.keys()))
                prediction = model.predict(df_pred)[0]
            except Exception:
                prediction = 0  # Hold

            # Simple signal interpretation: 1=buy, 0=hold/sell
            signal = int(prediction) if isinstance(prediction, int | float) else 0

            if signal == 1 and cash > price and holdings == 0:
                # Buy
                qty = cash / price
                holdings = qty
                cash = 0.0
                trades.append({
                    "timestamp": timestamp,
                    "action": "buy",
                    "price": price,
                    "quantity": qty,
                    "pnl": 0.0,
                })
            elif signal == 0 and holdings > 0:
                # Sell
                revenue = holdings * price
                cost_basis = trades[-1]["price"] * holdings if trades else 0
                pnl = revenue - cost_basis
                trades.append({
                    "timestamp": timestamp,
                    "action": "sell",
                    "price": price,
                    "quantity": holdings,
                    "pnl": pnl,
                })
                cash = revenue
                holdings = 0.0

            equity = cash + holdings * price
            equity_curve.append({"timestamp": timestamp, "equity": equity})

        return trades, equity_curve

    def _run_rule_based_backtest(
        self,
        algorithm: Algorithm,
        prices_df: pd.DataFrame,
        initial_capital: float,
    ) -> tuple[list[dict], list[dict]]:
        """Run backtest using simple MA crossover strategy."""
        # Parse configuration
        config = {}
        if algorithm.configuration_json:
            config = json.loads(algorithm.configuration_json)

        short_window = config.get("short_window", 10)
        long_window = config.get("long_window", 50)

        # Calculate moving averages
        prices_df["sma_short"] = prices_df["last"].rolling(window=short_window, min_periods=1).mean()
        prices_df["sma_long"] = prices_df["last"].rolling(window=long_window, min_periods=1).mean()

        cash = initial_capital
        holdings = 0.0
        trades: list[dict[str, Any]] = []
        equity_curve: list[dict[str, Any]] = []

        for i in range(long_window, len(prices_df)):
            row = prices_df.iloc[i]
            prev_row = prices_df.iloc[i - 1]
            price = row["last"]
            timestamp = str(row["timestamp"])

            # Crossover signals
            if (
                prev_row["sma_short"] <= prev_row["sma_long"]
                and row["sma_short"] > row["sma_long"]
                and holdings == 0
                and cash > price
            ):
                # Golden cross — buy
                qty = cash / price
                holdings = qty
                cash = 0.0
                trades.append({
                    "timestamp": timestamp,
                    "action": "buy",
                    "price": price,
                    "quantity": qty,
                    "pnl": 0.0,
                })
            elif (
                prev_row["sma_short"] >= prev_row["sma_long"]
                and row["sma_short"] < row["sma_long"]
                and holdings > 0
            ):
                # Death cross — sell
                revenue = holdings * price
                cost_basis = trades[-1]["price"] * holdings if trades else 0
                pnl = revenue - cost_basis
                trades.append({
                    "timestamp": timestamp,
                    "action": "sell",
                    "price": price,
                    "quantity": holdings,
                    "pnl": pnl,
                })
                cash = revenue
                holdings = 0.0

            equity = cash + holdings * price
            equity_curve.append({"timestamp": timestamp, "equity": equity})

        return trades, equity_curve
