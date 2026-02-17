"""
Tests for Trade Recorder

Tests cover:
- Trade attempt logging
- Success recording
- Failure recording
- Partial fill recording
- Order reconciliation
- Trade history queries
- Trade statistics
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models import Order, User
from app.services.trading.recorder import TradeRecorder, get_trade_recorder


@pytest.fixture
def trade_recorder(session: Session) -> TradeRecorder:
    """Create a trade recorder instance for testing"""
    return TradeRecorder(session=session)


class TestTradeRecorder:
    """Tests for TradeRecorder"""

    def test_log_trade_attempt(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test logging a trade attempt"""
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01'),
            order_type='market',
            price=None,
            algorithm_id=None
        )

        assert order.id is not None
        assert order.user_id == test_user.id
        assert order.coin_type == 'BTC'
        assert order.side == 'buy'
        assert order.quantity == Decimal('0.01')
        assert order.status == 'pending'
        assert order.created_at is not None

        # Verify it was saved to database
        db_order = session.get(Order, order.id)
        assert db_order is not None
        assert db_order.user_id == test_user.id

    def test_log_trade_attempt_with_algorithm(
        self,
        trade_recorder: TradeRecorder,
        test_user: User
    ):
        """Test logging algorithmic trade attempt"""
        algorithm_id = uuid4()

        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='sell',
            quantity=Decimal('1.0'),
            algorithm_id=algorithm_id
        )

        assert order.algorithm_id == algorithm_id
        assert order.coin_type == 'ETH'
        assert order.side == 'sell'

    def test_record_success(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test recording a successful trade"""
        # Create pending order
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )

        # Record success
        coinspot_order_id = 'CS12345'
        filled_qty = Decimal('0.01')
        execution_price = Decimal('60000')

        trade_recorder.record_success(
            order_id=order.id,
            coinspot_order_id=coinspot_order_id,
            filled_quantity=filled_qty,
            execution_price=execution_price
        )

        # Verify order was updated
        session.refresh(order)
        assert order.status == 'filled'
        assert order.filled_quantity == filled_qty
        assert order.price == execution_price
        assert order.coinspot_order_id == coinspot_order_id
        assert order.filled_at is not None

    def test_record_failure(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test recording a failed trade"""
        # Create pending order
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )

        # Record failure
        error_msg = "Insufficient balance"
        trade_recorder.record_failure(
            order_id=order.id,
            error_message=error_msg
        )

        # Verify order was updated
        session.refresh(order)
        assert order.status == 'failed'
        assert order.error_message == error_msg
        assert order.updated_at is not None

    def test_record_partial_fill(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test recording a partial fill"""
        # Create pending order for 1.0 ETH
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0')
        )

        # Record partial fill (0.5 ETH filled)
        filled_qty = Decimal('0.5')
        execution_price = Decimal('4000')

        trade_recorder.record_partial_fill(
            order_id=order.id,
            filled_quantity=filled_qty,
            execution_price=execution_price
        )

        # Verify order was updated
        session.refresh(order)
        assert order.status == 'partial'
        assert order.filled_quantity == filled_qty
        assert order.price == execution_price

    @pytest.mark.asyncio
    async def test_reconcile_order_complete(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test order reconciliation with complete status"""
        # Create order
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )

        # Simulate exchange data
        exchange_data = {
            'id': 'CS12345',
            'status': 'complete',
            'amount': 0.01,
            'rate': 60000
        }

        # Reconcile
        result = await trade_recorder.reconcile_order(
            order_id=order.id,
            exchange_data=exchange_data
        )

        assert result is True

        # Verify order updated
        session.refresh(order)
        assert order.status == 'filled'
        assert order.coinspot_order_id == 'CS12345'
        assert order.filled_quantity == Decimal('0.01')
        assert order.price == Decimal('60000')

    @pytest.mark.asyncio
    async def test_reconcile_order_partial(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test order reconciliation with partial status"""
        # Create order
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0')
        )

        # Simulate partial fill
        exchange_data = {
            'id': 'CS54321',
            'status': 'partial',
            'amount': 0.5,
            'rate': 4000
        }

        # Reconcile
        result = await trade_recorder.reconcile_order(
            order_id=order.id,
            exchange_data=exchange_data
        )

        assert result is True

        # Verify order updated
        session.refresh(order)
        assert order.status == 'partial'
        assert order.filled_quantity == Decimal('0.5')

    @pytest.mark.asyncio
    async def test_reconcile_order_cancelled(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test order reconciliation with cancelled status"""
        # Create order
        order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )

        # Simulate cancellation
        exchange_data = {
            'id': 'CS99999',
            'status': 'cancelled',
            'amount': 0,
            'rate': 0
        }

        # Reconcile
        result = await trade_recorder.reconcile_order(
            order_id=order.id,
            exchange_data=exchange_data
        )

        assert result is True

        # Verify order updated
        session.refresh(order)
        assert order.status == 'cancelled'

    @pytest.mark.asyncio
    async def test_reconcile_order_not_found(
        self,
        trade_recorder: TradeRecorder
    ):
        """Test reconciliation with non-existent order"""
        result = await trade_recorder.reconcile_order(
            order_id=uuid4(),
            exchange_data={'id': 'CS12345', 'status': 'complete'}
        )

        assert result is False

    def test_get_trade_history_all(
        self,
        trade_recorder: TradeRecorder,
        test_user: User
    ):
        """Test getting all trade history for a user"""
        # Create multiple orders
        for i in range(3):
            trade_recorder.log_trade_attempt(
                user_id=test_user.id,
                coin_type='BTC' if i % 2 == 0 else 'ETH',
                side='buy',
                quantity=Decimal('0.01')
            )

        # Get all trade history
        orders = trade_recorder.get_trade_history(user_id=test_user.id)

        assert len(orders) == 3

    def test_get_trade_history_with_coin_filter(
        self,
        trade_recorder: TradeRecorder,
        test_user: User
    ):
        """Test getting trade history filtered by coin"""
        # Create orders for different coins
        trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )
        trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0')
        )

        # Get BTC orders only
        btc_orders = trade_recorder.get_trade_history(
            user_id=test_user.id,
            coin_type='BTC'
        )

        assert len(btc_orders) == 1
        assert btc_orders[0].coin_type == 'BTC'

    def test_get_trade_history_with_status_filter(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test getting trade history filtered by status"""
        # Create orders with different statuses
        order1 = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )

        order2 = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0')
        )

        # Mark one as filled
        trade_recorder.record_success(
            order_id=order1.id,
            coinspot_order_id='CS12345',
            filled_quantity=Decimal('0.01'),
            execution_price=Decimal('60000')
        )

        # Get filled orders only
        filled_orders = trade_recorder.get_trade_history(
            user_id=test_user.id,
            status='filled'
        )

        assert len(filled_orders) == 1
        assert filled_orders[0].status == 'filled'

    def test_get_trade_history_with_date_filter(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test getting trade history filtered by date"""
        # Create old order
        old_order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )
        old_order.created_at = datetime.now(timezone.utc) - timedelta(days=10)
        session.add(old_order)
        session.commit()

        # Create recent order
        recent_order = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0')
        )

        # Get orders from last 7 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        recent_orders = trade_recorder.get_trade_history(
            user_id=test_user.id,
            start_date=cutoff
        )

        assert len(recent_orders) == 1
        assert recent_orders[0].coin_type == 'ETH'

    def test_get_trade_history_with_algorithm_filter(
        self,
        trade_recorder: TradeRecorder,
        test_user: User
    ):
        """Test getting trade history filtered by algorithm"""
        algorithm_id = uuid4()

        # Create algorithmic order
        trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01'),
            algorithm_id=algorithm_id
        )

        # Create manual order
        trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='buy',
            quantity=Decimal('1.0'),
            algorithm_id=None
        )

        # Get algorithmic orders only
        algo_orders = trade_recorder.get_trade_history(
            user_id=test_user.id,
            algorithm_id=algorithm_id
        )

        assert len(algo_orders) == 1
        assert algo_orders[0].algorithm_id == algorithm_id

    def test_get_trade_statistics(
        self,
        trade_recorder: TradeRecorder,
        test_user: User,
        session: Session
    ):
        """Test getting trade statistics"""
        # Create mix of filled, failed, and partial orders
        # Filled buy order
        order1 = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='BTC',
            side='buy',
            quantity=Decimal('0.01')
        )
        trade_recorder.record_success(
            order_id=order1.id,
            coinspot_order_id='CS1',
            filled_quantity=Decimal('0.01'),
            execution_price=Decimal('60000')
        )

        # Filled sell order
        order2 = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ETH',
            side='sell',
            quantity=Decimal('1.0')
        )
        trade_recorder.record_success(
            order_id=order2.id,
            coinspot_order_id='CS2',
            filled_quantity=Decimal('1.0'),
            execution_price=Decimal('4000')
        )

        # Failed order
        order3 = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='ADA',
            side='buy',
            quantity=Decimal('1000')
        )
        trade_recorder.record_failure(
            order_id=order3.id,
            error_message='Insufficient balance'
        )

        # Partial order
        order4 = trade_recorder.log_trade_attempt(
            user_id=test_user.id,
            coin_type='SOL',
            side='buy',
            quantity=Decimal('10')
        )
        trade_recorder.record_partial_fill(
            order_id=order4.id,
            filled_quantity=Decimal('5'),
            execution_price=Decimal('100')
        )

        # Get statistics
        stats = trade_recorder.get_trade_statistics(user_id=test_user.id)

        assert stats['total_trades'] == 4
        assert stats['filled_trades'] == 2
        assert stats['failed_trades'] == 1
        assert stats['partial_trades'] == 1
        assert stats['buy_trades'] == 1
        assert stats['sell_trades'] == 1
        assert stats['total_buy_volume_aud'] == 600.0  # 0.01 * 60000
        assert stats['total_sell_volume_aud'] == 4000.0  # 1.0 * 4000
        assert stats['success_rate'] == 50.0  # 2/4 * 100

    def test_get_trade_statistics_empty(
        self,
        trade_recorder: TradeRecorder,
        test_user: User
    ):
        """Test statistics with no trades"""
        stats = trade_recorder.get_trade_statistics(user_id=test_user.id)

        assert stats['total_trades'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['total_buy_volume_aud'] == 0.0

    def test_get_trade_recorder_factory(self, session: Session):
        """Test factory function"""
        recorder = get_trade_recorder(session)
        assert isinstance(recorder, TradeRecorder)

    def test_record_success_order_not_found(
        self,
        trade_recorder: TradeRecorder
    ):
        """Test recording success for non-existent order"""
        # Should not raise error, just log warning
        trade_recorder.record_success(
            order_id=uuid4(),
            coinspot_order_id='CS12345',
            filled_quantity=Decimal('0.01'),
            execution_price=Decimal('60000')
        )

    def test_record_failure_order_not_found(
        self,
        trade_recorder: TradeRecorder
    ):
        """Test recording failure for non-existent order"""
        # Should not raise error, just log warning
        trade_recorder.record_failure(
            order_id=uuid4(),
            error_message='Test error'
        )
