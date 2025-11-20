"""
Tests for Position Manager
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.trading.positions import PositionManager, get_position_manager
from app.models import Position


class TestPositionManager:
    """Test suite for PositionManager"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = MagicMock()
        session.exec = MagicMock()
        return session
    
    @pytest.fixture
    def manager(self, mock_session):
        """Create a position manager instance"""
        return PositionManager(mock_session)
    
    @pytest.fixture
    def sample_position(self):
        """Create a sample position"""
        return Position(
            id=uuid4(),
            user_id=uuid4(),
            coin_type='BTC',
            quantity=Decimal('0.5'),
            average_price=Decimal('50000.00'),
            total_cost=Decimal('25000.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def test_get_position(self, manager, mock_session, sample_position):
        """Test getting a specific position"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_position
        mock_session.exec.return_value = mock_result
        
        result = manager.get_position(sample_position.user_id, 'BTC')
        
        assert result == sample_position
        assert mock_session.exec.called
    
    def test_get_position_not_found(self, manager, mock_session):
        """Test getting a non-existent position"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        result = manager.get_position(uuid4(), 'BTC')
        
        assert result is None
    
    def test_get_all_positions(self, manager, mock_session, sample_position):
        """Test getting all positions for a user"""
        position2 = Position(
            id=uuid4(),
            user_id=sample_position.user_id,
            coin_type='ETH',
            quantity=Decimal('2.0'),
            average_price=Decimal('3000.00'),
            total_cost=Decimal('6000.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_position, position2]
        mock_session.exec.return_value = mock_result
        
        result = manager.get_all_positions(sample_position.user_id)
        
        assert len(result) == 2
        assert sample_position in result
        assert position2 in result
    
    @pytest.mark.asyncio
    async def test_get_position_with_value(self, manager, mock_session, sample_position):
        """Test getting position with current value"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_position
        mock_session.exec.return_value = mock_result
        
        # Mock Coinspot client response
        mock_balance_data = {
            'status': 'ok',
            'balance': '0.5',
            'audvalue': '26000.00'
        }
        
        with patch('app.services.trading.positions.CoinspotTradingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_balance = AsyncMock(return_value=mock_balance_data)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client
            
            result = await manager.get_position_with_value(
                sample_position.user_id,
                'BTC',
                'api_key',
                'api_secret'
            )
            
            assert result is not None
            assert result.coin_type == 'BTC'
            assert result.quantity == Decimal('0.5')
            assert result.current_value == Decimal('26000.00')
            assert result.unrealized_pnl == Decimal('1000.00')  # 26000 - 25000
    
    @pytest.mark.asyncio
    async def test_get_all_positions_with_values(self, manager, mock_session, sample_position):
        """Test getting all positions with current values"""
        position2 = Position(
            id=uuid4(),
            user_id=sample_position.user_id,
            coin_type='ETH',
            quantity=Decimal('2.0'),
            average_price=Decimal('3000.00'),
            total_cost=Decimal('6000.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_position, position2]
        mock_session.exec.return_value = mock_result
        
        # Mock Coinspot client response
        mock_balances_data = {
            'status': 'ok',
            'balances': {
                'BTC': {'balance': '0.5', 'audvalue': '26000.00'},
                'ETH': {'balance': '2.0', 'audvalue': '6500.00'}
            }
        }
        
        with patch('app.services.trading.positions.CoinspotTradingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_balances = AsyncMock(return_value=mock_balances_data)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client
            
            result = await manager.get_all_positions_with_values(
                sample_position.user_id,
                'api_key',
                'api_secret'
            )
            
            assert len(result) == 2
            
            # Check BTC position
            btc_pos = next(p for p in result if p.coin_type == 'BTC')
            assert btc_pos.current_value == Decimal('26000.00')
            assert btc_pos.unrealized_pnl == Decimal('1000.00')
            
            # Check ETH position
            eth_pos = next(p for p in result if p.coin_type == 'ETH')
            assert eth_pos.current_value == Decimal('6500.00')
            assert eth_pos.unrealized_pnl == Decimal('500.00')
    
    def test_get_portfolio_summary(self, manager, mock_session, sample_position):
        """Test getting portfolio summary"""
        position2 = Position(
            id=uuid4(),
            user_id=sample_position.user_id,
            coin_type='ETH',
            quantity=Decimal('2.0'),
            average_price=Decimal('3000.00'),
            total_cost=Decimal('6000.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_position, position2]
        mock_session.exec.return_value = mock_result
        
        result = manager.get_portfolio_summary(sample_position.user_id)
        
        assert result['user_id'] == sample_position.user_id
        assert result['total_positions'] == 2
        assert result['total_cost'] == Decimal('31000.00')  # 25000 + 6000
        assert 'BTC' in result['coins']
        assert 'ETH' in result['coins']
    
    @pytest.mark.asyncio
    async def test_get_portfolio_value(self, manager, mock_session, sample_position):
        """Test getting complete portfolio value and P&L"""
        position2 = Position(
            id=uuid4(),
            user_id=sample_position.user_id,
            coin_type='ETH',
            quantity=Decimal('2.0'),
            average_price=Decimal('3000.00'),
            total_cost=Decimal('6000.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_position, position2]
        mock_session.exec.return_value = mock_result
        
        # Mock Coinspot client response
        mock_balances_data = {
            'status': 'ok',
            'balances': {
                'BTC': {'balance': '0.5', 'audvalue': '26000.00'},
                'ETH': {'balance': '2.0', 'audvalue': '6500.00'}
            }
        }
        
        with patch('app.services.trading.positions.CoinspotTradingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_balances = AsyncMock(return_value=mock_balances_data)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client_class.return_value = mock_client
            
            result = await manager.get_portfolio_value(
                sample_position.user_id,
                'api_key',
                'api_secret'
            )
            
            assert result['user_id'] == sample_position.user_id
            assert result['total_positions'] == 2
            assert result['total_cost'] == Decimal('31000.00')
            assert result['total_value'] == Decimal('32500.00')  # 26000 + 6500
            assert result['total_unrealized_pnl'] == Decimal('1500.00')  # 1000 + 500
            # Return percentage: (1500 / 31000) * 100 = 4.84%
            assert result['return_percentage'] > Decimal('4.8')
            assert result['return_percentage'] < Decimal('4.9')


class TestGetPositionManager:
    """Test the get_position_manager factory function"""
    
    def test_get_position_manager(self):
        """Test factory function returns PositionManager instance"""
        mock_session = MagicMock()
        manager = get_position_manager(mock_session)
        
        assert isinstance(manager, PositionManager)
        assert manager.session == mock_session
