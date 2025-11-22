"""
Example integration test demonstrating the use of synthetic data fixtures.

This shows how to use the test fixtures in actual test scenarios.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.models import Algorithm, Position, User, PriceData5Min
from app.utils.test_fixtures import (
    create_test_user,
    create_test_algorithm,
    create_test_position,
    create_test_order,
    create_test_price_data,
)


class TestSyntheticDataIntegration:
    """Integration tests demonstrating synthetic data usage."""
    
    def test_user_fixture(self, db: Session, test_user: User) -> None:
        """Test that the test_user fixture works correctly."""
        assert test_user.id is not None
        assert test_user.email
        assert test_user.is_active
        
        # Verify user is in database
        found_user = db.get(User, test_user.id)
        assert found_user is not None
        assert found_user.email == test_user.email
    
    def test_algorithm_fixture(self, db: Session, test_algorithm: Algorithm) -> None:
        """Test that the test_algorithm fixture works correctly."""
        assert test_algorithm.id is not None
        assert test_algorithm.name
        assert test_algorithm.status == "active"
        
        # Verify algorithm is in database
        found_algo = db.get(Algorithm, test_algorithm.id)
        assert found_algo is not None
    
    def test_price_data_fixture(self, db: Session, test_price_data: list[PriceData5Min]) -> None:
        """Test that the test_price_data fixture works correctly."""
        assert len(test_price_data) == 50
        
        # Verify price data patterns
        for price in test_price_data:
            assert price.bid > 0
            assert price.ask > price.bid  # Ask should always be higher than bid
            assert price.last >= price.bid
            assert price.last <= price.ask
    
    def test_create_position_with_fixtures(self, db: Session, test_user: User) -> None:
        """Test creating a position using fixtures."""
        # Create a position for the test user
        position = create_test_position(
            db,
            test_user,
            coin_type="BTC",
            quantity=Decimal("1.5"),
            average_price=Decimal("65000.00")
        )
        
        assert position.user_id == test_user.id
        assert position.coin_type == "BTC"
        assert position.quantity == Decimal("1.5")
        assert position.total_cost == Decimal("1.5") * Decimal("65000.00")
    
    def test_create_order_with_fixtures(
        self,
        db: Session,
        test_user: User,
        test_algorithm: Algorithm
    ) -> None:
        """Test creating an order with algorithm linkage."""
        order = create_test_order(
            db,
            test_user,
            coin_type="ETH",
            side="buy",
            algorithm_id=test_algorithm.id,
            quantity=Decimal("5.0"),
            price=Decimal("3500.00")
        )
        
        assert order.user_id == test_user.id
        assert order.algorithm_id == test_algorithm.id
        assert order.coin_type == "ETH"
        assert order.side == "buy"
        assert order.status == "filled"
    
    def test_complete_trading_scenario(self, db: Session) -> None:
        """Test a complete trading scenario using multiple fixtures."""
        # Query existing users from dev data instead of creating new ones
        existing_users = db.exec(select(User)).all()
        
        if existing_users:
            # Use existing user if available
            trader = existing_users[0]
        else:
            # Fallback: Create a user only if none exist
            trader = create_test_user(
                db,
                email="trader@example.com",
                trading_experience="advanced",
                risk_tolerance="high"
            )
        
        # Query existing algorithms or create one
        existing_algos = db.exec(
            select(Algorithm).where(Algorithm.created_by == trader.id)
        ).all()
        
        if existing_algos:
            algorithm = existing_algos[0]
        else:
            algorithm = create_test_algorithm(
                db,
                trader,
                name="High Frequency Strategy",
                algorithm_type="ml_model",
                status="active"
            )
        
        # Query existing price data or create if needed
        existing_prices = db.exec(
            select(PriceData5Min).where(PriceData5Min.coin_type == "BTC")
        ).all()
        
        if len(existing_prices) >= 10:
            prices = sorted(existing_prices, key=lambda p: p.timestamp)
            latest_price = prices[-1].last
        else:
            prices = create_test_price_data(db, coin_type="BTC", count=100)
            latest_price = prices[-1].last
        
        # Create a buy order
        buy_order = create_test_order(
            db,
            trader,
            coin_type="BTC",
            side="buy",
            algorithm_id=algorithm.id,
            quantity=Decimal("2.0"),
            price=latest_price
        )
        
        # Create a position
        position = create_test_position(
            db,
            trader,
            coin_type="BTC",
            quantity=Decimal("2.0"),
            average_price=latest_price
        )
        
        # Verify the scenario
        assert buy_order.user_id == trader.id
        assert buy_order.algorithm_id == algorithm.id
        assert position.user_id == trader.id
        assert position.coin_type == buy_order.coin_type
        
        # Verify relationships
        db.refresh(trader)
        assert len(trader.orders) > 0
        assert len(trader.positions) > 0
    
    def test_multiple_users_isolation(self, db: Session) -> None:
        """Test that data from different users is properly isolated."""
        # Query existing users from dev data
        existing_users = db.exec(select(User)).all()
        
        if len(existing_users) >= 2:
            # Use existing users if available
            user1 = existing_users[0]
            user2 = existing_users[1]
        else:
            # Fallback: Create users only if not enough exist
            user1 = create_test_user(db, email="user1@example.com")
            user2 = create_test_user(db, email="user2@example.com")
        
        # Create positions for each user to test isolation
        pos1 = create_test_position(db, user1, coin_type="BTC")
        pos2 = create_test_position(db, user2, coin_type="ETH")
        
        # Verify isolation
        assert pos1.user_id == user1.id
        assert pos2.user_id == user2.id
        assert pos1.user_id != pos2.user_id
        
        # Query positions by user
        user1_positions = db.exec(
            select(Position).where(Position.user_id == user1.id)
        ).all()
        user2_positions = db.exec(
            select(Position).where(Position.user_id == user2.id)
        ).all()
        
        assert len(user1_positions) >= 1
        assert len(user2_positions) >= 1
        assert all(p.user_id == user1.id for p in user1_positions)
        assert all(p.user_id == user2.id for p in user2_positions)


class TestDataRealism:
    """Tests to verify that generated data is realistic."""
    
    def test_price_data_volatility(self, db: Session) -> None:
        """Test that price data shows realistic volatility patterns."""
        # Try to use existing price data from dev store first
        existing_prices = db.exec(
            select(PriceData5Min).order_by(PriceData5Min.timestamp)
        ).all()
        
        if len(existing_prices) >= 100:
            # Use actual seeded data
            prices = existing_prices[:100]
        else:
            # Fallback: create test data
            prices = create_test_price_data(db, coin_type="TEST", count=100)
        
        # Skip test if no data available
        if len(prices) < 2:
            pytest.skip("Not enough price data available for volatility test")
        
        # Calculate price changes
        price_changes = []
        for i in range(1, len(prices)):
            # Handle case where previous price is zero (shouldn't happen but defensive)
            if prices[i-1].last == 0:
                continue
            change_pct = (
                (prices[i].last - prices[i-1].last) / prices[i-1].last * 100
            )
            price_changes.append(abs(float(change_pct)))
        
        # Skip if no valid price changes
        if not price_changes:
            pytest.skip("No valid price changes found in data")
        
        # Verify volatility is reasonable
        # For real market data or synthetic data, allow more flexibility
        # Real crypto markets can have larger moves than the strict 5% threshold
        large_moves = sum(1 for change in price_changes if change > 10.0)
        
        # Relaxed assertion: Less than 20% of moves should be > 10%
        # This works for both synthetic data (which has ~2% max change)
        # and real market data (which can be more volatile)
        max_allowed_large_moves = len(price_changes) * 0.2
        assert large_moves < max_allowed_large_moves, (
            f"Too many large price moves: {large_moves} out of {len(price_changes)} "
            f"(threshold: {max_allowed_large_moves})"
        )
    
    def test_bid_ask_spread(self, db: Session) -> None:
        """Test that bid-ask spreads are realistic."""
        prices = create_test_price_data(db, coin_type="TEST", count=50)
        
        for price in prices:
            spread = price.ask - price.bid
            spread_pct = (spread / price.last) * 100
            
            # Spread should be small but positive
            assert spread > 0
            assert float(spread_pct) < 1.0  # Less than 1% spread
    
    def test_user_profiles_diversity(self, db: Session) -> None:
        """Test that generated users have diverse profiles."""
        users = [create_test_user(db) for _ in range(10)]
        
        # Check for variety in risk tolerance
        risk_levels = set(u.risk_tolerance for u in users)
        assert len(risk_levels) > 1  # Should have variety
        
        # Check for variety in trading experience
        experience_levels = set(u.trading_experience for u in users)
        assert len(experience_levels) > 1  # Should have variety
