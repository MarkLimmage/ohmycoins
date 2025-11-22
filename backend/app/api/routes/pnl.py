"""
P&L (Profit & Loss) API endpoints

Provides comprehensive P&L tracking and performance metrics for trading activities.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import CurrentUser, get_db
from app.services.trading.pnl import get_pnl_engine, PnLEngine, PnLMetrics


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================


class PnLSummaryResponse(BaseModel):
    """Response model for P&L summary"""
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    total_profit: float
    total_loss: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    max_drawdown: float
    sharpe_ratio: float
    total_volume: float
    total_fees: float
    
    @classmethod
    def from_metrics(cls, metrics: PnLMetrics) -> "PnLSummaryResponse":
        """Create response from PnLMetrics"""
        return cls(
            realized_pnl=float(metrics.realized_pnl),
            unrealized_pnl=float(metrics.unrealized_pnl),
            total_pnl=float(metrics.total_pnl),
            total_trades=metrics.total_trades,
            winning_trades=metrics.winning_trades,
            losing_trades=metrics.losing_trades,
            win_rate=float(metrics.win_rate),
            profit_factor=float(metrics.profit_factor),
            total_profit=float(metrics.total_profit),
            total_loss=float(metrics.total_loss),
            average_win=float(metrics.average_win),
            average_loss=float(metrics.average_loss),
            largest_win=float(metrics.largest_win),
            largest_loss=float(metrics.largest_loss),
            max_drawdown=float(metrics.max_drawdown),
            sharpe_ratio=float(metrics.sharpe_ratio),
            total_volume=float(metrics.total_volume),
            total_fees=float(metrics.total_fees)
        )


class PnLByAlgorithmResponse(BaseModel):
    """Response model for P&L grouped by algorithm"""
    algorithm_id: str
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    
    @classmethod
    def from_algorithm_metrics(cls, algorithm_id: UUID, metrics: PnLMetrics) -> "PnLByAlgorithmResponse":
        """Create response from algorithm ID and metrics"""
        return cls(
            algorithm_id=str(algorithm_id),
            realized_pnl=float(metrics.realized_pnl),
            unrealized_pnl=float(metrics.unrealized_pnl),
            total_pnl=float(metrics.total_pnl)
        )


class PnLByCoinResponse(BaseModel):
    """Response model for P&L grouped by coin"""
    coin_type: str
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    
    @classmethod
    def from_coin_metrics(cls, coin_type: str, metrics: PnLMetrics) -> "PnLByCoinResponse":
        """Create response from coin type and metrics"""
        return cls(
            coin_type=coin_type,
            realized_pnl=float(metrics.realized_pnl),
            unrealized_pnl=float(metrics.unrealized_pnl),
            total_pnl=float(metrics.total_pnl)
        )


class HistoricalPnLEntry(BaseModel):
    """Single entry in historical P&L data"""
    timestamp: str
    realized_pnl: float
    interval: str


class RealizedPnLResponse(BaseModel):
    """Response model for realized P&L"""
    realized_pnl: float


class UnrealizedPnLResponse(BaseModel):
    """Response model for unrealized P&L"""
    unrealized_pnl: float


# ============================================================================
# API Endpoints
# ============================================================================


@router.get("/summary", response_model=PnLSummaryResponse)
def get_pnl_summary(
    current_user: CurrentUser,
    session: Session = Depends(get_db),
    start_date: datetime | None = Query(None, description="Start date for P&L calculation (ISO format)"),
    end_date: datetime | None = Query(None, description="End date for P&L calculation (ISO format)")
) -> PnLSummaryResponse:
    """
    Get comprehensive P&L summary with performance metrics
    
    Returns realized and unrealized P&L along with detailed performance statistics
    including win rate, profit factor, largest trades, and total volume.
    
    Query Parameters:
    - start_date: Optional start date for filtering trades (ISO 8601 format)
    - end_date: Optional end date for filtering trades (ISO 8601 format)
    
    Returns:
    - PnLSummaryResponse with all P&L metrics and statistics
    """
    pnl_engine = get_pnl_engine(session)
    
    try:
        metrics = pnl_engine.get_pnl_summary(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return PnLSummaryResponse.from_metrics(metrics)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate P&L summary: {str(e)}"
        )


@router.get("/by-algorithm", response_model=list[PnLByAlgorithmResponse])
def get_pnl_by_algorithm(
    current_user: CurrentUser,
    session: Session = Depends(get_db),
    start_date: datetime | None = Query(None, description="Start date for P&L calculation"),
    end_date: datetime | None = Query(None, description="End date for P&L calculation")
) -> list[PnLByAlgorithmResponse]:
    """
    Get P&L metrics grouped by trading algorithm
    
    Shows which algorithms are performing well and which need improvement.
    
    Query Parameters:
    - start_date: Optional start date for filtering trades
    - end_date: Optional end date for filtering trades
    
    Returns:
    - List of P&L metrics per algorithm
    """
    pnl_engine = get_pnl_engine(session)
    
    try:
        pnl_by_algo = pnl_engine.get_pnl_by_algorithm(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return [
            PnLByAlgorithmResponse.from_algorithm_metrics(algorithm_id, metrics)
            for algorithm_id, metrics in pnl_by_algo.items()
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate P&L by algorithm: {str(e)}"
        )


@router.get("/by-coin", response_model=list[PnLByCoinResponse])
def get_pnl_by_coin(
    current_user: CurrentUser,
    session: Session = Depends(get_db),
    start_date: datetime | None = Query(None, description="Start date for P&L calculation"),
    end_date: datetime | None = Query(None, description="End date for P&L calculation")
) -> list[PnLByCoinResponse]:
    """
    Get P&L metrics grouped by cryptocurrency
    
    Shows which cryptocurrencies are generating the most profit/loss.
    
    Query Parameters:
    - start_date: Optional start date for filtering trades
    - end_date: Optional end date for filtering trades
    
    Returns:
    - List of P&L metrics per cryptocurrency
    """
    pnl_engine = get_pnl_engine(session)
    
    try:
        pnl_by_coin = pnl_engine.get_pnl_by_coin(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return [
            PnLByCoinResponse.from_coin_metrics(coin_type, metrics)
            for coin_type, metrics in pnl_by_coin.items()
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate P&L by coin: {str(e)}"
        )


@router.get("/history", response_model=list[HistoricalPnLEntry])
def get_historical_pnl(
    current_user: CurrentUser,
    session: Session = Depends(get_db),
    start_date: datetime = Query(..., description="Start date for historical data (required)"),
    end_date: datetime = Query(..., description="End date for historical data (required)"),
    interval: str = Query('day', description="Time interval (hour, day, week, month)")
) -> list[HistoricalPnLEntry]:
    """
    Get historical P&L data aggregated by time interval
    
    Provides time-series P&L data for charting and trend analysis.
    
    Query Parameters:
    - start_date: Start date for historical data (required, ISO 8601 format)
    - end_date: End date for historical data (required, ISO 8601 format)
    - interval: Aggregation interval - 'hour', 'day', 'week', or 'month' (default: 'day')
    
    Returns:
    - List of historical P&L data points with timestamps
    """
    # Validate interval
    valid_intervals = ['hour', 'day', 'week', 'month']
    if interval not in valid_intervals:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
        )
    
    pnl_engine = get_pnl_engine(session)
    
    try:
        historical_data = pnl_engine.get_historical_pnl(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        return [
            HistoricalPnLEntry(
                timestamp=entry['timestamp'],
                realized_pnl=entry['realized_pnl'],
                interval=entry['interval']
            )
            for entry in historical_data
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get historical P&L: {str(e)}"
        )


@router.get("/realized", response_model=RealizedPnLResponse)
def get_realized_pnl(
    current_user: CurrentUser,
    session: Session = Depends(get_db),
    start_date: datetime | None = Query(None, description="Start date for P&L calculation"),
    end_date: datetime | None = Query(None, description="End date for P&L calculation"),
    algorithm_id: UUID | None = Query(None, description="Filter by algorithm ID"),
    coin_type: str | None = Query(None, description="Filter by cryptocurrency (e.g., 'BTC')")
) -> RealizedPnLResponse:
    """
    Get realized P&L from completed trades
    
    Realized P&L is calculated from the difference between sell price and
    matching buy prices using FIFO accounting method.
    
    Query Parameters:
    - start_date: Optional start date for filtering trades
    - end_date: Optional end date for filtering trades
    - algorithm_id: Optional filter by algorithm UUID
    - coin_type: Optional filter by cryptocurrency symbol
    
    Returns:
    - RealizedPnLResponse with realized_pnl value
    """
    pnl_engine = get_pnl_engine(session)
    
    try:
        realized_pnl = pnl_engine.calculate_realized_pnl(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            algorithm_id=algorithm_id,
            coin_type=coin_type
        )
        
        return RealizedPnLResponse(realized_pnl=float(realized_pnl))
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate realized P&L: {str(e)}"
        )


@router.get("/unrealized", response_model=UnrealizedPnLResponse)
def get_unrealized_pnl(
    current_user: CurrentUser,
    session: Session = Depends(get_db),
    coin_type: str | None = Query(None, description="Filter by cryptocurrency (e.g., 'BTC')")
) -> UnrealizedPnLResponse:
    """
    Get unrealized P&L from current open positions
    
    Unrealized P&L is the difference between current market value
    and the total cost of current positions.
    
    Query Parameters:
    - coin_type: Optional filter by cryptocurrency symbol
    
    Returns:
    - UnrealizedPnLResponse with unrealized_pnl value
    """
    pnl_engine = get_pnl_engine(session)
    
    try:
        unrealized_pnl = pnl_engine.calculate_unrealized_pnl(
            user_id=current_user.id,
            coin_type=coin_type
        )
        
        return UnrealizedPnLResponse(unrealized_pnl=float(unrealized_pnl))
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate unrealized P&L: {str(e)}"
        )
