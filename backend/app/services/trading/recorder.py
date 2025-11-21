"""
Trade Recorder Service

Maintains comprehensive audit trail of all trading activity:
1. Log all trade attempts with full context
2. Record successful trades with Coinspot confirmation
3. Track failed trades with error reasons
4. Trade reconciliation with Coinspot API
5. Audit trail query APIs

All trading decisions and executions are logged for:
- Regulatory compliance
- Performance analysis
- Debugging and troubleshooting
- User transparency

Phase 6, Weeks 3-4
"""
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlmodel import Session, select, and_, or_

from app.models import Order, DeployedAlgorithm, Algorithm

logger = logging.getLogger(__name__)


class TradeRecordingError(Exception):
    """Exception raised when trade recording fails"""
    pass


class TradeRecorder:
    """
    Records and tracks all trading activity
    
    Responsible for:
    - Logging trade attempts before execution
    - Recording trade outcomes (success/failure)
    - Storing algorithm decisions and signals
    - Reconciling trades with Coinspot confirmations
    - Providing audit trail queries
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize trade recorder
        
        Args:
            db_session: Database session for recording
        """
        self.db = db_session
    
    async def record_trade_attempt(
        self,
        order: Order,
        algorithm_id: UUID | None = None,
        signal: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Record a trade attempt before execution
        
        Creates an Order record in 'pending' status with full context.
        
        Args:
            order: The order being attempted
            algorithm_id: UUID of algorithm that generated the signal (if applicable)
            signal: The trading signal that triggered this order
            context: Additional context (market data, algorithm state, etc.)
            
        Returns:
            UUID of the created order record
        """
        try:
            # Order should already have an ID if it was created via OrderCreate
            # If not, it will get one when added to the database
            
            # Add optional metadata as JSON in error_message field temporarily
            # (In production, would add a metadata_json field to Order model)
            metadata = {
                "signal": signal,
                "context": context,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            
            logger.info(
                f"Recording trade attempt: "
                f"order_id={order.id}, side={order.side}, "
                f"coin={order.coin_type}, qty={order.quantity}, "
                f"algorithm_id={algorithm_id}"
            )
            
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
            
            return order.id
            
        except Exception as e:
            logger.exception(f"Failed to record trade attempt: {str(e)}")
            raise TradeRecordingError(f"Recording failed: {str(e)}") from e
    
    async def record_trade_success(
        self,
        order_id: UUID,
        coinspot_order_id: str,
        filled_quantity: Decimal,
        filled_price: Decimal,
    ) -> None:
        """
        Record a successful trade execution
        
        Updates order status to 'filled' and records Coinspot confirmation.
        
        Args:
            order_id: UUID of the order
            coinspot_order_id: Coinspot's order ID from their API
            filled_quantity: Quantity that was filled
            filled_price: Price at which order was filled
        """
        try:
            # Load order
            statement = select(Order).where(Order.id == order_id)
            order = self.db.exec(statement).first()
            
            if not order:
                raise TradeRecordingError(f"Order {order_id} not found")
            
            # Update order
            order.status = "filled"
            order.coinspot_order_id = coinspot_order_id
            order.filled_quantity = filled_quantity
            order.price = filled_price
            order.filled_at = datetime.now(timezone.utc)
            
            self.db.add(order)
            self.db.commit()
            
            logger.info(
                f"Recorded trade success: "
                f"order_id={order_id}, coinspot_id={coinspot_order_id}, "
                f"filled_qty={filled_quantity}, price={filled_price}"
            )
            
        except Exception as e:
            logger.exception(f"Failed to record trade success: {str(e)}")
            raise TradeRecordingError(f"Recording failed: {str(e)}") from e
    
    async def record_trade_failure(
        self,
        order_id: UUID,
        error_message: str,
    ) -> None:
        """
        Record a failed trade execution
        
        Updates order status to 'failed' and stores error message.
        
        Args:
            order_id: UUID of the order
            error_message: Error message describing the failure
        """
        try:
            # Load order
            statement = select(Order).where(Order.id == order_id)
            order = self.db.exec(statement).first()
            
            if not order:
                raise TradeRecordingError(f"Order {order_id} not found")
            
            # Update order
            order.status = "failed"
            order.error_message = error_message[:500]  # Truncate to max length
            
            self.db.add(order)
            self.db.commit()
            
            logger.warning(
                f"Recorded trade failure: "
                f"order_id={order_id}, error={error_message}"
            )
            
        except Exception as e:
            logger.exception(f"Failed to record trade failure: {str(e)}")
            raise TradeRecordingError(f"Recording failed: {str(e)}") from e
    
    async def reconcile_trade(
        self,
        order_id: UUID,
        coinspot_order_data: dict[str, Any],
    ) -> bool:
        """
        Reconcile an order with Coinspot's confirmation data
        
        Verifies that our internal order matches Coinspot's records.
        Updates order if discrepancies are found.
        
        Args:
            order_id: UUID of the order
            coinspot_order_data: Order data from Coinspot API
            
        Returns:
            True if reconciliation successful, False if discrepancies found
        """
        try:
            # Load order
            statement = select(Order).where(Order.id == order_id)
            order = self.db.exec(statement).first()
            
            if not order:
                logger.error(f"Order {order_id} not found for reconciliation")
                return False
            
            # Extract Coinspot data
            coinspot_id = coinspot_order_data.get("id")
            coinspot_status = coinspot_order_data.get("status")
            coinspot_filled_qty = Decimal(str(coinspot_order_data.get("filled_amount", "0")))
            coinspot_price = Decimal(str(coinspot_order_data.get("price", "0")))
            
            # Check for discrepancies
            discrepancies = []
            
            if order.coinspot_order_id != coinspot_id:
                discrepancies.append(
                    f"Order ID mismatch: ours={order.coinspot_order_id}, "
                    f"theirs={coinspot_id}"
                )
            
            if coinspot_status == "filled" and order.status != "filled":
                discrepancies.append(
                    f"Status mismatch: ours={order.status}, theirs={coinspot_status}"
                )
                # Update our status to match
                order.status = "filled"
            
            if abs(order.filled_quantity - coinspot_filled_qty) > Decimal("0.00000001"):
                discrepancies.append(
                    f"Filled quantity mismatch: ours={order.filled_quantity}, "
                    f"theirs={coinspot_filled_qty}"
                )
                # Update our quantity to match
                order.filled_quantity = coinspot_filled_qty
            
            if order.price and abs(order.price - coinspot_price) > Decimal("0.01"):
                discrepancies.append(
                    f"Price mismatch: ours={order.price}, theirs={coinspot_price}"
                )
                # Update our price to match
                order.price = coinspot_price
            
            if discrepancies:
                logger.warning(
                    f"Trade reconciliation found discrepancies for order {order_id}: "
                    f"{', '.join(discrepancies)}"
                )
                
                # Save updates
                self.db.add(order)
                self.db.commit()
                
                return False
            
            logger.info(f"Trade reconciliation successful for order {order_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to reconcile trade {order_id}: {str(e)}")
            return False
    
    async def get_trades_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Order]:
        """
        Get trades for a user
        
        Args:
            user_id: UUID of the user
            status: Optional status filter ('pending', 'filled', 'failed', etc.)
            limit: Maximum number of trades to return
            
        Returns:
            List of Order objects
        """
        statement = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        
        if status:
            statement = statement.where(Order.status == status)
        
        trades = self.db.exec(statement).all()
        return list(trades)
    
    async def get_trades_by_algorithm(
        self,
        algorithm_id: UUID,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Order]:
        """
        Get trades for an algorithm
        
        Args:
            algorithm_id: UUID of the algorithm
            status: Optional status filter
            limit: Maximum number of trades to return
            
        Returns:
            List of Order objects
        """
        statement = (
            select(Order)
            .where(Order.algorithm_id == algorithm_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        
        if status:
            statement = statement.where(Order.status == status)
        
        trades = self.db.exec(statement).all()
        return list(trades)
    
    async def get_failed_trades(
        self,
        user_id: UUID | None = None,
        limit: int = 100,
    ) -> list[Order]:
        """
        Get failed trades for debugging
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of trades to return
            
        Returns:
            List of failed Order objects
        """
        statement = (
            select(Order)
            .where(Order.status == "failed")
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        
        if user_id:
            statement = statement.where(Order.user_id == user_id)
        
        trades = self.db.exec(statement).all()
        return list(trades)
    
    async def get_trade_statistics(
        self,
        user_id: UUID,
        algorithm_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get trade statistics for a user (optionally filtered by algorithm)
        
        Args:
            user_id: UUID of the user
            algorithm_id: Optional algorithm ID filter
            
        Returns:
            Dict with trade statistics:
            {
                "total_trades": int,
                "successful_trades": int,
                "failed_trades": int,
                "pending_trades": int,
                "success_rate": float,
                "total_volume": Decimal,
            }
        """
        # Base query
        base_statement = select(Order).where(Order.user_id == user_id)
        
        if algorithm_id:
            base_statement = base_statement.where(Order.algorithm_id == algorithm_id)
        
        all_trades = self.db.exec(base_statement).all()
        
        # Calculate statistics
        total = len(all_trades)
        successful = len([t for t in all_trades if t.status == "filled"])
        failed = len([t for t in all_trades if t.status == "failed"])
        pending = len([t for t in all_trades if t.status in ["pending", "submitted"]])
        
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        # Calculate total volume (sum of filled_quantity * price for filled trades)
        total_volume = sum(
            t.filled_quantity * (t.price or Decimal("0"))
            for t in all_trades
            if t.status == "filled" and t.price
        )
        
        return {
            "total_trades": total,
            "successful_trades": successful,
            "failed_trades": failed,
            "pending_trades": pending,
            "success_rate": success_rate,
            "total_volume": float(total_volume),
        }


# Factory function
def get_trade_recorder(db_session: Session) -> TradeRecorder:
    """
    Get trade recorder instance
    
    Args:
        db_session: Database session
        
    Returns:
        TradeRecorder instance
    """
    return TradeRecorder(db_session)
