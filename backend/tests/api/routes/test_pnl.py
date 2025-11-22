"""
Tests for P&L API endpoints
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from app.main import app
from app.models import User, Order, Position, PriceData5Min
from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash


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
def test_user(session: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def client(session: Session, test_user: User):
    """Create a test client with auth"""
    def override_get_db():
        return session
    
    def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


def test_get_pnl_summary_no_trades(client: TestClient):
    """Test P&L summary with no trades"""
    response = client.get("/api/v1/floor/pnl/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['realized_pnl'] == 0.0
    assert data['unrealized_pnl'] == 0.0
    assert data['total_pnl'] == 0.0
    assert data['total_trades'] == 0
    assert data['winning_trades'] == 0
    assert data['losing_trades'] == 0


def test_get_pnl_summary_with_trades(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test P&L summary with completed trades"""
    # Create profitable trade
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=2)
    ))
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='sell',
        quantity=Decimal('1.0'),
        price=Decimal('52000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) - timedelta(hours=1)
    ))
    session.commit()
    
    response = client.get("/api/v1/floor/pnl/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['realized_pnl'] == 2000.0
    assert data['total_trades'] == 1
    assert data['winning_trades'] == 1
    assert data['losing_trades'] == 0
    assert data['win_rate'] == 100.0
    assert data['largest_win'] == 2000.0


def test_get_pnl_summary_with_date_filter(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test P&L summary with date filters"""
    now = datetime.now(timezone.utc)
    
    # Old trade (should be excluded)
    session.add(Order(
        user_id=test_user.id,
        coin_type='BTC',
        side='buy',
        quantity=Decimal('1.0'),
        price=Decimal('50000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=now - timedelta(days=10)
    ))
    session.add(Order(
        user_id=test_user.id,
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
        user_id=test_user.id,
        coin_type='ETH',
        side='buy',
        quantity=Decimal('2.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('2.0'),
        status='filled',
        filled_at=now - timedelta(hours=2)
    ))
    session.add(Order(
        user_id=test_user.id,
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
    start_date = (now - timedelta(days=7)).isoformat()
    response = client.get(f"/api/v1/floor/pnl/summary?start_date={start_date}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include ETH trade: 200
    assert data['realized_pnl'] == 200.0
    assert data['total_trades'] == 1


def test_get_pnl_by_algorithm(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test P&L grouped by algorithm"""
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
    
    response = client.get("/api/v1/floor/pnl/by-algorithm")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    # Find each algorithm in results
    algo1_data = next(item for item in data if item['algorithm_id'] == str(algo1))
    algo2_data = next(item for item in data if item['algorithm_id'] == str(algo2))
    
    assert algo1_data['realized_pnl'] == 1000.0
    assert algo2_data['realized_pnl'] == 200.0


def test_get_pnl_by_coin(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test P&L grouped by cryptocurrency"""
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
    
    response = client.get("/api/v1/floor/pnl/by-coin")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 2
    
    # Find each coin in results
    btc_data = next(item for item in data if item['coin_type'] == 'BTC')
    eth_data = next(item for item in data if item['coin_type'] == 'ETH')
    
    assert btc_data['realized_pnl'] == 1000.0
    assert eth_data['realized_pnl'] == 200.0


def test_get_historical_pnl(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test historical P&L data"""
    now = datetime.now(timezone.utc)
    
    # Create trade
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
    session.commit()
    
    # Query historical data
    start_date = (now - timedelta(days=3)).isoformat()
    end_date = now.isoformat()
    
    response = client.get(
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


def test_get_historical_pnl_invalid_interval(client: TestClient):
    """Test historical P&L with invalid interval"""
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=7)).isoformat()
    end_date = now.isoformat()
    
    response = client.get(
        f"/api/v1/floor/pnl/history?start_date={start_date}&end_date={end_date}&interval=invalid"
    )
    
    assert response.status_code == 400
    assert "Invalid interval" in response.json()['detail']


def test_get_historical_pnl_missing_dates(client: TestClient):
    """Test historical P&L with missing required dates"""
    response = client.get("/api/v1/floor/pnl/history")
    
    assert response.status_code == 422  # Validation error


def test_get_realized_pnl(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test realized P&L endpoint"""
    # Create profitable trade
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
        price=Decimal('52000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc) + timedelta(hours=1)
    ))
    session.commit()
    
    response = client.get("/api/v1/floor/pnl/realized")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['realized_pnl'] == 2000.0


def test_get_realized_pnl_with_coin_filter(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test realized P&L with coin filter"""
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
        quantity=Decimal('1.0'),
        price=Decimal('3000.00'),
        filled_quantity=Decimal('1.0'),
        status='filled',
        filled_at=datetime.now(timezone.utc)
    ))
    session.commit()
    
    response = client.get("/api/v1/floor/pnl/realized?coin_type=BTC")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include BTC trade
    assert data['realized_pnl'] == 1000.0


def test_get_unrealized_pnl_no_positions(client: TestClient):
    """Test unrealized P&L with no positions"""
    response = client.get("/api/v1/floor/pnl/unrealized")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['unrealized_pnl'] == 0.0


def test_get_unrealized_pnl_with_position(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test unrealized P&L with open position"""
    # Create position
    position = Position(
        user_id=test_user.id,
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
    
    response = client.get("/api/v1/floor/pnl/unrealized")
    
    assert response.status_code == 200
    data = response.json()
    
    # Expected: (52000 - 50000) * 1.0 = 2000
    assert data['unrealized_pnl'] == 2000.0


def test_get_unrealized_pnl_with_coin_filter(
    client: TestClient,
    test_user: User,
    session: Session
):
    """Test unrealized P&L with coin filter"""
    # BTC position
    session.add(Position(
        user_id=test_user.id,
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
        user_id=test_user.id,
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
    
    response = client.get("/api/v1/floor/pnl/unrealized?coin_type=BTC")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include BTC position: 1000
    assert data['unrealized_pnl'] == 1000.0
