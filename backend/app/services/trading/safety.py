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

import redis.asyncio as redis
from sqlmodel import Session, func, select

from app.models import Order, Position, User, AuditLog, RiskRule
from app import crud_risk
from app.core.config import settings

logger = logging.getLogger(__name__)


class SafetyViolation(Exception):
    """Raised when a safety check fails"""
    pass


class TradingSafetyManager:
    """
    Manages trading safety mechanisms and risk controls
    
    Features:
    - Maximum position size limits (Dynamic via RiskRules)
    - Kill Switch (Redis-backed for speed)
    - Audit Logging
    """
    
    def __init__(
        self,
        session: Session,
        max_position_pct: Decimal = Decimal('0.20'),  # 20% of portfolio per position (Fallback)
        max_daily_loss_pct: Decimal = Decimal('0.05'),  # 5% daily loss limit (Fallback)
        max_algorithm_exposure_pct: Decimal = Decimal('0.30'),  # 30% per algorithm (Fallback)
    ):
        self.session = session
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_algorithm_exposure_pct = max_algorithm_exposure_pct
        self._emergency_stop = False
        self.redis_client: redis.Redis | None = None
    
    async def connect(self) -> None:
        """Connect to Redis"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None

    def _log_audit(
        self,
        action: str,
        details: dict[str, Any],
        severity: str = "INFO",
        actor_id: UUID | None = None
    ) -> None:
        """
        Create an immutable audit log entry (Risk Management Layer)
        Adapts internal call to database model (AuditLog)
        """
        try:
            log_entry = AuditLog(
                event_type=action,
                details=details,
                severity=severity.lower(),
                user_id=actor_id
            )
            self.session.add(log_entry)
            self.session.commit()
            logger.info(f"Audit Log: {action} - {severity}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
                                                                        
    async def activate_emergency_stop(self, actor_id: UUID | None = None) -> None:
        """
        Activate emergency stop - prevents all new trades
        """
        if not self.redis_client:
            await self.connect()
        
        await self.redis_client.set("omc:emergency_stop", "true")
        self._emergency_stop = True 
        
        self._log_audit(
            action="EMERGENCY_STOP_ACTIVATED",
            details={"timestamp": str(datetime.now(timezone.utc)), "source": "redis"},
            severity="CRITICAL",
            actor_id=actor_id
        )
        logger.critical("EMERGENCY STOP ACTIVATED (Redis) - All trading halted")
        
        # Also sync to DB SystemSetting for redundancy (Track A legacy)
        try:
            crud_risk.set_system_setting(
                session=self.session, 
                key="kill_switch", 
                value={"active": True},
                description="Emergency Stop Activated via SafetyManager (Synced from Redis)"
            )
        except Exception:
            pass # Ignore DB sync errors if Redis works

    async def clear_emergency_stop(self, actor_id: UUID | None = None) -> None:
        """Clear emergency stop and resume trading"""
        if not self.redis_client:
            await self.connect()
            
        await self.redis_client.delete("omc:emergency_stop")
        self._emergency_stop = False
        
        self._log_audit(
            action="EMERGENCY_STOP_CLEARED",
            details={"timestamp": str(datetime.now(timezone.utc)), "source": "redis"},
            severity="WARNING",
            actor_id=actor_id
        )
        logger.warning("Emergency stop cleared (Redis) - Trading resumed")
        
        # Sync DB
        try:
            crud_risk.set_system_setting(
                session=self.session, 
                key="kill_switch", 
                value={"active": False},
                description="Emergency Stop Cleared via SafetyManager (Synced from Redis)"
            )
        except Exception:
            pass
    
    async def is_emergency_stopped(self) -> bool:
        """Check if emergency stop is active (Checks Redis)"""
        if not self.redis_client:
            await self.connect()
            
        status = await self.redis_client.get("omc:emergency_stop")
        return status == "true"
    
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
        """
        try:
            # Check emergency stop
            if await self.is_emergency_stopped():
                # Log rejection
                self._log_audit(
                    action="TRADE_REJECTED",
                    details={"reason": "kill_switch_active", "user_id": str(user_id)},
                    severity="ERROR",
                    actor_id=user_id # system rejection
                )
                raise SafetyViolation("Emergency stop is active - trading is halted")
                                                                                    
            # Get user
            user = self.session.get(User, user_id)
            if not user:
                raise SafetyViolation(f"User {user_id} not found")
            
            # Calculate trade value
            trade_value = quantity * estimated_price
            
            # Check position size limit (for buy orders)
            if side == 'buy':
                await self._check_position_size_limit(user_id, coin_type, trade_value)
            
            # Check daily loss limit
            await self._check_daily_loss_limit(user_id)
            
            # Check algorithm exposure limit (if algorithmic trade)
            if algorithm_id:
                await self._check_algorithm_exposure_limit(user_id, algorithm_id, trade_value)
            
            # All checks passed
            self._log_audit(
                action="TRADE_APPROVED",
                details={
                    "user_id": str(user_id),
                    "coin": coin_type,
                    "side": side,
                    "quantity": float(quantity),
                    "estimated_price": float(estimated_price),
                    "trade_value": float(trade_value),
                    "algorithm_id": str(algorithm_id) if algorithm_id else None
                },
                severity="INFO",
                actor_id=user_id
            )
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
        except SafetyViolation as e:
            self._log_audit(
                action="TRADE_REJECTED",
                details={
                    "user_id": str(user_id),
                    "coin": coin_type,
                    "side": side,
                    "quantity": float(quantity),
                    "reason": str(e),
                    "algorithm_id": str(algorithm_id) if algorithm_id else None
                },
                severity="WARNING",
                actor_id=user_id
            )
            raise e
    
    async def _check_position_size_limit(
        self,
        user_id: UUID,
        coin_type: str,
        trade_value: Decimal
    ) -> None:
        """
        Check that position size won't exceed limits
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

        # --- Dynamic Risk Rule Check (Merged from Track A) ---
        active_rules = self.session.exec(
            select(RiskRule).where(
                RiskRule.is_active == True, 
                RiskRule.rule_type == "max_position_size"
            )
        ).all()
        
        for rule in active_rules:
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
        """Check that daily losses haven't exceeded limit"""
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
        
        portfolio_value = self._get_portfolio_value(user_id)
        
        if portfolio_value == 0:
            logger.info(f"User {user_id} has no portfolio, skipping daily loss check")
            return
        
        max_loss = portfolio_value * self.max_daily_loss_pct
        
        if daily_pnl < -max_loss:
            raise SafetyViolation(
                f"Daily loss limit exceeded. Loss: {abs(daily_pnl):.2f} AUD, Limit: {max_loss:.2f} AUD"
            )
    
    async def _check_algorithm_exposure_limit(self, user_id: UUID, algorithm_id: UUID, trade_value: Decimal) -> None:
        """Check that algorithm exposure won't exceed limits"""
        portfolio_value = self._get_portfolio_value(user_id)
        
        if portfolio_value == 0:
            logger.info(f"User {user_id} has no portfolio, allowing initial algorithmic trade")
            return
        
        order_statement = select(func.sum(Order.filled_quantity * Order.price)).where(
            Order.user_id == user_id,
            Order.algorithm_id == algorithm_id,
            Order.status == 'filled',
            Order.side == 'buy'
        )
        algorithm_exposure = self.session.exec(order_statement).first() or Decimal('0')
        new_exposure = algorithm_exposure + trade_value
        max_exposure = portfolio_value * self.max_algorithm_exposure_pct
        
        if new_exposure > max_exposure:
            raise SafetyViolation(
                f"Algorithm exposure limit exceeded. New exposure: {new_exposure:.2f} AUD, Limit: {max_exposure:.2f} AUD"
            )

    def _get_portfolio_value(self, user_id: UUID) -> Decimal:
        """Calculate total portfolio value for a user"""
        statement = select(Position).where(Position.user_id == user_id)
        positions = self.session.exec(statement).all()
        return sum(pos.total_cost for pos in positions)
    
    def get_safety_status(self, user_id: UUID) -> dict[str, Any]:
        """Get current safety status for a user"""
        portfolio_value = self._get_portfolio_value(user_id)
        
        # Get today's P&L (simplified duplication of logic above)
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
    global _safety_manager
    if _safety_manager is None:
        _safety_manager = TradingSafetyManager(session)
    return _safety_manager
