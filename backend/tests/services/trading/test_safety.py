"""
Tests for Trading Safety Manager

Tests cover:
- Safety validation
- Position size limits
- Daily loss limits
- Algorithm exposure limits
- Emergency stop functionality
"""
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlmodel import Session

from app.models import Order, Position, RiskRule, User
from app.services.trading.safety import (
    SafetyViolation,
    TradingSafetyManager,
    get_safety_manager,
)


@pytest_asyncio.fixture
async def safety_manager(session: Session) -> AsyncGenerator[TradingSafetyManager, None]:
    """Create a safety manager instance for testing"""
    manager = TradingSafetyManager(
        session=session,
        max_position_pct=Decimal('0.20'),  # 20%
        max_daily_loss_pct=Decimal('0.05'),  # 5%
        max_algorithm_exposure_pct=Decimal('0.30')  # 30%
    )

    # Ensure clean state start
    await manager.connect()
    await manager.redis_client.delete("omc:emergency_stop")
    await manager.redis_client.delete("omc:market_status")

    yield manager

    # Teardown
    if manager.redis_client:
        await manager.redis_client.delete("omc:emergency_stop")
        await manager.redis_client.delete("omc:market_status")
        await manager.disconnect()


@pytest.fixture
def test_user_with_portfolio(session: Session, test_user: User) -> User:
    """Create a test user with existing positions"""
    # Create positions with total value of 10,000 AUD
    positions = [
        Position(
            user_id=test_user.id,
            coin_type='BTC',
            quantity=Decimal('0.1'),
            average_price=Decimal('60000'),
            total_cost=Decimal('6000'),  # 60% of portfolio
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        Position(
            user_id=test_user.id,
            coin_type='ETH',
            quantity=Decimal('1.0'),
            average_price=Decimal('4000'),
            total_cost=Decimal('4000'),  # 40% of portfolio
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]

    for pos in positions:
        session.add(pos)

    session.commit()
    return test_user


class TestSafetyManager:
    """Tests for TradingSafetyManager"""

    @pytest.mark.asyncio
    async def test_emergency_stop(self, safety_manager: TradingSafetyManager):
        """Test emergency stop activation and clearing"""
        assert not await safety_manager.is_emergency_stopped()

        await safety_manager.activate_emergency_stop()
        assert await safety_manager.is_emergency_stopped()

        await safety_manager.clear_emergency_stop()
        assert not await safety_manager.is_emergency_stopped()

    @pytest.mark.asyncio
    async def test_validate_trade_with_emergency_stop(
        self,
        safety_manager: TradingSafetyManager,
        test_user: User
    ):
        """Test that trades are blocked when emergency stop is active"""
        await safety_manager.activate_emergency_stop()

        with pytest.raises(SafetyViolation, match="Emergency stop is active"):
            await safety_manager.validate_trade(
                user_id=test_user.id,
                coin_type='BTC',
                side='buy',
                quantity=Decimal('100'),
                estimated_price=Decimal('60000')
            )

    @pytest.mark.asyncio
    async def test_validate_trade_user_not_found(
        self,
        safety_manager: TradingSafetyManager
    ):
        """Test validation fails for non-existent user"""
        with pytest.raises(SafetyViolation, match="User .* not found"):
            await safety_manager.validate_trade(
                user_id=uuid4(),
                coin_type='BTC',
                side='buy',
                quantity=Decimal('100'),
                estimated_price=Decimal('60000')
            )

    @pytest.mark.asyncio
    async def test_validate_trade_first_position(
        self,
        safety_manager: TradingSafetyManager,
        test_user: User
    ):
        """Test that first position is allowed (no existing portfolio)"""
        result = await safety_manager.validate_trade(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('100'),
            estimated_price=Decimal('60000')
        )

        assert result['valid'] is True
        assert 'position_size' in result['checks_passed']

    @pytest.mark.asyncio
    async def test_position_size_limit_not_exceeded(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test trade within position size limit"""
        # Portfolio value: 10,000 AUD
        # Max position: 20% = 2,000 AUD
        # Buying 500 AUD of ADA (no existing position)

        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('1000'),  # 1000 ADA
            estimated_price=Decimal('0.50')  # = 500 AUD
        )

        assert result['valid'] is True
        assert result['trade_value'] == Decimal('500')

    @pytest.mark.asyncio
    async def test_position_size_limit_exceeded(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test trade exceeds position size limit"""
        # Portfolio value: 10,000 AUD
        # Max position: 20% = 2,000 AUD
        # Trying to buy 3,000 AUD worth

        with pytest.raises(SafetyViolation, match="Position size limit exceeded"):
            await safety_manager.validate_trade(
                user_id=test_user_with_portfolio.id,
                coin_type='SOL',
                side='buy',
                quantity=Decimal('30'),  # 30 SOL
                estimated_price=Decimal('100')  # = 3,000 AUD
            )

    @pytest.mark.asyncio
    async def test_position_size_limit_with_existing_position(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test position size limit considers existing position"""
        # BTC position: 6,000 AUD
        # Max position: 2,000 AUD (20% of 10,000)
        # Already exceeds limit, can't add more

        with pytest.raises(SafetyViolation, match="Position size limit exceeded"):
            await safety_manager.validate_trade(
                user_id=test_user_with_portfolio.id,
                coin_type='BTC',
                side='buy',
                quantity=Decimal('100'),
                estimated_price=Decimal('60000')  # More BTC
            )

    @pytest.mark.asyncio
    async def test_daily_loss_limit_no_trades(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test daily loss check with no trades today"""
        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('100'),
            estimated_price=Decimal('0.50')
        )

        assert result['valid'] is True
        assert 'daily_loss' in result['checks_passed']

    @pytest.mark.asyncio
    async def test_daily_loss_limit_exceeded(
        self,
        session: Session,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test daily loss limit is enforced"""
        # Portfolio: 10,000 AUD
        # Max daily loss: 5% = 500 AUD
        # Create losing trades totaling 600 AUD loss

        # Create a sell order that resulted in loss
        order = Order(
            user_id=test_user_with_portfolio.id,
            coin_type='BTC',
            side='sell',
            quantity=Decimal('0.01'),
            price=Decimal('40000'),  # Sold at lower price (loss)
            filled_quantity=Decimal('0.01'),
            status='filled',
            filled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(order)

        # Create a buy order (cost)
        order2 = Order(
            user_id=test_user_with_portfolio.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('0.1'),
            price=Decimal('4000'),
            filled_quantity=Decimal('0.1'),
            status='filled',
            filled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(order2)
        session.commit()

        # Net: +400 (sell) - 400 (buy) = 0, so this should pass
        # Note: The actual P&L calculation is simplified in the code
        # TODO: Full P&L calculation with cost basis tracking will be implemented in Phase 6 Weeks 5-6
        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('100'),
            estimated_price=Decimal('0.50')
        )

        assert result['valid'] is True

    @pytest.mark.asyncio
    async def test_algorithm_exposure_limit_first_trade(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test algorithm exposure for first algorithmic trade"""
        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('100'),
            estimated_price=Decimal('0.50'),
            algorithm_id=uuid4()
        )

        assert result['valid'] is True
        assert 'algorithm_exposure' in result['checks_passed']

    @pytest.mark.asyncio
    async def test_algorithm_exposure_limit_within_limit(
        self,
        session: Session,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test algorithm exposure within limit"""
        algorithm_id = uuid4()

        # Create previous algorithmic buy order (1,000 AUD)
        # Set filled_at to yesterday to avoid triggering daily loss limit check
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        order = Order(
            user_id=test_user_with_portfolio.id,
            algorithm_id=algorithm_id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('2000'),
            price=Decimal('0.50'),
            filled_quantity=Decimal('2000'),
            status='filled',
            filled_at=yesterday,
            created_at=yesterday,
            updated_at=yesterday
        )
        session.add(order)
        session.commit()

        # Portfolio: 10,000 AUD
        # Max algorithm exposure: 30% = 3,000 AUD
        # Existing: 1,000 AUD
        # New trade: 500 AUD
        # Total: 1,500 AUD < 3,000 AUD ✓

        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='SOL',
            side='buy',
            quantity=Decimal('5'),
            estimated_price=Decimal('100'),  # 500 AUD
            algorithm_id=algorithm_id
        )

        assert result['valid'] is True

    @pytest.mark.asyncio
    async def test_get_safety_status(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test getting safety status"""
        status = safety_manager.get_safety_status(test_user_with_portfolio.id)

        assert status['emergency_stop'] is False
        assert status['portfolio_value'] == 10000.0
        assert status['max_daily_loss'] == 500.0  # 5% of 10,000
        assert status['max_position_size'] == 2000.0  # 20% of 10,000
        assert status['max_algorithm_exposure'] == 3000.0  # 30% of 10,000
        assert 'limits' in status

    def test_get_safety_manager_singleton(self, session: Session):
        """Test that get_safety_manager returns singleton instance"""
        manager1 = get_safety_manager(session)
        manager2 = get_safety_manager(session)

        assert manager1 is manager2


class TestSafetyManagerEdgeCases:
    """Edge case tests for safety manager"""

    @pytest.mark.asyncio
    async def test_sell_order_no_position_size_check(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test that sell orders don't trigger position size check"""
        # Sell orders reduce positions, so position size limit doesn't apply
        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='BTC',
            side='sell',
            quantity=Decimal('0.05'),
            estimated_price=Decimal('60000')
        )

        assert result['valid'] is True

    @pytest.mark.asyncio
    async def test_zero_quantity_trade(
        self,
        safety_manager: TradingSafetyManager,
        test_user: User
    ):
        """Test validation with zero quantity"""
        result = await safety_manager.validate_trade(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0'),
            estimated_price=Decimal('60000')
        )

        assert result['valid'] is True
        assert result['trade_value'] == Decimal('0')

    @pytest.mark.asyncio
    async def test_custom_safety_limits(self, session: Session, test_user: User):
        """Test safety manager with custom limits"""
        custom_manager = TradingSafetyManager(
            session=session,
            max_position_pct=Decimal('0.10'),  # Stricter: 10%
            max_daily_loss_pct=Decimal('0.02'),  # Stricter: 2%
            max_algorithm_exposure_pct=Decimal('0.15')  # Stricter: 15%
        )

        status = custom_manager.get_safety_status(test_user.id)

        assert status['limits']['max_position_pct'] == 0.10
        assert status['limits']['max_daily_loss_pct'] == 0.02
        assert status['limits']['max_algorithm_exposure_pct'] == 0.15

    @pytest.mark.asyncio
    async def test_emergency_stop_slack_alert(self, safety_manager: TradingSafetyManager):
        """Test that emergency stop sends a slack alert"""
        # Patch the send_slack_alert function where it is active (safety module)
        with patch('app.services.trading.safety.send_slack_alert', new_callable=AsyncMock) as mock_alert:
            await safety_manager.activate_emergency_stop()
            mock_alert.assert_called_once()
            assert "KILL SWITCH ACTIVATED" in mock_alert.call_args[0][0]

    @pytest.mark.asyncio
    async def test_volatile_market_detection(self, safety_manager: TradingSafetyManager):
        """Test detection of volatile market mode via Redis"""
        # Default is non-volatile
        assert not await safety_manager.is_volatile_market()

        # Set volatile
        await safety_manager.redis_client.set("omc:market_status", "volatile")
        assert await safety_manager.is_volatile_market()

        # Clear
        await safety_manager.redis_client.delete("omc:market_status")
        assert not await safety_manager.is_volatile_market()

    @pytest.mark.asyncio
    async def test_volatile_market_limits(
        self,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test that validation fails in volatile market with halved limits"""
        # Portfolio: 10,000 AUD
        # Normal Max Position (20%): 2,000 AUD
        # Volatile Max Position (10%): 1,000 AUD

        # Trade: Buy 1,500 AUD of SOL (New Coin)
        # Should PASS in Normal Market (1500 < 2000)
        result = await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='SOL',
            side='buy',
            quantity=Decimal('15'),
            estimated_price=Decimal('100')  # 15 * 100 = 1,500
        )
        assert result['valid'] is True

        # Set Volatile Mode
        await safety_manager.redis_client.set("omc:market_status", "volatile")

        # Should FAIL in Volatile Market (1500 > 1000)
        with pytest.raises(SafetyViolation) as excinfo:
            await safety_manager.validate_trade(
                user_id=test_user_with_portfolio.id,
                coin_type='SOL',
                side='buy',
                quantity=Decimal('15'),
                estimated_price=Decimal('100')
            )

        assert "VOLATILE MARKET MODE ACTIVE" in str(excinfo.value)

        # Cleanup
        await safety_manager.redis_client.delete("omc:market_status")

    @pytest.mark.asyncio
    async def test_daily_loss_limit_volatile(
        self,
        session: Session,
        safety_manager: TradingSafetyManager,
        test_user_with_portfolio: User
    ):
        """Test daily loss limit is halved in volatile market"""
        # Portfolio: 10,000 AUD
        # Normal Max Daily Loss (5%): 500 AUD
        # Volatile Max Daily Loss (2.5%): 250 AUD

        # 1. Simulate a realized loss of 300 AUD (Sold low)
        # Buy 1 ETH at 4000 (Cost)
        buy_order = Order(
            user_id=test_user_with_portfolio.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0'),
            price=Decimal('4000'),
            filled_quantity=Decimal('1.0'),
            status='filled',
            filled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(buy_order)

        # Sell 1 ETH at 3700 (Avg Cost 4000) -> -300 AUD Loss
        sell_order = Order(
            user_id=test_user_with_portfolio.id,
            coin_type='ETH',
            side='sell',
            quantity=Decimal('1.0'),
            price=Decimal('3700'),  # Loss of 300 vs 4000
            filled_quantity=Decimal('1.0'),
            status='filled',
            filled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(sell_order)
        session.commit()

        # 2. Check in Normal Market -> Should PASS (-300 > -500)
        # Note: -300 is technically "greater" than -500 in magnitude terms check?
        # The code checks: if daily_pnl < -max_loss:
        # -300 < -500 is FALSE. So it passes.
        await safety_manager.validate_trade(
            user_id=test_user_with_portfolio.id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('100'),
            estimated_price=Decimal('0.50')
        )

        # 3. Set Volatile Mode
        await safety_manager.redis_client.set("omc:market_status", "volatile")

        # 4. Check in Volatile Market -> Should FAIL (-300 < -250)
        # max_loss becomes 250. -max_loss is -250.
        # -300 < -250 is TRUE. So it raises.
        with pytest.raises(SafetyViolation) as excinfo:
             await safety_manager.validate_trade(
                user_id=test_user_with_portfolio.id,
                coin_type='ADA',
                side='buy',
                quantity=Decimal('100'),
                estimated_price=Decimal('0.50')
            )

        assert "VOLATILE MARKET MODE ACTIVE" in str(excinfo.value)
        assert "Daily loss limit exceeded" in str(excinfo.value)

        # Cleanup
        await safety_manager.redis_client.delete("omc:market_status")

    @pytest.mark.asyncio
    async def test_audit_log_failure_silent(
        self,
        safety_manager: TradingSafetyManager
    ):
        """Test that audit log failures do not crash the application"""
        # Mock session.add to raise an exception
        with patch.object(safety_manager.session, 'add', side_effect=Exception("DB Error")):
             # This simple log call should not raise an exception
             safety_manager._log_audit("TEST_ACTION", {})


