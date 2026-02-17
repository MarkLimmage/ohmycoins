# mypy: ignore-errors
"""
Profit & Loss (P&L) Calculation Engine

This module provides comprehensive P&L tracking and performance metrics
for the OhMyCoins trading platform.

Features:
- Realized P&L calculation (on completed trades)
- Unrealized P&L calculation (on open positions)
- Historical P&L tracking
- Performance metrics (Sharpe ratio, max drawdown, win rate, profit factor)
- P&L aggregation by algorithm, coin, and time period
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import desc
from sqlmodel import Session, select

from app.models import Order, Position, PriceData5Min

logger = logging.getLogger(__name__)


class PnLMetrics:
    """Container for P&L metrics and performance statistics"""

    def __init__(
        self,
        realized_pnl: Decimal = Decimal('0'),
        unrealized_pnl: Decimal = Decimal('0'),
        total_pnl: Decimal | None = None,
        total_trades: int = 0,
        winning_trades: int = 0,
        losing_trades: int = 0,
        win_rate: Decimal | None = None,
        profit_factor: Decimal | None = None,
        total_profit: Decimal = Decimal('0'),
        total_loss: Decimal = Decimal('0'),
        average_win: Decimal | None = None,
        average_loss: Decimal | None = None,
        largest_win: Decimal = Decimal('0'),
        largest_loss: Decimal = Decimal('0'),
        max_drawdown: Decimal | None = None,
        sharpe_ratio: Decimal | None = None,
        total_volume: Decimal = Decimal('0'),
        total_fees: Decimal = Decimal('0')
    ):
        self.realized_pnl = realized_pnl
        self.unrealized_pnl = unrealized_pnl
        self.total_pnl = total_pnl if total_pnl is not None else (realized_pnl + unrealized_pnl)
        self.total_trades = total_trades
        self.winning_trades = winning_trades
        self.losing_trades = losing_trades
        self.win_rate = win_rate if win_rate is not None else (
            Decimal(winning_trades) / Decimal(total_trades) * Decimal('100')
            if total_trades > 0 else Decimal('0')
        )
        self.profit_factor = profit_factor if profit_factor is not None else (
            total_profit / abs(total_loss) if total_loss != 0 else Decimal('0')
        )
        self.total_profit = total_profit
        self.total_loss = total_loss
        self.average_win = average_win if average_win is not None else (
            total_profit / Decimal(winning_trades) if winning_trades > 0 else Decimal('0')
        )
        self.average_loss = average_loss if average_loss is not None else (
            abs(total_loss) / Decimal(losing_trades) if losing_trades > 0 else Decimal('0')
        )
        self.largest_win = largest_win
        self.largest_loss = largest_loss
        self.max_drawdown = max_drawdown if max_drawdown is not None else Decimal('0')
        self.sharpe_ratio = sharpe_ratio if sharpe_ratio is not None else Decimal('0')
        self.total_volume = total_volume
        self.total_fees = total_fees

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'realized_pnl': float(self.realized_pnl),
            'unrealized_pnl': float(self.unrealized_pnl),
            'total_pnl': float(self.total_pnl),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': float(self.win_rate),
            'profit_factor': float(self.profit_factor),
            'total_profit': float(self.total_profit),
            'total_loss': float(self.total_loss),
            'average_win': float(self.average_win),
            'average_loss': float(self.average_loss),
            'largest_win': float(self.largest_win),
            'largest_loss': float(self.largest_loss),
            'max_drawdown': float(self.max_drawdown),
            'sharpe_ratio': float(self.sharpe_ratio),
            'total_volume': float(self.total_volume),
            'total_fees': float(self.total_fees)
        }


class PnLEngine:
    """
    Profit & Loss Calculation Engine
    
    Calculates realized and unrealized P&L, tracks performance metrics,
    and provides historical P&L data aggregation.
    """

    def __init__(self, session: Session):
        """
        Initialize P&L engine
        
        Args:
            session: Database session
        """
        self.session = session

    def calculate_realized_pnl(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        algorithm_id: UUID | None = None,
        coin_type: str | None = None
    ) -> Decimal:
        """
        Calculate realized P&L from completed trades
        
        Realized P&L is calculated from the difference between sell price and
        matching buy prices using FIFO (First In First Out) accounting method.
        
        Args:
            user_id: User UUID
            start_date: Start date for P&L calculation (inclusive)
            end_date: End date for P&L calculation (inclusive)
            algorithm_id: Filter by algorithm ID
            coin_type: Filter by coin type
            
        Returns:
            Realized P&L as Decimal
        """
        # Build query for filled orders
        query = select(Order).where(
            Order.user_id == user_id,
            Order.status == 'filled'
        )

        # Apply filters
        # Note: We don't filter by start_date in the query because we need
        # historical buy orders to correctly calculate cost basis (FIFO).
        # Filtering by start_date happens in memory during accumulation.
        if end_date:
            query = query.where(Order.filled_at <= end_date)
        if algorithm_id:
            query = query.where(Order.algorithm_id == algorithm_id)
        if coin_type:
            query = query.where(Order.coin_type == coin_type)

        # Order by filled_at to process trades chronologically
        query = query.order_by(Order.filled_at)

        orders = self.session.exec(query).all()

        # Calculate P&L using FIFO (First In, First Out) method
        realized_pnl = Decimal('0')
        positions_tracker: dict[str, list[tuple[Decimal, Decimal]]] = {}  # coin -> [(quantity, price)]

        for order in orders:
            if order.side == 'buy':
                # Add to position tracker
                if order.coin_type not in positions_tracker:
                    positions_tracker[order.coin_type] = []
                positions_tracker[order.coin_type].append(
                    (order.filled_quantity, order.price or Decimal('0'))
                )

            elif order.side == 'sell':
                # Calculate realized P&L from sell
                if order.coin_type not in positions_tracker or not positions_tracker[order.coin_type]:
                    # No buy positions to match against - skip
                    logger.warning(
                        f"Sell order {order.id} has no matching buy positions for {order.coin_type}"
                    )
                    continue

                sell_quantity = order.filled_quantity
                sell_price = order.price or Decimal('0')

                # Match sells against buys using FIFO
                while sell_quantity > 0 and positions_tracker[order.coin_type]:
                    buy_quantity, buy_price = positions_tracker[order.coin_type][0]

                    # Calculate how much we can match
                    match_quantity = min(sell_quantity, buy_quantity)

                    # Calculate P&L for this match
                    trade_pnl = match_quantity * (sell_price - buy_price)

                    # Only calculate/add P&L if within the requested window
                    if not start_date or order.filled_at >= start_date:
                        realized_pnl += trade_pnl

                    # Update quantities
                    sell_quantity -= match_quantity
                    buy_quantity -= match_quantity

                    # Update or remove buy position
                    if buy_quantity > 0:
                        positions_tracker[order.coin_type][0] = (buy_quantity, buy_price)
                    else:
                        positions_tracker[order.coin_type].pop(0)

        return realized_pnl

    def calculate_unrealized_pnl(
        self,
        user_id: UUID,
        coin_type: str | None = None
    ) -> Decimal:
        """
        Calculate unrealized P&L from current positions
        
        Unrealized P&L is the difference between current market value
        and the total cost of current positions.
        
        Args:
            user_id: User UUID
            coin_type: Filter by coin type
            
        Returns:
            Unrealized P&L as Decimal
        """
        # Get current positions
        query = select(Position).where(Position.user_id == user_id)

        if coin_type:
            query = query.where(Position.coin_type == coin_type)

        positions = self.session.exec(query).all()

        unrealized_pnl = Decimal('0')

        for position in positions:
            # Get current price for this coin
            current_price = self._get_current_price(position.coin_type)

            if current_price is None:
                logger.warning(f"No price data for {position.coin_type}, skipping unrealized P&L")
                continue

            # Calculate current value
            current_value = position.quantity * current_price

            # Calculate unrealized P&L
            position_pnl = current_value - position.total_cost
            unrealized_pnl += position_pnl

        return unrealized_pnl

    def get_pnl_summary(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> PnLMetrics:
        """
        Get comprehensive P&L summary with performance metrics
        
        Args:
            user_id: User UUID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            PnLMetrics object with all performance statistics
        """
        # Calculate realized and unrealized P&L
        realized_pnl = self.calculate_realized_pnl(user_id, start_date, end_date)
        unrealized_pnl = self.calculate_unrealized_pnl(user_id)

        # Get trade statistics
        query = select(Order).where(
            Order.user_id == user_id,
            Order.status == 'filled'
        )

        if start_date:
            query = query.where(Order.filled_at >= start_date)
        if end_date:
            query = query.where(Order.filled_at <= end_date)

        orders = self.session.exec(query).all()

        # Calculate trade metrics
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        total_profit = Decimal('0')
        total_loss = Decimal('0')
        largest_win = Decimal('0')
        largest_loss = Decimal('0')
        total_volume = Decimal('0')

        # Track positions for P&L calculation per trade
        positions_tracker: dict[str, list[tuple[Decimal, Decimal]]] = {}

        for order in orders:
            if order.side == 'buy':
                # Track buy positions
                if order.coin_type not in positions_tracker:
                    positions_tracker[order.coin_type] = []
                positions_tracker[order.coin_type].append(
                    (order.filled_quantity, order.price or Decimal('0'))
                )
                total_volume += order.filled_quantity * (order.price or Decimal('0'))

            elif order.side == 'sell':
                # Calculate P&L for this sell
                if order.coin_type not in positions_tracker or not positions_tracker[order.coin_type]:
                    continue

                sell_quantity = order.filled_quantity
                sell_price = order.price or Decimal('0')
                trade_pnl = Decimal('0')

                # Match against buys
                while sell_quantity > 0 and positions_tracker[order.coin_type]:
                    buy_quantity, buy_price = positions_tracker[order.coin_type][0]
                    match_quantity = min(sell_quantity, buy_quantity)

                    pnl = match_quantity * (sell_price - buy_price)
                    trade_pnl += pnl

                    sell_quantity -= match_quantity
                    buy_quantity -= match_quantity

                    if buy_quantity > 0:
                        positions_tracker[order.coin_type][0] = (buy_quantity, buy_price)
                    else:
                        positions_tracker[order.coin_type].pop(0)

                # Update statistics
                total_trades += 1
                total_volume += order.filled_quantity * sell_price

                if trade_pnl > 0:
                    winning_trades += 1
                    total_profit += trade_pnl
                    largest_win = max(largest_win, trade_pnl)
                elif trade_pnl < 0:
                    losing_trades += 1
                    total_loss += trade_pnl
                    largest_loss = min(largest_loss, trade_pnl)

        return PnLMetrics(
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_profit=total_profit,
            total_loss=total_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            total_volume=total_volume
        )

    def get_pnl_by_algorithm(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[UUID, PnLMetrics]:
        """
        Get P&L metrics grouped by algorithm
        
        Args:
            user_id: User UUID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary mapping algorithm_id to PnLMetrics
        """
        # Get all algorithms used by this user
        query = select(Order.algorithm_id).where(
            Order.user_id == user_id,
            Order.algorithm_id.isnot(None),
            Order.status == 'filled'
        ).distinct()

        if start_date:
            query = query.where(Order.filled_at >= start_date)
        if end_date:
            query = query.where(Order.filled_at <= end_date)

        algorithm_ids = self.session.exec(query).all()

        result = {}
        for algo_id in algorithm_ids:
            realized_pnl = self.calculate_realized_pnl(
                user_id, start_date, end_date, algorithm_id=algo_id
            )
            # Note: Unrealized P&L not split by algorithm as positions don't track algorithm
            result[algo_id] = PnLMetrics(realized_pnl=realized_pnl)

        return result

    def get_pnl_by_coin(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, PnLMetrics]:
        """
        Get P&L metrics grouped by cryptocurrency
        
        Args:
            user_id: User UUID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary mapping coin_type to PnLMetrics
        """
        # Get all coins traded by this user
        query = select(Order.coin_type).where(
            Order.user_id == user_id,
            Order.status == 'filled'
        ).distinct()

        if start_date:
            query = query.where(Order.filled_at >= start_date)
        if end_date:
            query = query.where(Order.filled_at <= end_date)

        coin_types = self.session.exec(query).all()

        result = {}
        for coin_type in coin_types:
            realized_pnl = self.calculate_realized_pnl(
                user_id, start_date, end_date, coin_type=coin_type
            )
            unrealized_pnl = self.calculate_unrealized_pnl(user_id, coin_type=coin_type)
            result[coin_type] = PnLMetrics(
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl
            )

        return result

    def get_historical_pnl(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        interval: str = 'day'
    ) -> list[dict[str, Any]]:
        """
        Get historical P&L data aggregated by time interval
        
        Args:
            user_id: User UUID
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Aggregation interval ('hour', 'day', 'week', 'month')
            
        Returns:
            List of dictionaries with timestamp and P&L data
        """
        # Determine time buckets based on interval
        if interval == 'hour':
            delta = timedelta(hours=1)
        elif interval == 'day':
            delta = timedelta(days=1)
        elif interval == 'week':
            delta = timedelta(weeks=1)
        elif interval == 'month':
            delta = timedelta(days=30)  # Approximate
        else:
            raise ValueError(f"Invalid interval: {interval}")

        result = []
        current_date = start_date

        while current_date <= end_date:
            next_date = current_date + delta

            # Calculate P&L for this time bucket
            realized_pnl = self.calculate_realized_pnl(
                user_id,
                start_date=current_date,
                end_date=next_date
            )

            result.append({
                'timestamp': current_date.isoformat(),
                'realized_pnl': float(realized_pnl),
                'interval': interval
            })

            current_date = next_date

        return result

    def _get_current_price(self, coin_type: str) -> Decimal | None:
        """
        Get the most recent price for a cryptocurrency
        
        Args:
            coin_type: Cryptocurrency symbol
            
        Returns:
            Current price or None if not available
        """
        # Query for most recent price data
        query = select(PriceData5Min).where(
            PriceData5Min.coin_type == coin_type
        ).order_by(desc(PriceData5Min.timestamp)).limit(1)

        price_data = self.session.exec(query).first()

        if price_data:
            # Use last price (most recent trade price)
            logger.debug(
                f"Using price for {coin_type}: {price_data.last} "
                f"(timestamp: {price_data.timestamp})"
            )
            return price_data.last

        logger.debug(f"No price data found for {coin_type}")
        return None


# Factory function for creating P&L engine instances
def get_pnl_engine(session: Session) -> PnLEngine:
    """
    Factory function to create a PnLEngine instance
    
    Args:
        session: Database session
        
    Returns:
        PnLEngine instance
    """
    return PnLEngine(session)
