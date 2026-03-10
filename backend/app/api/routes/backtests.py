# mypy: ignore-errors
"""Backtest API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import desc, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    BacktestRun,
    BacktestRunCreate,
    BacktestRunList,
    BacktestRunPublic,
)
from app.services.trading.backtester import BacktestEngine

router = APIRouter()


@router.post("", response_model=BacktestRunPublic)
def create_backtest(
    body: BacktestRunCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Create and run a backtest."""
    engine = BacktestEngine(session)
    result = engine.run(
        algorithm_id=body.algorithm_id,
        coin_type=body.coin_type,
        start_date=body.start_date,
        end_date=body.end_date,
        initial_capital=body.initial_capital,
        user_id=current_user.id,
    )
    return result


@router.get("/{backtest_id}", response_model=BacktestRunPublic)
def get_backtest(
    backtest_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get a backtest by ID."""
    backtest = session.get(BacktestRun, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    if backtest.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return backtest


@router.get("", response_model=BacktestRunList)
def list_backtests(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 20,
) -> Any:
    """List user's backtests."""
    count_statement = (
        select(func.count())
        .select_from(BacktestRun)
        .where(BacktestRun.user_id == current_user.id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(BacktestRun)
        .where(BacktestRun.user_id == current_user.id)
        .order_by(desc(BacktestRun.created_at))
        .offset(skip)
        .limit(limit)
    )
    backtests = session.exec(statement).all()
    return BacktestRunList(data=backtests, count=count)
