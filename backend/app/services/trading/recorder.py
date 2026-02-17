# mypy: ignore-errors
"""
Trade Recording and Reconciliation Service

This module tracks all trading activity, logs trade attempts, and reconciles
executed trades with exchange confirmations.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models import Order

logger = logging.getLogger(__name__)


class TradeRecorder:
    """
    Records and reconciles trading activity
    
    Features:
    - Log all trade attempts
    - Track successful and failed trades
    - Reconcile orders with exchange confirmations
    - Handle partial fills
    - Generate trade reports
    """
    
    def __init__(self, session: Session):
        """
        Initialize trade recorder
        
        Args:
            session: Database session
        """
        self.session = session
    
    def log_trade_attempt(
        self,
        user_id: UUID,
        coin_type: str,
        side: str,
        quantity: Decimal,
        order_type: str = 'market',
        price: Decimal | None = None,
        algorithm_id: UUID | None = None
    ) -> Order:
        """
        Log a trade attempt by creating an order record
        
        Args:
            user_id: User executing the trade
            coin_type: Cryptocurrency being traded
            side: 'buy' or 'sell'
            quantity: Trade quantity
            order_type: Order type (default: 'market')
            price: Limit price (for limit orders)
            algorithm_id: Algorithm ID if automated trade
            
        Returns:
            Created Order object
        """
        order = Order(
            user_id=user_id,
            coin_type=coin_type,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            algorithm_id=algorithm_id,
            status='pending',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        
        logger.info(
            f"Trade attempt logged: {order.id} - "
            f"{side} {quantity} {coin_type} for user {user_id}"
        )
        
        return order
    
    def record_success(
        self,
        order_id: UUID,
        coinspot_order_id: str,
        filled_quantity: Decimal,
        execution_price: Decimal
    ) -> None:
        """
        Record a successful trade execution
        
        Args:
            order_id: Internal order ID
            coinspot_order_id: Exchange order ID
            filled_quantity: Quantity filled
            execution_price: Actual execution price
        """
        order = self.session.get(Order, order_id)
        if not order:
            logger.error(f"Order {order_id} not found for success recording")
            return
        
        order.status = 'filled'
        order.filled_quantity = filled_quantity
        order.price = execution_price
        order.coinspot_order_id = coinspot_order_id
        order.filled_at = datetime.now(timezone.utc)
        order.updated_at = datetime.now(timezone.utc)
        
        self.session.add(order)
        self.session.commit()
        
        logger.info(
            f"Trade success recorded: {order_id} - "
            f"Filled {filled_quantity} at {execution_price} "
            f"(Exchange ID: {coinspot_order_id})"
        )
    
    def record_failure(
        self,
        order_id: UUID,
        error_message: str
    ) -> None:
        """
        Record a failed trade attempt
        
        Args:
            order_id: Internal order ID
            error_message: Error description
        """
        order = self.session.get(Order, order_id)
        if not order:
            logger.error(f"Order {order_id} not found for failure recording")
            return
        
        order.status = 'failed'
        order.error_message = error_message
        order.updated_at = datetime.now(timezone.utc)
        
        self.session.add(order)
        self.session.commit()
        
        logger.warning(
            f"Trade failure recorded: {order_id} - {error_message}"
        )
    
    def record_partial_fill(
        self,
        order_id: UUID,
        filled_quantity: Decimal,
        execution_price: Decimal
    ) -> None:
        """
        Record a partial fill
        
        Args:
            order_id: Internal order ID
            filled_quantity: Quantity filled so far
            execution_price: Average execution price
        """
        order = self.session.get(Order, order_id)
        if not order:
            logger.error(f"Order {order_id} not found for partial fill recording")
            return
        
        order.status = 'partial'
        order.filled_quantity = filled_quantity
        order.price = execution_price
        order.updated_at = datetime.now(timezone.utc)
        
        self.session.add(order)
        self.session.commit()
        
        logger.info(
            f"Partial fill recorded: {order_id} - "
            f"Filled {filled_quantity}/{order.quantity} at {execution_price}"
        )
    
    async def reconcile_order(
        self,
        order_id: UUID,
        exchange_data: dict[str, Any]
    ) -> bool:
        """
        Reconcile an order with exchange confirmation
        
        Args:
            order_id: Internal order ID
            exchange_data: Data from exchange API
            
        Returns:
            True if reconciliation successful, False otherwise
        """
        order = self.session.get(Order, order_id)
        if not order:
            logger.error(f"Order {order_id} not found for reconciliation")
            return False
        
        # Extract exchange data
        exchange_order_id = exchange_data.get('id')
        exchange_status = exchange_data.get('status')
        filled_amount = Decimal(str(exchange_data.get('amount', 0)))
        execution_rate = Decimal(str(exchange_data.get('rate', 0)))
        
        # Update order with exchange data
        if order.coinspot_order_id != exchange_order_id:
            logger.warning(
                f"Order {order_id} exchange ID mismatch: "
                f"expected {order.coinspot_order_id}, got {exchange_order_id}"
            )
            order.coinspot_order_id = exchange_order_id
        
        # Update status based on exchange status
        if exchange_status == 'complete':
            order.status = 'filled'
            order.filled_quantity = filled_amount
            order.price = execution_rate
            order.filled_at = datetime.now(timezone.utc)
        elif exchange_status == 'partial':
            order.status = 'partial'
            order.filled_quantity = filled_amount
            order.price = execution_rate
        elif exchange_status == 'cancelled':
            order.status = 'cancelled'
        
        order.updated_at = datetime.now(timezone.utc)
        
        self.session.add(order)
        self.session.commit()
        
        logger.info(
            f"Order reconciled: {order_id} - "
            f"Status: {order.status}, Filled: {filled_amount}"
        )
        
        return True
    
    def get_trade_history(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        coin_type: str | None = None,
        algorithm_id: UUID | None = None,
        status: str | None = None
    ) -> list[Order]:
        """
        Get trade history with filters
        
        Args:
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            coin_type: Coin type filter (optional)
            algorithm_id: Algorithm ID filter (optional)
            status: Order status filter (optional)
            
        Returns:
            List of Order objects matching filters
        """
        statement = select(Order).where(Order.user_id == user_id)
        
        if start_date:
            statement = statement.where(Order.created_at >= start_date)
        
        if end_date:
            statement = statement.where(Order.created_at <= end_date)
        
        if coin_type:
            statement = statement.where(Order.coin_type == coin_type)
        
        if algorithm_id:
            statement = statement.where(Order.algorithm_id == algorithm_id)
        
        if status:
            statement = statement.where(Order.status == status)
        
        statement = statement.order_by(Order.created_at.desc())
        
        orders = self.session.exec(statement).all()
        
        logger.debug(
            f"Retrieved {len(orders)} trades for user {user_id} with filters: "
            f"start={start_date}, end={end_date}, coin={coin_type}, "
            f"algo={algorithm_id}, status={status}"
        )
        
        return orders
    
    def get_trade_statistics(
        self,
        user_id: UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get trade statistics for a user
        
        Args:
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            Dictionary with trade statistics
        """
        orders = self.get_trade_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate statistics
        total_trades = len(orders)
        filled_trades = [o for o in orders if o.status == 'filled']
        failed_trades = [o for o in orders if o.status == 'failed']
        partial_trades = [o for o in orders if o.status == 'partial']
        
        buy_trades = [o for o in filled_trades if o.side == 'buy']
        sell_trades = [o for o in filled_trades if o.side == 'sell']
        
        total_buy_volume = sum(o.filled_quantity * o.price for o in buy_trades)
        total_sell_volume = sum(o.filled_quantity * o.price for o in sell_trades)
        
        stats = {
            'total_trades': total_trades,
            'filled_trades': len(filled_trades),
            'failed_trades': len(failed_trades),
            'partial_trades': len(partial_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_volume_aud': float(total_buy_volume),
            'total_sell_volume_aud': float(total_sell_volume),
            'success_rate': (
                len(filled_trades) / total_trades * 100 
                if total_trades > 0 else 0
            ),
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            }
        }
        
        logger.info(
            f"Trade statistics for user {user_id}: "
            f"{total_trades} total, {len(filled_trades)} filled, "
            f"{len(failed_trades)} failed"
        )
        
        return stats


def get_trade_recorder(session: Session) -> TradeRecorder:
    """
    Get a trade recorder instance
    
    Args:
        session: Database session
        
    Returns:
        TradeRecorder instance
    """
    return TradeRecorder(session)
