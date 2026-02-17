from app.services.agent.strategist.governance import (
    GovernanceConfig,
    GovernanceEvaluator,
)
from app.services.backtesting.schemas import BacktestResult


def test_governance_approval():
    evaluator = GovernanceEvaluator(GovernanceConfig(
        min_sharpe_ratio=1.5,
        max_drawdown_percent=0.20
    ))

    good_result = BacktestResult(
        strategy_name="GoodStrat",
        coin_type="BTC",
        total_return=1000.0,
        total_return_percent=0.10,
        max_drawdown=-0.10,  # 10% DD
        sharpe_ratio=2.0,
        win_rate=0.6,
        total_trades=50
    )

    decision = evaluator.evaluate(good_result)
    assert decision.approved is True
    assert len(decision.rejection_reasons) == 0

def test_governance_rejection():
    evaluator = GovernanceEvaluator(GovernanceConfig(
        min_sharpe_ratio=1.5,
        max_drawdown_percent=0.20
    ))

    bad_result = BacktestResult(
        strategy_name="BadStrat",
        coin_type="BTC",
        total_return=1000.0,
        total_return_percent=0.10,
        max_drawdown=-0.30,  # 30% DD, should fail
        sharpe_ratio=1.0,    # Should fail
        win_rate=0.3,        # Should fail default 40%
        total_trades=5       # Should fail default 10
    )

    decision = evaluator.evaluate(bad_result)
    assert decision.approved is False
    assert len(decision.rejection_reasons) >= 1
    assert any("Sharpe" in r for r in decision.rejection_reasons)
    assert any("Drawdown" in r for r in decision.rejection_reasons)
