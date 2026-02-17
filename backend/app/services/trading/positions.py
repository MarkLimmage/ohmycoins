# mypy: ignore-errors
"""
Position Management Service

This module provides position tracking and portfolio management functionality.
"""
import logging
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session, select

from app.models import Position, PositionPublic
from app.services.trading.client import CoinspotTradingClient

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Manages trading positions and portfolio tracking
    
    Features:
    - Position queries by user and coin
    - Portfolio value calculation
    - Unrealized P&L calculation
    """

    def __init__(self, session: Session):
        """
        Initialize position manager
        
        Args:
            session: Database session
        """
        self.session = session

    def get_position(self, user_id: UUID, coin_type: str) -> Position | None:
        """
        Get position for a specific user and coin
        
        Args:
            user_id: User UUID
            coin_type: Cryptocurrency symbol (e.g., 'BTC')
            
        Returns:
            Position or None if not found
        """
        statement = select(Position).where(
            Position.user_id == user_id,
            Position.coin_type == coin_type
        )
        return self.session.exec(statement).first()

    def get_all_positions(self, user_id: UUID) -> list[Position]:
        """
        Get all positions for a user
        
        Args:
            user_id: User UUID
            
        Returns:
            List of positions
        """
        statement = select(Position).where(Position.user_id == user_id)
        return list(self.session.exec(statement).all())

    async def get_position_with_value(
        self,
        user_id: UUID,
        coin_type: str,
        api_key: str,
        api_secret: str
    ) -> PositionPublic | None:
        """
        Get position with current market value and unrealized P&L
        
        Args:
            user_id: User UUID
            coin_type: Cryptocurrency symbol
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            
        Returns:
            PositionPublic with calculated values or None
        """
        position = self.get_position(user_id, coin_type)
        if not position:
            return None

        # Get current price from Coinspot
        async with CoinspotTradingClient(api_key, api_secret) as client:
            balance_data = await client.get_balance(coin_type)

        # Calculate current value (assuming audvalue is provided)
        current_value = Decimal(str(balance_data.get('audvalue', '0')))

        # Calculate unrealized P&L
        unrealized_pnl = current_value - position.total_cost

        return PositionPublic(
            id=position.id,
            user_id=position.user_id,
            coin_type=position.coin_type,
            quantity=position.quantity,
            average_price=position.average_price,
            total_cost=position.total_cost,
            created_at=position.created_at,
            updated_at=position.updated_at,
            current_value=current_value,
            unrealized_pnl=unrealized_pnl
        )

    async def get_all_positions_with_values(
        self,
        user_id: UUID,
        api_key: str,
        api_secret: str
    ) -> list[PositionPublic]:
        """
        Get all positions with current market values and unrealized P&L
        
        Args:
            user_id: User UUID
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            
        Returns:
            List of PositionPublic with calculated values
        """
        positions = self.get_all_positions(user_id)
        result = []

        async with CoinspotTradingClient(api_key, api_secret) as client:
            # Get all balances at once for efficiency
            balances_data = await client.get_balances()
            balances = balances_data.get('balances', {})

            for position in positions:
                # Get balance data for this coin
                balance = balances.get(position.coin_type, {})
                current_value = Decimal(str(balance.get('audvalue', '0')))

                # Calculate unrealized P&L
                unrealized_pnl = current_value - position.total_cost

                result.append(PositionPublic(
                    id=position.id,
                    user_id=position.user_id,
                    coin_type=position.coin_type,
                    quantity=position.quantity,
                    average_price=position.average_price,
                    total_cost=position.total_cost,
                    created_at=position.created_at,
                    updated_at=position.updated_at,
                    current_value=current_value,
                    unrealized_pnl=unrealized_pnl
                ))

        return result

    def get_portfolio_summary(self, user_id: UUID) -> dict:
        """
        Get portfolio summary for a user
        
        Args:
            user_id: User UUID
            
        Returns:
            Dictionary with portfolio statistics
        """
        positions = self.get_all_positions(user_id)

        total_positions = len(positions)
        total_cost = sum(p.total_cost for p in positions)

        # Get unique coins
        coins = list(set(p.coin_type for p in positions))

        return {
            'user_id': user_id,
            'total_positions': total_positions,
            'total_cost': total_cost,
            'coins': coins
        }

    async def get_portfolio_value(
        self,
        user_id: UUID,
        api_key: str,
        api_secret: str
    ) -> dict:
        """
        Get complete portfolio value and P&L
        
        Args:
            user_id: User UUID
            api_key: Coinspot API key
            api_secret: Coinspot API secret
            
        Returns:
            Dictionary with portfolio value and P&L
        """
        positions = await self.get_all_positions_with_values(user_id, api_key, api_secret)

        total_cost = sum(p.total_cost for p in positions)
        total_value = sum(p.current_value for p in positions if p.current_value)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions if p.unrealized_pnl)

        # Calculate return percentage
        return_pct = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else Decimal('0')

        return {
            'user_id': user_id,
            'total_positions': len(positions),
            'total_cost': total_cost,
            'total_value': total_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'return_percentage': return_pct,
            'positions': positions
        }


def get_position_manager(session: Session) -> PositionManager:
    """
    Get a position manager instance
    
    Args:
        session: Database session
        
    Returns:
        PositionManager instance
    """
    return PositionManager(session)
