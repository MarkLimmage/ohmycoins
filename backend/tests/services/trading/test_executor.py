"""
Tests for Order Executor
"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models import Order, Position
from app.services.trading.executor import OrderExecutor, OrderQueue, get_order_queue


class TestOrderExecutor:
    """Test suite for OrderExecutor"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = MagicMock()
        session.get = MagicMock()
        session.exec = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.delete = MagicMock()
        return session

    @pytest.fixture
    def executor(self, mock_session):
        """Create an order executor instance"""
        return OrderExecutor(
            session=mock_session,
            api_key='test_key',
            api_secret='test_secret',
            max_retries=3,
            retry_delay=0.1  # Fast retry for tests
        )

    @pytest.fixture
    def sample_order(self):
        """Create a sample order"""
        return Order(
            id=uuid4(),
            user_id=uuid4(),
            coin_type='BTC',
            side='buy',
            order_type='market',
            quantity=Decimal('1000.00'),
            filled_quantity=Decimal('0'),
            status='pending',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.mark.asyncio
    async def test_submit_order(self, executor, sample_order):
        """Test submitting an order to the queue"""
        await executor.submit_order(sample_order.id)

        # Queue should have one item
        assert executor._queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_execute_buy_order_success(self, executor, mock_session, sample_order):
        """Test successful buy order execution"""
        # Mock session.get to return our sample order
        mock_session.get.return_value = sample_order

        # Mock position query to return None (no existing position)
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # Mock the trade execution
        mock_result = {
            'status': 'ok',
            'id': '12345',
            'rate': '50000.00',
            'coin': '0.02'
        }

        with patch.object(executor, '_execute_trade', new_callable=AsyncMock) as mock_trade:
            mock_trade.return_value = mock_result

            await executor._execute_order(sample_order.id)

            # Verify order was updated
            assert sample_order.status == 'filled'
            assert sample_order.filled_quantity == sample_order.quantity
            assert sample_order.coinspot_order_id == '12345'
            assert sample_order.price == Decimal('50000.00')

            # Verify session methods were called
            assert mock_session.add.called
            assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_execute_sell_order_success(self, executor, mock_session):
        """Test successful sell order execution"""
        # Create sell order
        sell_order = Order(
            id=uuid4(),
            user_id=uuid4(),
            coin_type='ETH',
            side='sell',
            order_type='market',
            quantity=Decimal('0.5'),
            filled_quantity=Decimal('0'),
            status='pending',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Mock existing position
        existing_position = Position(
            id=uuid4(),
            user_id=sell_order.user_id,
            coin_type='ETH',
            quantity=Decimal('1.0'),
            average_price=Decimal('3000.00'),
            total_cost=Decimal('3000.00'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        mock_session.get.return_value = sell_order
        mock_result = MagicMock()
        mock_result.first.return_value = existing_position
        mock_session.exec.return_value = mock_result

        # Mock the trade execution
        mock_result = {
            'status': 'ok',
            'id': '67890',
            'rate': '3100.00'
        }

        with patch.object(executor, '_execute_trade', new_callable=AsyncMock) as mock_trade:
            mock_trade.return_value = mock_result

            await executor._execute_order(sell_order.id)

            # Verify order was updated
            assert sell_order.status == 'filled'
            assert sell_order.coinspot_order_id == '67890'

            # Verify position was updated (quantity reduced)
            assert existing_position.quantity == Decimal('0.5')

    @pytest.mark.asyncio
    async def test_execute_order_with_retry(self, executor, mock_session, sample_order):
        """Test order execution with retries on API error"""
        from app.services.trading.exceptions import CoinspotAPIError

        mock_session.get.return_value = sample_order
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # First call fails, second succeeds
        mock_trade = AsyncMock()
        mock_trade.side_effect = [
            CoinspotAPIError("API timeout"),
            {
                'status': 'ok',
                'id': '99999',
                'rate': '50000.00'
            }
        ]

        with patch.object(executor, '_execute_trade', mock_trade):
            await executor._execute_order(sample_order.id)

            # Should have retried and succeeded
            assert sample_order.status == 'filled'
            assert mock_trade.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_order_max_retries_exceeded(self, executor, mock_session, sample_order):
        """Test order execution fails after max retries"""
        from app.services.trading.exceptions import CoinspotAPIError

        mock_session.get.return_value = sample_order

        # All attempts fail
        mock_trade = AsyncMock()
        mock_trade.side_effect = CoinspotAPIError("API error")

        with patch.object(executor, '_execute_trade', mock_trade):
            await executor._execute_order(sample_order.id)

            # Should have failed
            assert sample_order.status == 'failed'
            assert sample_order.error_message is not None
            assert mock_trade.call_count == executor.max_retries

    @pytest.mark.asyncio
    async def test_execute_order_already_processed(self, executor, mock_session, sample_order):
        """Test executing an already processed order"""
        sample_order.status = 'filled'
        mock_session.get.return_value = sample_order

        with patch.object(executor, '_execute_trade', new_callable=AsyncMock) as mock_trade:
            await executor._execute_order(sample_order.id)

            # Should not attempt to execute
            assert not mock_trade.called


class TestOrderQueue:
    """Test suite for OrderQueue singleton"""

    def test_singleton_pattern(self):
        """Test that OrderQueue follows singleton pattern"""
        queue1 = get_order_queue()
        queue2 = get_order_queue()

        assert queue1 is queue2

    def test_initialize(self):
        """Test queue initialization"""
        queue = OrderQueue()
        mock_session = MagicMock()

        queue.initialize(
            session=mock_session,
            api_key='key',
            api_secret='secret'
        )

        assert queue._executor is not None
