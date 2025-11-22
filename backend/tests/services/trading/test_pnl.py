"""
Tests for the P&L (Profit & Loss) calculation engine
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.models import User, Order, Position, PriceData5Min
from app.services.trading.pnl import PnLEngine, PnLMetrics, get_pnl_engine


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def pnl_engine(session: Session) -> PnLEngine:
    """Create a P&L engine instance"""
    return PnLEngine(session)


def test_pnl_engine_creation(session: Session):
    """Test P&L engine can be created"""
    engine = PnLEngine(session)
    assert engine is not None
    assert engine.session == session


def test_get_pnl_engine_factory(session: Session):
    """Test factory function creates P&L engine"""
    engine = get_pnl_engine(session)
    assert isinstance(engine, PnLEngine)
    assert engine.session == session


def test_calculate_realized_pnl_no_trades(pnl_engine: PnLEngine, test_user: User):
    """Test realized P&L calculation with no trades"""
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    assert pnl == Decimal('0')


def test_calculate_realized_pnl_single_profitable_trade(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test realized P&L with a single profitable trade"""
    # Buy 1 BTC at $50,000
    buy_order = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        order_type='market',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    )
    session.add(buy_order)
    
    # Sell 1 BTC at $55,000
    sell_order = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        order_type='market',
        quantity=Decimal('1.0'),
        price=Decimal('55000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    session.add(sell_order)
    session.commit()
    
    # Calculate realized P&L
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    
    # Expected P&L: (55000 - 50000) * 1.0 = 5000
    assert pnl == Decimal('5000.00')


def test_calculate_realized_pnl_losing_trade(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test realized P&L with a losing trade"""
    # Buy 2 ETH at $3000
    buy_order = Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        order_type='market',
        quantity=Decimal('2.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    )
    session.add(buy_order)
    
    # Sell 2 ETH at $2800
    sell_order = Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='sell',
        order_type='market',
        quantity=Decimal('2.0'),
        price=Decimal('2800.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    session.add(sell_order)
    session.commit()
    
    # Calculate realized P&L
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    
    # Expected P&L: (2800 - 3000) * 2.0 = -400
    assert pnl == Decimal('-400.00')


def test_calculate_realized_pnl_partial_sell(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test realized P&L with partial position sell"""
    # Buy 10 BTC at $50,000
    buy_order = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        order_type='market',
        quantity=Decimal('10.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('10.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    )
    session.add(buy_order)
    
    # Sell 3 BTC at $52,000
    sell_order = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        order_type='market',
        quantity=Decimal('3.0'),
        price=Decimal('52000.00'),
        filled_quantity=Decimal('3.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    session.add(sell_order)
    session.commit()
    
    # Calculate realized P&L
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    
    # Expected P&L: (52000 - 50000) * 3.0 = 6000
    assert pnl == Decimal('6000.00')


def test_calculate_realized_pnl_fifo_method(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test FIFO (First In First Out) method for P&L calculation"""
    # Buy 1 BTC at $50,000
    buy1 = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        order_type='market',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    )
    session.add(buy1)
    
    # Buy 1 BTC at $51,000
    buy2 = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        order_type='market',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    session.add(buy2)
    
    # Sell 1 BTC at $53,000 (should use first buy at $50,000)
    sell = Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        order_type='market',
        quantity=Decimal('1.0'),
        price=Decimal('53000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=2)
    )
    session.add(sell)
    session.commit()
    
    # Calculate realized P&L
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    
    # Expected P&L: (53000 - 50000) * 1.0 = 3000
    # Not (53000 - 51000) * 1.0 = 2000
    assert pnl == Decimal('3000.00')


def test_calculate_realized_pnl_multiple_coins(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test P&L calculation across multiple cryptocurrencies"""
    # BTC trade: profit of 1000
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    
    # ETH trade: loss of 200
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('2.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('2.0'),
        price=Decimal('2900.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    session.commit()
    
    # Calculate total realized P&L
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    
    # Expected: 1000 - 200 = 800
    assert pnl == Decimal('800.00')


def test_calculate_realized_pnl_by_coin_filter(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test P&L calculation filtered by specific coin"""
    # BTC trade
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    
    # ETH trade
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('2.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.commit()
    
    # Calculate P&L for BTC only
    pnl = pnl_engine.calculate_realized_pnl(test_user.id, coin_type='BTC')
    
    # Should only include BTC trade: 1000
    assert pnl == Decimal('1000.00')


def test_calculate_realized_pnl_date_filter(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test P&L calculation with date filters"""
    now = datetime.now(timezone.utc)
    
    # Trade 1: Yesterday
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=2)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=1)
    ))
    
    # Trade 2: Today
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(hours=2)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('3100.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(hours=1)
    ))
    session.commit()
    
    # Calculate P&L for today only
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pnl = pnl_engine.calculate_realized_pnl(test_user.id, start_date=start_of_today)
    
    # Should only include ETH trade: 100
    assert pnl == Decimal('100.00')


def test_calculate_unrealized_pnl_no_positions(pnl_engine: PnLEngine, test_user: User):
    """Test unrealized P&L with no open positions"""
    pnl = pnl_engine.calculate_unrealized_pnl(test_user.id)
    assert pnl == Decimal('0')


def test_calculate_unrealized_pnl_with_position(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test unrealized P&L calculation with open position"""
    # Create a position: bought 2 BTC at average price of $50,000
    position = Position(
        user_id=test_user.id,
        coin_type='BTC',
        quantity=Decimal('2.0'),
        average_price=Decimal('50000.00'),
        total_cost=Decimal('100000.00')
    )
    session.add(position)
    
    # Add current price data: BTC is now $52,000
    price_data = PriceData5Min(
        timestamp=datetime.now(timezone.utc),
        coin_type='BTC',
        bid=Decimal('51900.00'),
        ask=Decimal('52100.00'),
        last=Decimal('52000.00')
    )
    session.add(price_data)
    session.commit()
    
    # Calculate unrealized P&L
    pnl = pnl_engine.calculate_unrealized_pnl(test_user.id)
    
    # Expected: (52000 * 2) - 100000 = 104000 - 100000 = 4000
    assert pnl == Decimal('4000.00')


def test_calculate_unrealized_pnl_loss(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test unrealized P&L with losing position"""
    # Position: 5 ETH at $3000 = $15,000 total cost
    position = Position(
        user_id=test_user.id,
        coin_type='ETH',
        quantity=Decimal('5.0'),
        average_price=Decimal('3000.00'),
        total_cost=Decimal('15000.00')
    )
    session.add(position)
    
    # Current price: ETH is now $2800
    price_data = PriceData5Min(
        timestamp=datetime.now(timezone.utc),
        coin_type='ETH',
        bid=Decimal('2790.00'),
        ask=Decimal('2810.00'),
        last=Decimal('2800.00')
    )
    session.add(price_data)
    session.commit()
    
    # Calculate unrealized P&L
    pnl = pnl_engine.calculate_unrealized_pnl(test_user.id)
    
    # Expected: (2800 * 5) - 15000 = 14000 - 15000 = -1000
    assert pnl == Decimal('-1000.00')


def test_get_pnl_summary_comprehensive(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test comprehensive P&L summary with multiple trades"""
    # Winning trade 1: BTC +2000
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=3)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('52000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=2)
    ))
    
    # Winning trade 2: ETH +400
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('2.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=2)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('2.0'),
        price=Decimal('3200.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=1)
    ))
    
    # Losing trade: DOGE -50
    session.add(Order(
        user_id=test_user.id,
        coin_type='DOGE',
        side='buy',
        quantity=Decimal('1000.0'),
        price=Decimal('0.50'),
        filled_quantity=Decimal('1000.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=1)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='DOGE',
        side='sell',
        quantity=Decimal('1000.0'),
        price=Decimal('0.45'),
        filled_quantity=Decimal('1000.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.commit()
    
    # Get P&L summary
    metrics = pnl_engine.get_pnl_summary(test_user.id)
    
    # Verify calculations
    assert metrics.realized_pnl == Decimal('2350.00')  # 2000 + 400 - 50
    assert metrics.total_trades == 3
    assert metrics.winning_trades == 2
    assert metrics.losing_trades == 1
    # Win rate: 2/3 = 66.67% (rounded)
    assert abs(metrics.win_rate - Decimal('66.67')) < Decimal('0.01')
    assert metrics.total_profit == Decimal('2400.00')  # 2000 + 400
    assert metrics.total_loss == Decimal('-50.00')
    assert metrics.largest_win == Decimal('2000.00')
    assert metrics.largest_loss == Decimal('-50.00')


def test_get_pnl_by_algorithm(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test P&L grouping by algorithm"""
    algo1 = uuid.uuid4()
    algo2 = uuid.uuid4()
    
    # Algorithm 1: profit 1000
    session.add(Order(
        user_id=test_user.id,
        algorithm_id=algo1,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        algorithm_id=algo1,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    
    # Algorithm 2: profit 200
    session.add(Order(
        user_id=test_user.id,
        algorithm_id=algo2,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        algorithm_id=algo2,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('3200.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    session.commit()
    
    # Get P&L by algorithm
    pnl_by_algo = pnl_engine.get_pnl_by_algorithm(test_user.id)
    
    assert len(pnl_by_algo) == 2
    assert pnl_by_algo[algo1].realized_pnl == Decimal('1000.00')
    assert pnl_by_algo[algo2].realized_pnl == Decimal('200.00')


def test_get_pnl_by_coin(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test P&L grouping by cryptocurrency"""
    # BTC: profit 1000
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    
    # ETH: profit 200
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('3200.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    session.commit()
    
    # Get P&L by coin
    pnl_by_coin = pnl_engine.get_pnl_by_coin(test_user.id)
    
    assert len(pnl_by_coin) == 2
    assert pnl_by_coin['BTC'].realized_pnl == Decimal('1000.00')
    assert pnl_by_coin['ETH'].realized_pnl == Decimal('200.00')


def test_get_historical_pnl_daily(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test historical P&L data with daily aggregation"""
    now = datetime.now(timezone.utc)
    
    # Day 1: profit 1000
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=2)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=2, hours=-1)
    ))
    
    # Day 2: profit 200
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=1)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('3200.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=1, hours=-1)
    ))
    session.commit()
    
    # Get historical P&L
    start_date = now - timedelta(days=3)
    end_date = now
    historical = pnl_engine.get_historical_pnl(test_user.id, start_date, end_date, interval='day')
    
    assert len(historical) >= 3  # At least 3 days
    assert all('timestamp' in entry for entry in historical)
    assert all('realized_pnl' in entry for entry in historical)
    assert all('interval' in entry for entry in historical)


def test_pnl_metrics_to_dict(session: Session):
    """Test PnLMetrics conversion to dictionary"""
    metrics = PnLMetrics(
        realized_pnl=Decimal('1000.00'),
        unrealized_pnl=Decimal('500.00'),
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        total_profit=Decimal('2000.00'),
        total_loss=Decimal('-500.00')
    )
    
    result = metrics.to_dict()
    
    assert isinstance(result, dict)
    assert result['realized_pnl'] == 1000.0
    assert result['unrealized_pnl'] == 500.0
    assert result['total_pnl'] == 1500.0
    assert result['total_trades'] == 10
    assert result['winning_trades'] == 6
    assert result['losing_trades'] == 4
    assert result['win_rate'] == 60.0
    assert result['total_profit'] == 2000.0
    assert result['total_loss'] == -500.0


def test_pnl_metrics_calculations():
    """Test PnLMetrics automatic calculations"""
    metrics = PnLMetrics(
        total_trades=10,
        winning_trades=7,
        losing_trades=3,
        total_profit=Decimal('3500.00'),
        total_loss=Decimal('-1000.00')
    )
    
    # Win rate should be calculated
    assert metrics.win_rate == Decimal('70.00')
    
    # Profit factor should be calculated (profit / abs(loss))
    assert metrics.profit_factor == Decimal('3.50')
    
    # Average win should be calculated
    assert metrics.average_win == Decimal('500.00')
    
    # Average loss should be calculated
    assert metrics.average_loss.quantize(Decimal('0.01')) == Decimal('333.33')


def test_calculate_realized_pnl_ignores_pending_orders(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test that P&L calculation ignores non-filled orders"""
    # Filled order: should be included
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    
    # Pending order: should be ignored
    session.add(Order(
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('0'),
        status='pending'
    ))
    
    # Failed order: should be ignored
    session.add(Order(
        user_id=test_user.id,
        coin_type='DOGE',
        side='buy',
        quantity=Decimal('100.0'),
        price=Decimal('0.50'),
        filled_quantity=Decimal('0'),
        status='failed'
    ))
    session.commit()
    
    # Calculate P&L
    pnl = pnl_engine.calculate_realized_pnl(test_user.id)
    
    # Should only include the filled BTC trade
    assert pnl == Decimal('1000.00')


def test_pnl_with_no_price_data(
    pnl_engine: PnLEngine,
    test_user: User,
    session: Session
):
    """Test unrealized P&L when no price data is available"""
    # Create position without price data
    position = Position(
        user_id=test_user.id,
        coin_type='BTC',
        quantity=Decimal('1.0'),
        average_price=Decimal('50000.00'),
        total_cost=Decimal('50000.00')
    )
    session.add(position)
    session.commit()
    
    # Calculate unrealized P&L (should be 0 since no price data)
    pnl = pnl_engine.calculate_unrealized_pnl(test_user.id)
    
    # Should be 0 since we can't calculate current value
    assert pnl == Decimal('0')
