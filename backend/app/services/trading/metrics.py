# mypy: ignore-errors
"""Backtest performance metrics calculator."""

import math


def calculate_backtest_metrics(
    equity_curve: list[float],
    trades: list[dict],
) -> dict:
    """
    Calculate comprehensive backtest performance metrics.

    Args:
        equity_curve: List of equity values over time (daily granularity assumed).
        trades: List of trade dicts, each with at least a 'pnl' key (float).

    Returns:
        Dictionary of performance metrics.
    """
    if not equity_curve or len(equity_curve) < 2:
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_duration": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "num_trades": 0,
            "avg_trade_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }

    initial = equity_curve[0]
    final = equity_curve[-1]
    total_return = (final - initial) / initial if initial != 0 else 0.0

    # Daily returns
    returns = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        if prev != 0:
            returns.append((equity_curve[i] - prev) / prev)
        else:
            returns.append(0.0)

    # Sharpe ratio (annualized, 252 trading days)
    if returns:
        mean_return = sum(returns) / len(returns)
        std_return = (
            math.sqrt(sum((r - mean_return) ** 2 for r in returns) / len(returns))
            if len(returns) > 1
            else 0.0
        )
        sharpe_ratio = (
            (mean_return / std_return * math.sqrt(252)) if std_return > 0 else 0.0
        )
    else:
        sharpe_ratio = 0.0
        mean_return = 0.0

    # Sortino ratio (downside deviation only)
    downside_returns = [r for r in returns if r < 0]
    if downside_returns:
        downside_std = math.sqrt(
            sum(r**2 for r in downside_returns) / len(downside_returns)
        )
        sortino_ratio = (
            (mean_return / downside_std * math.sqrt(252)) if downside_std > 0 else 0.0
        )
    else:
        sortino_ratio = 0.0

    # Max drawdown and duration
    peak = equity_curve[0]
    max_drawdown = 0.0
    max_drawdown_duration = 0
    current_drawdown_start = 0
    in_drawdown = False

    for i, equity in enumerate(equity_curve):
        if equity > peak:
            if in_drawdown:
                duration = i - current_drawdown_start
                if duration > max_drawdown_duration:
                    max_drawdown_duration = duration
                in_drawdown = False
            peak = equity
        else:
            drawdown = (peak - equity) / peak if peak > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            if not in_drawdown:
                current_drawdown_start = i
                in_drawdown = True

    # Handle drawdown still ongoing at end
    if in_drawdown:
        duration = len(equity_curve) - current_drawdown_start
        if duration > max_drawdown_duration:
            max_drawdown_duration = duration

    # Trade metrics
    pnls = [t.get("pnl", 0.0) for t in trades]
    num_trades = len(trades)

    if num_trades > 0:
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p < 0]
        win_rate = len(winning) / num_trades
        gross_profit = sum(winning)
        gross_loss = abs(sum(losing))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        avg_trade_pnl = sum(pnls) / num_trades
        best_trade = max(pnls) if pnls else 0.0
        worst_trade = min(pnls) if pnls else 0.0
    else:
        win_rate = 0.0
        profit_factor = 0.0
        avg_trade_pnl = 0.0
        best_trade = 0.0
        worst_trade = 0.0

    return {
        "total_return": round(total_return, 6),
        "sharpe_ratio": round(sharpe_ratio, 4),
        "sortino_ratio": round(sortino_ratio, 4),
        "max_drawdown": round(max_drawdown, 6),
        "max_drawdown_duration": max_drawdown_duration,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "num_trades": num_trades,
        "avg_trade_pnl": round(avg_trade_pnl, 4),
        "best_trade": round(best_trade, 4),
        "worst_trade": round(worst_trade, 4),
    }
