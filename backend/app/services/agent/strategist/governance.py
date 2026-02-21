from pydantic import BaseModel

from app.services.backtesting.schemas import BacktestResult


class GovernanceConfig(BaseModel):
    min_sharpe_ratio: float = 1.2
    max_drawdown_percent: float = 0.25  # 25%
    min_win_rate: float = 0.40  # 40%
    min_trades: int = 10  # Ensure statistical significance


class GovernanceDecision(BaseModel):
    approved: bool
    rejection_reasons: list[str]
    score: float


class GovernanceEvaluator:
    """
    Evaluates trading strategies against safety and performance 'Golden Rules'.
    """

    def __init__(self, config: GovernanceConfig | None = None):
        self.config = config or GovernanceConfig()

    def evaluate(self, result: BacktestResult) -> GovernanceDecision:
        reasons = []

        # 1. Sharpe Ratio Check
        if result.sharpe_ratio < self.config.min_sharpe_ratio:
            reasons.append(
                f"Sharpe Ratio {result.sharpe_ratio:.2f} < Minimum {self.config.min_sharpe_ratio}"
            )

        # 2. Max Drawdown Check (Note: drawdown is negative or positive? In engine it was: equity / cum_max - 1, so negative)
        # We generally check the absolute magnitude of drawdown.
        # If max_drawdown is e.g. -0.3, abs is 0.3 which is > 0.25.
        if abs(result.max_drawdown) > self.config.max_drawdown_percent:
            reasons.append(
                f"Max Drawdown {abs(result.max_drawdown):.2%} > Limit {self.config.max_drawdown_percent:.0%}"
            )

        # 3. Win Rate Check
        if result.win_rate < self.config.min_win_rate:
            reasons.append(
                f"Win Rate {result.win_rate:.2%} < Minimum {self.config.min_win_rate:.0%}"
            )

        # 4. Statistical Significance
        if result.total_trades < self.config.min_trades:
            reasons.append(
                f"Not enough trades ({result.total_trades}) to be statistically significant (Min {self.config.min_trades})"
            )

        is_approved = len(reasons) == 0

        # Simple Score: Weighted average of key metrics normalized
        # This is arbitrary for now, but useful for ranking
        score = (result.sharpe_ratio * 10) + (result.total_return_percent * 100)

        return GovernanceDecision(
            approved=is_approved, rejection_reasons=reasons, score=score
        )
