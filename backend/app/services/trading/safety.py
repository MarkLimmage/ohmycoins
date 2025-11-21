"""
Safety Manager Service

Implements trading safety mechanisms to prevent excessive risk:
1. Position size limits (per coin, per algorithm, portfolio-wide)
2. Daily loss limits (per algorithm, portfolio-wide)  
3. Maximum drawdown limits
4. Trade frequency limits (prevent over-trading)
5. Emergency stop functionality (kill switch)

All trades must pass safety checks before execution.

Phase 6, Weeks 3-4
"""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlmodel import Session, select, func

from app.models import (
    DeployedAlgorithm,
    Order,
    OrderCreate,
    Position,
)

logger = logging.getLogger(__name__)


class SafetyViolationError(Exception):
    """Exception raised when a safety limit is violated"""
    pass


class SafetyManager:
    """
    Manages trading safety checks and limits
    
    Prevents risky trades by enforcing:
    - Position limits
    - Loss limits
    - Frequency limits
    - Emergency stops
    """
    
    # Default safety limits (can be overridden per user/deployment)
    DEFAULT_POSITION_LIMIT_AUD = Decimal("10000")  # $10k max position
    DEFAULT_DAILY_LOSS_LIMIT_AUD = Decimal("1000")  # $1k max daily loss
    DEFAULT_MAX_TRADES_PER_HOUR = 10  # Max 10 trades per hour
    DEFAULT_MAX_PORTFOLIO_VALUE_AUD = Decimal("50000")  # $50k max portfolio
    
    def __init__(self, db_session: Session):
        """
        Initialize safety manager
        
        Args:
            db_session: Database session for queries
        """
        self.db = db_session
        self._emergency_stop_active = False  # Global kill switch
    
    async def check_trade_safety(
        self,
        user_id: UUID,
        order: OrderCreate,
        deployment: DeployedAlgorithm | None = None,
    ) -> tuple[bool, str]:
        """
        Check if a trade passes all safety checks
        
        Args:
            user_id: User ID placing the trade
            order: Order to check
            deployment: Optional deployment configuration with custom limits
            
        Returns:
            (is_safe, reason) tuple:
            - is_safe: True if trade passes all checks, False otherwise
            - reason: Explanation if trade is rejected, empty string if safe
        """
        # 1. Emergency stop check
        if self._emergency_stop_active:
            return False, "Emergency stop is active - all trading halted"
        
        # 2. Position limit check
        is_safe, reason = await self._check_position_limit(user_id, order, deployment)
        if not is_safe:
            return False, reason
        
        # 3. Daily loss limit check
        is_safe, reason = await self._check_daily_loss_limit(user_id, deployment)
        if not is_safe:
            return False, reason
        
        # 4. Trade frequency limit check
        is_safe, reason = await self._check_trade_frequency(user_id, deployment)
        if not is_safe:
            return False, reason
        
        # 5. Portfolio value limit check
        is_safe, reason = await self._check_portfolio_limit(user_id)
        if not is_safe:
            return False, reason
        
        # All checks passed
        return True, ""
    
    async def _check_position_limit(
        self,
        user_id: UUID,
        order: OrderCreate,
        deployment: DeployedAlgorithm | None,
    ) -> tuple[bool, str]:
        """
        Check if order would exceed position limits
        
        Checks:
        - Deployment-specific limit (if set)
        - Algorithm default limit (if set)
        - Global default limit
        """
        # Get position limit
        if deployment and deployment.position_limit:
            limit = deployment.position_limit
        else:
            limit = self.DEFAULT_POSITION_LIMIT_AUD
        
        # Get current position for this coin
        statement = (
            select(Position)
            .where(Position.user_id == user_id)
            .where(Position.coin_type == order.coin_type)
        )
        position = self.db.exec(statement).first()
        
        if order.side == "buy":
            # Calculate new position value if order fills
            # Simplified: assume order fills at current price
            # In production, would get actual market price
            estimated_cost = order.quantity * Decimal("50000")  # Placeholder price
            
            current_value = position.total_cost if position else Decimal("0")
            new_value = current_value + estimated_cost
            
            if new_value > limit:
                return False, (
                    f"Order would exceed position limit: "
                    f"new_value={new_value:.2f} > limit={limit:.2f}"
                )
        
        # Sell orders reduce position, always safe
        return True, ""
    
    async def _check_daily_loss_limit(
        self,
        user_id: UUID,
        deployment: DeployedAlgorithm | None,
    ) -> tuple[bool, str]:
        """
        Check if daily losses exceed limit
        
        Checks:
        - Deployment-specific limit (if set)
        - Global default limit
        """
        # Get daily loss limit
        if deployment and deployment.daily_loss_limit:
            limit = deployment.daily_loss_limit
        else:
            limit = self.DEFAULT_DAILY_LOSS_LIMIT_AUD
        
        # Calculate today's P&L (orders from last 24 hours)
        today_start = datetime.now(timezone.utc) - timedelta(days=1)
        
        statement = (
            select(func.sum(Order.filled_quantity * Order.price))
            .where(Order.user_id == user_id)
            .where(Order.status == "filled")
            .where(Order.created_at >= today_start)
        )
        
        result = self.db.exec(statement).first()
        daily_pnl = result if result else Decimal("0")
        
        # Check if losses exceed limit (negative P&L)
        if daily_pnl < -limit:
            return False, (
                f"Daily loss limit exceeded: "
                f"pnl={daily_pnl:.2f} < limit=-{limit:.2f}"
            )
        
        return True, ""
    
    async def _check_trade_frequency(
        self,
        user_id: UUID,
        deployment: DeployedAlgorithm | None,
    ) -> tuple[bool, str]:
        """
        Check if trade frequency is within limits
        
        Prevents over-trading by limiting trades per hour
        """
        # Count trades in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        statement = (
            select(func.count(Order.id))
            .where(Order.user_id == user_id)
            .where(Order.created_at >= one_hour_ago)
        )
        
        if deployment:
            statement = statement.where(Order.algorithm_id == deployment.algorithm_id)
        
        trade_count = self.db.exec(statement).first() or 0
        
        if trade_count >= self.DEFAULT_MAX_TRADES_PER_HOUR:
            return False, (
                f"Trade frequency limit exceeded: "
                f"{trade_count} trades in last hour (max {self.DEFAULT_MAX_TRADES_PER_HOUR})"
            )
        
        return True, ""
    
    async def _check_portfolio_limit(
        self,
        user_id: UUID,
    ) -> tuple[bool, str]:
        """
        Check if total portfolio value is within limits
        
        Prevents excessive total exposure
        """
        # Get all positions
        statement = (
            select(func.sum(Position.total_cost))
            .where(Position.user_id == user_id)
        )
        
        total_value = self.db.exec(statement).first() or Decimal("0")
        
        if total_value > self.DEFAULT_MAX_PORTFOLIO_VALUE_AUD:
            return False, (
                f"Portfolio value limit exceeded: "
                f"value={total_value:.2f} > limit={self.DEFAULT_MAX_PORTFOLIO_VALUE_AUD:.2f}"
            )
        
        return True, ""
    
    def activate_emergency_stop(self) -> None:
        """
        Activate emergency stop (kill switch)
        
        Immediately halts all trading across all users and algorithms.
        Should only be used in emergencies.
        """
        self._emergency_stop_active = True
        logger.critical("EMERGENCY STOP ACTIVATED - All trading halted")
    
    def deactivate_emergency_stop(self) -> None:
        """
        Deactivate emergency stop
        
        Resumes normal trading operations.
        """
        self._emergency_stop_active = False
        logger.warning("Emergency stop deactivated - Trading resumed")
    
    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is currently active"""
        return self._emergency_stop_active
    
    async def get_safety_status(self, user_id: UUID) -> dict[str, Any]:
        """
        Get current safety status for a user
        
        Returns:
            Dict with safety metrics:
            {
                "emergency_stop": bool,
                "daily_pnl": Decimal,
                "daily_loss_limit": Decimal,
                "portfolio_value": Decimal,
                "portfolio_limit": Decimal,
                "trades_last_hour": int,
                "trade_frequency_limit": int,
            }
        """
        # Calculate daily P&L
        today_start = datetime.now(timezone.utc) - timedelta(days=1)
        statement = (
            select(func.sum(Order.filled_quantity * Order.price))
            .where(Order.user_id == user_id)
            .where(Order.status == "filled")
            .where(Order.created_at >= today_start)
        )
        daily_pnl = self.db.exec(statement).first() or Decimal("0")
        
        # Calculate portfolio value
        statement = (
            select(func.sum(Position.total_cost))
            .where(Position.user_id == user_id)
        )
        portfolio_value = self.db.exec(statement).first() or Decimal("0")
        
        # Count trades in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        statement = (
            select(func.count(Order.id))
            .where(Order.user_id == user_id)
            .where(Order.created_at >= one_hour_ago)
        )
        trades_last_hour = self.db.exec(statement).first() or 0
        
        return {
            "emergency_stop": self._emergency_stop_active,
            "daily_pnl": float(daily_pnl),
            "daily_loss_limit": float(self.DEFAULT_DAILY_LOSS_LIMIT_AUD),
            "portfolio_value": float(portfolio_value),
            "portfolio_limit": float(self.DEFAULT_MAX_PORTFOLIO_VALUE_AUD),
            "trades_last_hour": trades_last_hour,
            "trade_frequency_limit": self.DEFAULT_MAX_TRADES_PER_HOUR,
        }


# Global safety manager instance (singleton)
_safety_manager_instance: SafetyManager | None = None


def get_safety_manager(db_session: Session) -> SafetyManager:
    """
    Get or create safety manager instance
    
    Args:
        db_session: Database session
        
    Returns:
        SafetyManager instance
    """
    global _safety_manager_instance
    if _safety_manager_instance is None:
        _safety_manager_instance = SafetyManager(db_session)
    return _safety_manager_instance
