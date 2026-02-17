# mypy: ignore-errors
"""
Backtest Service

This module is responsible for running historical simulations of trading strategies.
It ensures data isolation by using historical data (PriceData5Min) and not interacting
with live trading execution or orders.
"""
import logging
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from sqlmodel import Session, select

from app.models import PriceData5Min
from app.services.backtesting.schemas import BacktestConfig, BacktestResult

logger = logging.getLogger(__name__)


class BacktestService:
    """
    Service for executing backtests on historical data.
    """

    def __init__(self, session: Session):
        self.session = session

    def _fetch_data(self, coin_type: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch historical data from the database and convert to a Pandas DataFrame.
        Resolves 'isolation of data' by strictly querying the historical table.
        """
        statement = select(PriceData5Min).where(
            PriceData5Min.coin_type == coin_type,
            PriceData5Min.timestamp >= start_date,
            PriceData5Min.timestamp <= end_date
        ).order_by(PriceData5Min.timestamp)

        results = self.session.exec(statement).all()

        if not results:
            return pd.DataFrame()

        # Convert to list of dicts for pandas
        data = [
            {
                "timestamp": r.timestamp,
                "open": float(r.last), # Proxying open with last/close if open not available in current model
                "high": float(r.last), # Proxying high
                "low": float(r.last),  # Proxying low
                "close": float(r.last),
                # If PriceData5Min had OHLC, we would use it.
                # Currently it has bid/ask/last based on `PriceDataBase`.
                # Assuming `last` is the close price.
            }
            for r in results
        ]

        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df

    def run_backtest(self, config: BacktestConfig, strategy_fn: Callable[[pd.DataFrame, dict], pd.DataFrame] = None, fee_rate: float = 0.001, slippage: float = 0.0005) -> BacktestResult:
        """
        Run a backtest for a given configuration.

        Args:
            config: BacktestConfiguration object
            strategy_fn: Optional function to calculate signals. If None, uses a default simple strategy.
                         Signature: (df: pd.DataFrame, params: dict) -> pd.DataFrame with 'signal' column.
                         Signal: 1 (buy), -1 (sell), 0 (hold)
            fee_rate: Trading fee as a decimal (e.g. 0.001 for 0.1%)
            slippage: Slippage as a decimal (e.g. 0.0005 for 0.05%)
        """
        logger.info(f"Starting backtest for {config.strategy_name} on {config.coin_type}")

        # 1. Fetch Data
        df = self._fetch_data(config.coin_type, config.start_date, config.end_date)

        if df.empty:
            logger.warning("No data found for backtest")
            return self._empty_result(config)

        # 2. Apply Strategy
        if strategy_fn:
            df = strategy_fn(df, config.parameters)
        else:
            # Default fallback: random or simple strategy if none provided
            # For now, let's implement a simple reusable one or placeholder
             df = self._default_strategy(df, config.parameters)

        # 3. Simulate Execution (Vectorized)
        result = self._calculate_performance(df, config.initial_capital, fee_rate, slippage)

        result.strategy_name = config.strategy_name
        result.coin_type = config.coin_type

        return result

    def _default_strategy(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        A simple default strategy (e.g., Simple Moving Average Crossover) if none provided.
        Params: fast_window, slow_window
        """
        fast_window = params.get("fast_window", 10)
        slow_window = params.get("slow_window", 30)

        df["fast_ma"] = df["close"].rolling(window=fast_window).mean()
        df["slow_ma"] = df["close"].rolling(window=slow_window).mean()

        df["signal"] = 0
        df.loc[df["fast_ma"] > df["slow_ma"], "signal"] = 1 # Long
        # strategies can be long-only or long-short.
        # For simplicity, assuming Long only (1) vs Flat (0).
        # If shorting is allowed, -1.

        # Shift signal by 1 to avoid lookahead bias (signal valid for NEXT candle)
        df["position"] = df["signal"].shift(1)

        return df

    def _calculate_performance(self, df: pd.DataFrame, initial_capital: Decimal, fee_rate: float, slippage: float) -> BacktestResult:
        """
        Calculate performance metrics from strategy signals.
        """
        # Calculate returns
        df["returns"] = df["close"].pct_change()

        # Handle NaN in position (start of series)
        df["position"] = df["position"].fillna(0)

        # Gross Returns
        df["strategy_returns_gross"] = df["position"] * df["returns"]

        # Transaction Costs
        # Cost is incurred when position changes.
        # Cost % = (Fee + Slippage) * |Change in Position|
        # This approximates cost as a drag on returns.
        df["position_change"] = df["position"].diff().fillna(0).abs()
        df["transaction_costs"] = df["position_change"] * (fee_rate + slippage)

        # Net Returns
        df["strategy_returns"] = df["strategy_returns_gross"] - df["transaction_costs"]

        # Cumulative Returns
        # We fill NaN returns with 0 to safely cumprod
        df["strategy_returns"] = df["strategy_returns"].fillna(0)

        df["cumulative_returns"] = (1 + df["strategy_returns"]).cumprod()
        df["equity"] = float(initial_capital) * df["cumulative_returns"]

        # Metrics
        total_return_percent = (df["equity"].iloc[-1] / float(initial_capital)) - 1
        total_return = float(initial_capital) * total_return_percent

        # Max Drawdown
        df["cum_max"] = df["equity"].cummax()
        df["drawdown"] = df["equity"] / df["cum_max"] - 1
        max_drawdown = df["drawdown"].min()

        # Sharpe Ratio (assuming constant risk free rate of 0 for simplicity)
        # Annualized Sharpe (assuming 5min candles -> 288 per day -> 365 days)
        periods_per_year = 288 * 365
        if df["strategy_returns"].std() == 0:
            sharpe_ratio = 0.0
        else:
            sharpe_ratio = (df["strategy_returns"].mean() / df["strategy_returns"].std()) * np.sqrt(periods_per_year)

        # Win Rate
        # A trade is defined by a change in position? Or per period?
        # Usually Win Rate is per Trade.
        # Need to reconstruct trades from position changes.
        trades = self._extract_trades(df, fee_rate, slippage)
        winning_trades = [t for t in trades if t["pnl"] > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0.0

        # Equity Curve for chart
        equity_curve = [
            {"time": str(ts), "value": val}
            for ts, val in df["equity"].items()
            if isinstance(ts, datetime) # Filter generic index
        ]
        # Downsample for UI if needed, but returning full for now

        return BacktestResult(
            strategy_name="Unknown", # To be filled by caller
            coin_type="Unknown",    # To be filled by caller
            total_return=total_return,
            total_return_percent=total_return_percent,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            total_trades=len(trades),
            trades=trades,
            equity_curve=equity_curve[-100:] # Just return last 100 for brevity in result, or full?
                                             # Usually full is needed for charts.
                                             # But large payloads can be an issue.
                                             # I'll return full list but be careful with large ranges.
        )

    def _extract_trades(self, df: pd.DataFrame, fee_rate: float, slippage: float) -> list[dict[str, Any]]:
        """
        Reconstruct discrete trades from position series.
        """
        trades = []
        in_trade = False
        entry_price = 0.0
        entry_time = None
        current_position = 0

        # Cost factor per side (entry or exit)
        cost_per_side = fee_rate + slippage

        for ts, row in df.iterrows():
            pos = row["position"]
            price = row["close"]

            if pos != current_position:
                # Position changed

                # Close existing trade if any
                if in_trade:
                    exit_price = price
                    # Gross PnL
                    gross_pnl = (exit_price - entry_price) / entry_price * (1 if current_position > 0 else -1)
                    # Deduct costs for entry and exit
                    # Note: This is an approximation.
                    # Exact: Entry Cost = EntryVal * cost. Exit Cost = ExitVal * cost.
                    # But since we use pct returns, we sum the pct costs?
                    # PnL% = (Val_exit - Cost_exit - (Val_entry + Cost_entry)) / (Val_entry + Cost_entry)?
                    # Standard approx: Gross PnL - (2 * cost_per_side)
                    pnl = gross_pnl - (2 * cost_per_side)

                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": ts,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "type": "long" if current_position > 0 else "short",
                        "pnl": pnl
                    })
                    in_trade = False

                # Open new trade
                if pos != 0:
                    entry_price = price
                    entry_time = ts
                    in_trade = True

                current_position = pos

        # Close open trade at end
        if in_trade:
             exit_price = df["close"].iloc[-1]
             gross_pnl = (exit_price - entry_price) / entry_price * (1 if current_position > 0 else -1)
             pnl = gross_pnl - (2 * cost_per_side)

             trades.append({
                "entry_time": entry_time,
                "exit_time": df.index[-1],
                "entry_price": entry_price,
                "exit_price": exit_price,
                "type": "long" if current_position > 0 else "short",
                "pnl": pnl
            })

        return trades

    def _empty_result(self, config: BacktestConfig) -> BacktestResult:
        return BacktestResult(
            strategy_name=config.strategy_name,
            coin_type=config.coin_type,
            total_return=0.0,
            total_return_percent=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            total_trades=0,
            trades=[],
            equity_curve=[]
        )
