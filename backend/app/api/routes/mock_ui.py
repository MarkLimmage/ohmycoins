"""
Mock API endpoints for Storybook and UI development.
Available only in non-production environments.
"""
import random
import uuid
from datetime import datetime, timedelta, timezone

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import Field

from app.api.response_base import APIResponseBase
from app.api.routes.pnl import PnLSummaryResponse
from app.models import (
    AgentSessionMessagePublic,
    Signal,
)

router = APIRouter()

# ============================================================================
# LedgerCard Mocks
# ============================================================================

@router.get("/ledgers/{ledger_type}", response_model=PnLSummaryResponse)
async def get_mock_ledger_data(ledger_type: str, state: str = "success") -> PnLSummaryResponse:
    """
    Get mock data for LedgerCard component.

    Args:
        ledger_type: 'human', 'catalyst', 'algorithm', 'exchange', etc.
        state: 'success', 'loading', 'error', 'empty'
    """
    if state == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to load ledger data",
                "detail": "Connection to data provider timed out after 5000ms",
                "error_code": "DATA_PROVIDER_TIMEOUT"
            }
        )

    is_loading = (state == "loading")

    # Base mock data
    mock_data: dict[str, Any] = {
        "realized_pnl": 1250.50 if state != "empty" else 0.0,
        "unrealized_pnl": -320.25 if state != "empty" else 0.0,
        "total_pnl": 930.25 if state != "empty" else 0.0,
        "total_trades": 42 if state != "empty" else 0,
        "winning_trades": 28 if state != "empty" else 0,
        "losing_trades": 14 if state != "empty" else 0,
        "win_rate": 0.66 if state != "empty" else 0.0,
        "profit_factor": 1.5,
        "total_profit": 5600.0,
        "total_loss": 3729.0,
        "average_win": 200.0,
        "average_loss": -266.3,
        "largest_win": 1200.0,
        "largest_loss": -800.0,
        "max_drawdown": -15.5,
        "sharpe_ratio": 1.8,
        "total_volume": 150000.0,
        "total_fees": 150.0,
        # API Response Base
        "is_loading": is_loading,
        "last_updated": datetime.now(timezone.utc),
        "data_staleness_seconds": 0.0
    }

    return PnLSummaryResponse(**mock_data)

# ============================================================================
# AgentTerminal Mocks
# ============================================================================

@router.get("/agent/sessions/{session_id}/messages", response_model=list[AgentSessionMessagePublic])
async def get_mock_agent_messages(session_id: uuid.UUID, _stream: bool = False) -> list[AgentSessionMessagePublic]:
    """Get mock messages for AgentTerminal."""

    agents = ["ResearchAgent", "StrategyAgent", "ExecutionAgent", "RiskAgent"]
    messages = []

    # Generate 10 mock messages
    for i in range(10):
        role = "assistant" if i % 2 == 0 else "user"
        agent_name = random.choice(agents) if role == "assistant" else None

        msg = AgentSessionMessagePublic(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=f"Mock message {i+1} content... Analysing market data for BTC/USDT.",
            agent_name=agent_name,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10-i),
            is_loading=False,
            last_updated=datetime.now(timezone.utc),
            data_staleness_seconds=0.0
        )
        messages.append(msg)

    return messages

# ============================================================================
# SafetyButton Mocks
# ============================================================================

class SafetyStatusResponse(APIResponseBase):
    status: str = Field(description="Safety system status: active, triggered, disabled")
    triggered_at: datetime | None = Field(default=None, description="When the safety mechanism was triggered")
    triggered_by: str | None = Field(default=None, description="User or system that triggered it")

@router.post("/safety/{action_type}", response_model=SafetyStatusResponse)
async def trigger_mock_safety_action(action_type: str, confirm: bool = False) -> SafetyStatusResponse:
    """
    Mock endpoint for SafetyButton actions.

    Args:
        action_type: 'kill-switch', 'confirm-trade', 'emergency-stop'
    """
    if not confirm:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Confirmation required",
                "detail": "Action requires explicit confirmation.",
                "error_code": "MISSING_CONFIRMATION"
            }
        )

    return SafetyStatusResponse(
        status="triggered",
        triggered_at=datetime.now(timezone.utc),
        triggered_by="current_user",
        is_loading=False,
        last_updated=datetime.now(timezone.utc),
        data_staleness_seconds=0.0
    )

# ============================================================================
# Active Signals Mocks
# ============================================================================

@router.get("/signals/active", response_model=list[Signal])
async def get_mock_active_signals() -> list[Signal]:
    """Get mock active signals for Dashboard."""
    return [
        Signal(
            id=1,
            type="buy",
            asset="BTC/USDT",
            strength=0.85,
            generated_at=datetime.now(timezone.utc),
            source="MovingAverageCrossover",
            context={"short_window": 50, "long_window": 200, "reason": "Golden Cross confirmed"}
        ),
        Signal(
            id=2,
            type="sell",
            asset="ETH/USDT",
            strength=0.72,
            generated_at=datetime.now(timezone.utc) - timedelta(minutes=15),
            source="RSIOverbought",
            context={"period": 14, "current_rsi": 82.5}
        ),
        Signal(
            id=3,
            type="neutral",
            asset="SOL/USDT",
            strength=0.30,
            generated_at=datetime.now(timezone.utc) - timedelta(hours=1),
            source="NewsSentiment",
            context={"news_count": 5, "sentiment_score": 0.1}
        )
    ]

# ============================================================================
# Collector Stats Mocks
# ============================================================================

from pydantic import BaseModel

class CollectorStat(BaseModel):
    timestamp: datetime
    records_collected: int

@router.get("/collectors/stats", response_model=list[CollectorStat])
async def get_mock_collector_stats() -> list[CollectorStat]:
    """Get mock collector execution stats for Dashboard sparkline."""
    stats = []
    now = datetime.now(timezone.utc)
    # Generate data for the last 60 minutes
    for i in range(60):
        t = now - timedelta(minutes=60-i)
        # Random data with some spikes
        count = random.randint(5, 50)
        if i % 15 == 0:
            count += 100 # Simulate a burst
        stats.append(CollectorStat(timestamp=t, records_collected=count))
    return stats
