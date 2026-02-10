"""
Safety Mechanisms for Trading System

This module provides safety checks and limits to prevent excessive losses
and manage risk in the automated trading system.
"""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlmodel import Session, func, select

from app.models import Order, Position, User, RiskRule
from app import crud_risk

logger = logging.getLogger(__name__)


class SafetyViolation(Exception):
    """Raised when a safety check fails"""
    pass


class TradingSafetyManager:
    """
    Manages trading safety mechanisms and risk controls
    
    Features:
    - Maximum position size limits (Dynamic via RiskRules)
    - Kill Switch (SystemSetting)
    - Audit Logging
    """
    
    def __init__(
        self,
        session: Session,
        max_position_pct: Decimal = Decimal('0.20'),  # 20% of portfolio per position (Fallback)
        max_daily_loss_pct: Decimal = Decimal('0.05'),  # 5% daily loss limit (Fallback)
        max_algorithm_exposure_pct: Decimal = Decimal('0.30'),  # 30% per algorithm (Fallback)
    ):
        """
        Initialize safety manager
        
        Args:
            session: Database session
            max_position_pct: Maximum position size as percentage of portfolio (default: 20%)
            max_daily_loss_pct: Maximum daily loss as percentage of portfolio (default: 5%)
            max_algorithm_exposure_pct: Maximum exposure per algorithm (default: 30%)
        """
        self.session = session
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_algorithm_exposure_pct = max_algorithm_exposure_pct
        self._emergency_stop = False
    
    def activate_emergency_stop(self) -> None:
        """
        Activate emergency stop - prevents all new trades
        """
        self._emergency_stop = True
        logger.critical("EMERGENCY STOP ACTIVATED - All trading halted")
        crud_risk.set_system_setting(
            session=self.session, 
            key="kill_switch", 
            value={"active": True},
            description="Emergency Stop Activated via SafetyManager"
        )
        crud_risk.create_audit_log(
            session=self.session,
            audit_log_create=crud_risk.AuditLogCreate(
                event_type="kill_switch_activate",
                severity="critical",
                details={"source": "safety_manager"},
                performed_by="system"
            )
        )
    
    def clear_emergency_stop(self) -> None:
        """Clear emergency stop and resume trading"""
        self._emergency_stop = False
        logger.warning("Emergency stop cleared - Trading resumed")
        crud_risk.set_system_setting(
            session=self.session, 
            key="kill_switch", 
            value={"active": False},
            description="Emergency Stop Cleared via SafetyManager"
        )
        crud_risk.create_audit_log(
            session=self.session,
            audit_log_create=crud_risk.AuditLogCreate(
                event_type="kill_switch_deactivate",
                severity="warning",
                details={"source": "safety_manager"},
                performed_by="system"
            )
        )
    
    def is_emergency_stopped(self) -> bool:
        """Check if emergency stop is active"""
        # Check caching or DB
        setting = crud_risk.get_system_setting(session=self.session, key="kill_switch")
        if setting and setting.value.get("active", False):
            return True
        return self._emergency_stop
    
    async def validate_trade(
        self,
        user_id: UUID,
        coin_type: str,
        side: str,
        quantity: Decimal,
        estimated_price: Decimal,
        algorithm_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Validate a trade against all safety mechanisms
        
        Args:
            user_id: User executing the trade
            coin_type: Cryptocurrency being traded
            side: 'buy' or 'sell'
            quantity: Trade quantity
            estimated_price: Estimated execution price
            algorithm_id: Algorithm ID if automated trade
            
        Returns:
            Dictionary with validation results
            
        Raises:
            SafetyViolation: If any safety check fails
        """
        # Check emergency stop
        if self.is_emergency_stopped():
            crud_risk.create_audit_log(
                session=self.session,
                audit_log_create=crud_risk.AuditLogCreate(
                    event_type="trade_rejected",
                    severity="error",
                    details={"reason": "kill_switch_active", "user_id": str(user_id)},
                    performed_by="system"
                )
            )
            raise SafetyViolation("Emergency stop is active - trading is halted")
        
        # Get user
        user = self.session.get(User, user_id)
        if not user:
            raise SafetyViolation(f"User {user_id} not found")
        
        # Calculate trade value
        trade_value = quantity * estimated_price
        
        try:
            # Check position size limit (for buy orders)
            if side == 'buy':
                await self._check_position_size_limit(user_id, coin_type, trade_value)
            
            # Check daily loss limit
            await self._check_daily_loss_limit(user_id)
            
            # Check algorithm exposure limit (if algorithmic trade)
            if algorithm_id:
                await self._check_algorithm_exposure_limit(user_id, algorithm_id, trade_value)

        except SafetyViolation as e:
            crud_risk.create_audit_log(
                session=self.session,
                audit_log_create=crud_risk.AuditLogCreate(
                    event_type="trade_rejected",
                    severity="warning",
                    details={
                        "reason": str(e),
                        "user_id": str(user_id), 
                        "coin_type": coin_type, 
                        "amount": float(quantity),
                        "value": float(trade_value)
                    },
                    performed_by="system"
                )
            )
            raise e
        
        # All checks passed
        logger.info(f"Trade validation passed for user {user_id}: {side} {quantity} {coin_type}")
        
        return {
            'valid': True,
            'trade_value': trade_value,
            'checks_passed': [
                'emergency_stop',
                'position_size',
                'daily_loss',
                'algorithm_exposure' if algorithm_id else 'manual_trade'
            ]
        }
    
    async def _check_position_size_limit(
        self,
        user_id: UUID,
        coin_type: str,
        trade_value: Decimal
    ) -> None:
        """
        Check that position size won't exceed limits
        
        Args:
            user_id: User ID
            coin_type: Coin being traded
            trade_value: Value of the trade
            
        Raises:
            SafetyViolation: If position size limit would be exceeded
        """
        # Calculate total portfolio value
        portfolio_value = self._get_portfolio_value(user_id)
        
        # Get current position value for this coin
        statement = select(Position).where(
            Position.user_id == user_id,
            Position.coin_type == coin_type
        )
        position = self.session.exec(statement).first()
        
        current_position_value = Decimal('0')
        if position:
            current_position_value = position.total_cost
        
        # Calculate new position value after trade
        new_position_value = current_position_value + trade_value

        # --- Dynamic Risk Rule Check ---
        active_rules = self.session.exec(
            select(RiskRule).where(
                RiskRule.is_active == True, 
                RiskRule.rule_type == "max_position_size"
            )
        ).all()
        
        for rule in active_rules:
            # Check for hard value limit (e.g., max 5000 AUD per position)
            rule_value = rule.value or {}
            
            # Check absolute value limit
            if "max_value" in rule_value:
                limit_val = Decimal(str(rule_value["max_value"]))
                if new_position_value > limit_val:
                    raise SafetyViolation(
                        f"Dynamic Risk Rule '{rule.name}' violated. "
                        f"Position {new_position_value:.2f} > Limit {limit_val:.2f}"
                    )
            
            # Check percentage limit override
            if "max_percentage" in rule_value and portfolio_value > 0:
                limit_pct = Decimal(str(rule_value["max_percentage"]))
                max_allowed = portfolio_value * limit_pct
                if new_position_value > max_allowed:
                     raise SafetyViolation(
                        f"Dynamic Risk Rule '{rule.name}' violated. "
                        f"Position {new_position_value:.2f} > {limit_pct*100}% Portfolio ({max_allowed:.2f})"
                    )

        if portfolio_value == 0:
            # No existing portfolio, allow first trade up to a reasonable amount
            # This prevents division by zero and allows initial positions
            logger.info(f"User {user_id} has no existing portfolio, allowing initial trade (Dynamic absolute limits still apply)")
            return
        max_position_value = portfolio_value * self.max_position_pct
        
        if new_position_value > max_position_value:
            raise SafetyViolation(
                f"Position size limit exceeded for {coin_type}. "
                f"New position: {new_position_value:.2f} AUD, "
                f"Limit: {max_position_value:.2f} AUD "
                f"({self.max_position_pct * 100:.0f}% of portfolio)"
            )
        
        logger.debug(
            f"Position size check passed for {coin_type}: "
            f"{new_position_value:.2f}/{max_position_value:.2f} AUD"
        )
    
    async def _check_daily_loss_limit(self, user_id: UUID) -> None:
        """
        Check that daily losses haven't exceeded limit
        
        Args:
            user_id: User ID
            
        Raises:
            SafetyViolation: If daily loss limit exceeded
        """
        # Get portfolio value at start of day
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate P&L for today
        # Get all filled orders from today
        statement = select(Order).where(
            Order.user_id == user_id,
            Order.status == 'filled',
            Order.filled_at >= today_start
        )
        today_orders = self.session.exec(statement).all()
        
        # Calculate realized P&L from today's trades
        daily_pnl = Decimal('0')
        for order in today_orders:
            if order.side == 'sell':
                # For sell orders, calculate profit/loss
                # This is simplified - full P&L calculation would track cost basis
                daily_pnl += (order.filled_quantity * order.price)
            elif order.side == 'buy':
                daily_pnl -= (order.filled_quantity * order.price)
        
        # Get current portfolio value
        portfolio_value = self._get_portfolio_value(user_id)
        
        if portfolio_value == 0:
            logger.info(f"User {user_id} has no portfolio, skipping daily loss check")
            return
        
        # Check if loss exceeds limit
        max_loss = portfolio_value * self.max_daily_loss_pct
        
        if daily_pnl < -max_loss:
            raise SafetyViolation(
                f"Daily loss limit exceeded. "
                f"Loss: {abs(daily_pnl):.2f} AUD, "
                f"Limit: {max_loss:.2f} AUD "
                f"({self.max_daily_loss_pct * 100:.0f}% of portfolio)"
            )
        
        logger.debug(
            f"Daily loss check passed: "
            f"P&L: {daily_pnl:.2f} AUD, "
            f"Limit: {max_loss:.2f} AUD"
        )
    
    async def _check_algorithm_exposure_limit(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        trade_value: Decimal
    ) -> None:
        """
        Check that algorithm exposure won't exceed limits
        
        Args:
            user_id: User ID
            algorithm_id: Algorithm ID
            trade_value: Value of the trade
            
        Raises:
            SafetyViolation: If algorithm exposure limit would be exceeded
        """
        # Get portfolio value
        portfolio_value = self._get_portfolio_value(user_id)
        
        if portfolio_value == 0:
            logger.info(f"User {user_id} has no portfolio, allowing initial algorithmic trade")
            return
        
        # Get current exposure for this algorithm
        # Sum up all open positions created by this algorithm
        statement = select(func.sum(Position.total_cost)).where(
            Position.user_id == user_id
        )
        # Note: This is simplified - ideally we'd track which algorithm created each position
        # For now, we check total algorithm exposure from orders
        
        order_statement = select(func.sum(Order.filled_quantity * Order.price)).where(
            Order.user_id == user_id,
            Order.algorithm_id == algorithm_id,
            Order.status == 'filled',
            Order.side == 'buy'
        )
        algorithm_exposure = self.session.exec(order_statement).first() or Decimal('0')
        
        # Calculate new exposure
        new_exposure = algorithm_exposure + trade_value
        
        # Check limit
        max_exposure = portfolio_value * self.max_algorithm_exposure_pct
        
        if new_exposure > max_exposure:
            raise SafetyViolation(
                f"Algorithm exposure limit exceeded. "
                f"New exposure: {new_exposure:.2f} AUD, "
                f"Limit: {max_exposure:.2f} AUD "
                f"({self.max_algorithm_exposure_pct * 100:.0f}% of portfolio)"
            )
        
        logger.debug(
            f"Algorithm exposure check passed: "
            f"{new_exposure:.2f}/{max_exposure:.2f} AUD"
        )
    
    def _get_portfolio_value(self, user_id: UUID) -> Decimal:
        """
        Calculate total portfolio value for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Total portfolio value in AUD
        """
        # Get all positions
        statement = select(Position).where(Position.user_id == user_id)
        positions = self.session.exec(statement).all()
        
        # Sum up total cost (this is the invested amount)
        # In a real system, we'd calculate current market value
        total_value = sum(pos.total_cost for pos in positions)
        
        return total_value
    
    def get_safety_status(self, user_id: UUID) -> dict[str, Any]:
        """
        Get current safety status for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with safety status information
        """
        # Get portfolio value
        portfolio_value = self._get_portfolio_value(user_id)
        
        # Get today's P&L
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        statement = select(Order).where(
            Order.user_id == user_id,
            Order.status == 'filled',
            Order.filled_at >= today_start
        )
        today_orders = self.session.exec(statement).all()
        
        daily_pnl = Decimal('0')
        for order in today_orders:
            if order.side == 'sell':
                daily_pnl += (order.filled_quantity * order.price)
            elif order.side == 'buy':
                daily_pnl -= (order.filled_quantity * order.price)
        
        return {
            'emergency_stop': self._emergency_stop,
            'portfolio_value': float(portfolio_value),
            'daily_pnl': float(daily_pnl),
            'max_daily_loss': float(portfolio_value * self.max_daily_loss_pct),
            'max_position_size': float(portfolio_value * self.max_position_pct),
            'max_algorithm_exposure': float(portfolio_value * self.max_algorithm_exposure_pct),
            'limits': {
                'max_position_pct': float(self.max_position_pct),
                'max_daily_loss_pct': float(self.max_daily_loss_pct),
                'max_algorithm_exposure_pct': float(self.max_algorithm_exposure_pct)
            }
        }


# Global instance
_safety_manager: TradingSafetyManager | None = None


def get_safety_manager(session: Session) -> TradingSafetyManager:
    """
    Get or create the global safety manager instance
    
    Args:
        session: Database session
        
    Returns:
        TradingSafetyManager instance
    """
    global _safety_manager
    if _safety_manager is None:
        _safety_manager = TradingSafetyManager(session)
    return _safety_manager
