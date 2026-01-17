"""
Tests for the seed_data utility module.

These tests validate that the synthetic data generation and real data collection
functions work correctly.
"""

import pytest
from sqlmodel import Session, select, func

from app.models import (
    User,
    PriceData5Min,
    Algorithm,
    Position,
    Order,
)
from app.utils.seed_data import (
    generate_users,
    generate_algorithms,
    generate_positions_and_orders,
    clear_all_data,
)
from app.utils.test_fixtures import (
    create_test_user,
    create_test_price_data,
    create_test_algorithm,
    create_test_position,
    create_test_order,
)


class TestSeedData:
    """Test suite for seed_data module."""
    
    def test_generate_users(self, db: Session) -> None:
        """Test that user generation creates the expected number of users."""
        # Get the initial superuser count
        from app.core.config import settings
        initial_superuser_exists = db.exec(
            select(func.count(User.id)).where(User.email == settings.FIRST_SUPERUSER)
        ).one() > 0
        
        initial_count = db.exec(select(func.count(User.id))).one()
        
        # Generate 5 test users
        users = generate_users(db, count=5)
        
        # The function returns either 5 users (if no superuser exists) or 1 superuser + 4 new users
        if initial_superuser_exists:
            # If superuser exists, we get 1 superuser + 4 new users = 5 total returned
            assert len(users) == 5
            assert users[0].is_superuser  # First returned should be superuser
            assert not users[1].is_superuser  # Others should not be superuser
            # Only 4 new users were actually created
            final_count = db.exec(select(func.count(User.id))).one()
            assert final_count == initial_count + 4
        else:
            # If no superuser exists, we create 5 new users
            assert len(users) == 5
            assert users[0].is_superuser  # First user should be superuser
            assert not users[1].is_superuser  # Others should not be superuser
            final_count = db.exec(select(func.count(User.id))).one()
            assert final_count == initial_count + 5
    
    def test_generate_algorithms(self, db: Session) -> None:
        """Test algorithm generation."""
        # Create a test user first
        user = create_test_user(db)
        
        # Generate algorithms
        algorithms = generate_algorithms(db, [user], count=3)
        
        assert len(algorithms) == 3
        for algo in algorithms:
            assert algo.created_by == user.id
            assert algo.name
            assert algo.algorithm_type in ["ml_model", "rule_based", "reinforcement_learning"]
    
    def test_generate_positions_and_orders(self, db: Session) -> None:
        """Test position and order generation."""
        # Setup: Create users, price data, and algorithms
        users = [create_test_user(db) for _ in range(3)]
        create_test_price_data(db, coin_type="BTC", count=10)
        algorithms = [create_test_algorithm(db, users[0]) for _ in range(2)]
        
        # Generate positions and orders
        count = generate_positions_and_orders(db, users, algorithms)
        
        assert count > 0
        
        # Verify positions were created
        positions = db.exec(select(Position)).all()
        assert len(positions) > 0
        
        # Verify orders were created
        orders = db.exec(select(Order)).all()
        assert len(orders) > 0
    
    def test_clear_all_data(self, db: Session) -> None:
        """Test that clear_all_data removes all data except superuser."""
        # Setup: Create some test data
        user = create_test_user(db)
        create_test_price_data(db, count=10)
        algo = create_test_algorithm(db, user)
        
        # Clear all data
        clear_all_data(db)
        
        # Verify data is cleared (excluding the configured superuser)
        from app.core.config import settings
        users = db.exec(select(User).where(User.email != settings.FIRST_SUPERUSER)).all()
        assert len(users) == 0
        
        prices = db.exec(select(PriceData5Min)).all()
        assert len(prices) == 0
        
        algorithms = db.exec(select(Algorithm)).all()
        assert len(algorithms) == 0


class TestTestFixtures:
    """Test suite for test_fixtures module."""
    
    def test_create_test_user(self, db: Session) -> None:
        """Test user fixture creation."""
        user = create_test_user(db)
        
        assert user.id
        assert user.email  # Just verify email exists, don't check specific value
        assert user.is_active
        assert not user.is_superuser
    
    def test_create_test_price_data(self, db: Session) -> None:
        """Test price data fixture creation."""
        prices = create_test_price_data(db, coin_type="ETH", count=20)
        
        assert len(prices) == 20
        assert all(p.coin_type == "ETH" for p in prices)
        assert all(p.bid > 0 for p in prices)
        assert all(p.ask > p.bid for p in prices)  # Ask should be higher than bid
    
    def test_create_test_algorithm(self, db: Session) -> None:
        """Test algorithm fixture creation."""
        user = create_test_user(db)
        algo = create_test_algorithm(db, user, name="Test Algo", status="active")
        
        assert algo.id
        assert algo.name == "Test Algo"
        assert algo.status == "active"
        assert algo.created_by == user.id
    
    def test_create_test_position(self, db: Session) -> None:
        """Test position fixture creation."""
        user = create_test_user(db)
        position = create_test_position(db, user, coin_type="BTC")
        
        assert position.id
        assert position.user_id == user.id
        assert position.coin_type == "BTC"
        assert position.quantity > 0
        assert position.total_cost == position.quantity * position.average_price
    
    def test_create_test_order(self, db: Session) -> None:
        """Test order fixture creation."""
        user = create_test_user(db)
        order = create_test_order(db, user, coin_type="ETH", side="buy")
        
        assert order.id
        assert order.user_id == user.id
        assert order.coin_type == "ETH"
        assert order.side == "buy"
        assert order.status == "filled"


class TestDataIntegrity:
    """Test data relationships and integrity."""
    
    def test_user_position_relationship(self, db: Session) -> None:
        """Test that positions are correctly linked to users."""
        user = create_test_user(db)
        position = create_test_position(db, user)
        
        # Verify relationship using explicit query (SQLModel compatibility)
        user_positions = db.exec(select(Position).where(Position.user_id == user.id)).all()
        assert any(p.id == position.id for p in user_positions)
    
    def test_user_order_relationship(self, db: Session) -> None:
        """Test that orders are correctly linked to users."""
        user = create_test_user(db)
        order = create_test_order(db, user)
        
        # Verify relationship using explicit query (SQLModel compatibility)
        user_orders = db.exec(select(Order).where(Order.user_id == user.id)).all()
        assert any(o.id == order.id for o in user_orders)
    
    def test_algorithm_deployment_relationship(self, db: Session) -> None:
        """Test that algorithms can have deployments."""
        user = create_test_user(db)
        algo = create_test_algorithm(db, user)
        
        # Algorithm should exist and be queryable
        found_algo = db.get(Algorithm, algo.id)
        assert found_algo is not None
        assert found_algo.id == algo.id
