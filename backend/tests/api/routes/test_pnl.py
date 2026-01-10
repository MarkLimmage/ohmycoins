"""
Tests for P&L API endpoints
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.models import User, Order, Position, PriceData5Min
from app.api.deps import get_db, get_current_user
from app.utils.test_fixtures import create_test_user


@pytest.fixture
def pnl_test_user(session: Session) -> User:
    """Create a test user for PnL tests using PostgreSQL session with unique email"""
    user = create_test_user(
        session,
        email=f"pnl_test_{uuid.uuid4()}@example.com",
        full_name="PnL Test User"
    )
    return user


@pytest.fixture
def pnl_client(session: Session, pnl_test_user: User):
    """Create a test client with auth for PnL tests"""
    def override_get_db():
        return session
    
    def override_get_current_user():
        return pnl_test_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


def test_get_pnl_summary_no_trades(pnl_client: TestClient):
    """Test P&L summary with no trades"""
    response = pnl_client.get("/api/v1/floor/pnl/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['realized_pnl'] == 0.0
    assert data['unrealized_pnl'] == 0.0
    assert data['total_pnl'] == 0.0
    assert data['total_trades'] == 0
    assert data['winning_trades'] == 0
    assert data['losing_trades'] == 0


def test_get_pnl_summary_with_trades(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test P&L summary with completed trades"""
    # Create profitable trade
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=2)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('52000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=1)
    ))
    session.commit()
    
    response = pnl_client.get("/api/v1/floor/pnl/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['realized_pnl'] == 2000.0
    assert data['total_trades'] == 1
    assert data['winning_trades'] == 1
    assert data['losing_trades'] == 0
    assert data['win_rate'] == 100.0
    assert data['largest_win'] == 2000.0


def test_get_pnl_summary_with_date_filter(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test P&L summary with date filters"""
    now = datetime.now(timezone.utc)
    
    # Old trade (should be excluded)
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=10)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=9)
    ))
    
    # Recent trade (should be included)
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('2.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=now - timedelta(hours=2)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('2.0'),
        price=Decimal('3100.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=now - timedelta(hours=1)
    ))
    session.commit()
    
    # Query with date filter (last 7 days)
    # Use URL-safe format (without microseconds and with Z for UTC)
    start_date = (now - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    response = pnl_client.get(f"/api/v1/floor/pnl/summary?start_date={start_date}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include ETH trade: 200
    assert data['realized_pnl'] == 200.0
    assert data['total_trades'] == 1


def test_get_pnl_by_algorithm(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test P&L grouped by algorithm"""
    algo1 = uuid.uuid4()
    algo2 = uuid.uuid4()
    
    # Algorithm 1: profit 1000
    session.add(Order(
        user_id=pnl_test_user.id,
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
        user_id=pnl_test_user.id,
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
        user_id=pnl_test_user.id,
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
        user_id=pnl_test_user.id,
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
    
    response = pnl_client.get("/api/v1/floor/pnl/by-algorithm")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    # Find each algorithm in results
    algo1_data = next(item for item in data if item['algorithm_id'] == str(algo1))
    algo2_data = next(item for item in data if item['algorithm_id'] == str(algo2))
    
    assert algo1_data['realized_pnl'] == 1000.0
    assert algo2_data['realized_pnl'] == 200.0


def test_get_pnl_by_coin(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test P&L grouped by cryptocurrency"""
    # BTC: profit 1000
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
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
        user_id=pnl_test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='ETH',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('3200.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    session.commit()
    
    response = pnl_client.get("/api/v1/floor/pnl/by-coin")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    # Find each coin in results
    btc_data = next(item for item in data if item['coin_type'] == 'BTC')
    eth_data = next(item for item in data if item['coin_type'] == 'ETH')
    
    assert btc_data['realized_pnl'] == 1000.0
    assert eth_data['realized_pnl'] == 200.0


def test_get_historical_pnl(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test historical P&L data"""
    now = datetime.now(timezone.utc)
    
    # Create trade
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=2)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('51000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=2, hours=-1)
    ))
    session.commit()
    
    # Query historical data
    # Use URL-safe format (without microseconds and with Z for UTC)
    start_date = (now - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    response = pnl_client.get(
        f"/api/v1/floor/pnl/history?start_date={start_date}&end_date={end_date}&interval=day"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 3  # At least 3 daily entries
    assert all('timestamp' in entry for entry in data)
    assert all('realized_pnl' in entry for entry in data)
    assert all('interval' in entry for entry in data)
    assert all(entry['interval'] == 'day' for entry in data)


def test_get_historical_pnl_invalid_interval(pnl_client: TestClient):
    """Test historical P&L with invalid interval"""
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    response = pnl_client.get(
        f"/api/v1/floor/pnl/history?start_date={start_date}&end_date={end_date}&interval=invalid"
    )
    
    assert response.status_code == 400
    assert "Invalid interval" in response.json()['detail']


def test_get_historical_pnl_missing_dates(pnl_client: TestClient):
    """Test historical P&L with missing required dates"""
    response = pnl_client.get("/api/v1/floor/pnl/history")
    
    assert response.status_code == 422  # Validation error


def test_get_realized_pnl(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test realized P&L endpoint"""
    # Create profitable trade
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('52000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    session.commit()
    
    response = pnl_client.get("/api/v1/floor/pnl/realized")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['realized_pnl'] == 2000.0


def test_get_realized_pnl_with_coin_filter(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test realized P&L with coin filter"""
    # BTC trade
    session.add(Order(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.add(Order(
        user_id=pnl_test_user.id,
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
        user_id=pnl_test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.commit()
    
    response = pnl_client.get("/api/v1/floor/pnl/realized?coin_type=BTC")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include BTC trade
    assert data['realized_pnl'] == 1000.0


def test_get_unrealized_pnl_no_positions(pnl_client: TestClient):
    """Test unrealized P&L with no positions"""
    response = pnl_client.get("/api/v1/floor/pnl/unrealized")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['unrealized_pnl'] == 0.0


def test_get_unrealized_pnl_with_position(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test unrealized P&L with open position"""
    # Create position
    position = Position(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        quantity=Decimal('1.0'),
        average_price=Decimal('50000.00'),
        total_cost=Decimal('50000.00')
    )
    session.add(position)
    
    # Add price data
    price_data = PriceData5Min(
        timestamp=datetime.now(timezone.utc),
        coin_type='BTC',
        bid=Decimal('51900.00'),
        ask=Decimal('52100.00'),
        last=Decimal('52000.00')
    )
    session.add(price_data)
    session.commit()
    
    response = pnl_client.get("/api/v1/floor/pnl/unrealized")
    
    assert response.status_code == 200
    data = response.json()
    
    # Expected: (52000 - 50000) * 1.0 = 2000
    assert data['unrealized_pnl'] == 2000.0


def test_get_unrealized_pnl_with_coin_filter(
    pnl_client: TestClient,
    pnl_test_user: User,
    session: Session
):
    """Test unrealized P&L with coin filter"""
    # BTC position
    session.add(Position(
        user_id=pnl_test_user.id,
        coin_type='BTC',
        quantity=Decimal('1.0'),
        average_price=Decimal('50000.00'),
        total_cost=Decimal('50000.00')
    ))
    session.add(PriceData5Min(
        timestamp=datetime.now(timezone.utc),
        coin_type='BTC',
        bid=Decimal('51000.00'),
        ask=Decimal('51000.00'),
        last=Decimal('51000.00')
    ))
    
    # ETH position
    session.add(Position(
        user_id=pnl_test_user.id,
        coin_type='ETH',
        quantity=Decimal('2.0'),
        average_price=Decimal('3000.00'),
        total_cost=Decimal('6000.00')
    ))
    session.add(PriceData5Min(
        timestamp=datetime.now(timezone.utc),
        coin_type='ETH',
        bid=Decimal('3200.00'),
        ask=Decimal('3200.00'),
        last=Decimal('3200.00')
    ))
    session.commit()
    
    response = pnl_client.get("/api/v1/floor/pnl/unrealized?coin_type=BTC")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include BTC position: 1000
    assert data['unrealized_pnl'] == 1000.0
