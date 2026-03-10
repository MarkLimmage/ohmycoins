"""Tests for backtest metrics calculator."""

from app.services.trading.metrics import calculate_backtest_metrics


class TestCalculateBacktestMetrics:
    def test_sharpe_and_sortino(self) -> None:
        """Test Sharpe and Sortino ratio calculation."""
        # Steadily increasing equity curve
        equity = [10000 + i * 10 for i in range(100)]
        trades = [{"pnl": 10.0} for _ in range(10)]
        result = calculate_backtest_metrics(equity, trades)

        assert result["sharpe_ratio"] > 0
        # Sortino will be 0 for steadily increasing curve (no downside returns)
        assert result["sortino_ratio"] >= 0
        assert result["total_return"] > 0

    def test_max_drawdown(self) -> None:
        """Test max drawdown calculation."""
        # Peak at 12000, drops to 9000, then recovers
        equity = [10000, 11000, 12000, 10000, 9000, 10000, 11000]
        trades = [{"pnl": -1000}, {"pnl": 2000}]
        result = calculate_backtest_metrics(equity, trades)

        # Max drawdown = (12000 - 9000) / 12000 = 0.25
        assert abs(result["max_drawdown"] - 0.25) < 0.01
        assert result["max_drawdown_duration"] > 0

    def test_win_rate_and_profit_factor(self) -> None:
        """Test win rate and profit factor."""
        equity = [10000, 10500, 10300, 10800]
        trades = [
            {"pnl": 500},
            {"pnl": -200},
            {"pnl": 500},
        ]
        result = calculate_backtest_metrics(equity, trades)

        assert abs(result["win_rate"] - 2 / 3) < 0.01
        assert result["profit_factor"] == round(1000 / 200, 4)
        assert result["num_trades"] == 3
        assert result["best_trade"] == 500
        assert result["worst_trade"] == -200

    def test_empty_inputs(self) -> None:
        """Test with no equity or trades."""
        result = calculate_backtest_metrics([], [])
        assert result["total_return"] == 0.0
        assert result["num_trades"] == 0
        assert result["sharpe_ratio"] == 0.0
