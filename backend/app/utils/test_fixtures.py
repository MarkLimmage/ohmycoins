"""
Test fixtures for Oh My Coins.

Provides reusable test data fixtures that can be used across tests.
These fixtures use the seeding utilities but are optimized for fast test execution.
"""

import os
import random
import uuid
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from faker import Faker
from sqlmodel import Session

from app.core.security import get_password_hash
from app.models import (
    Algorithm,
    Order,
    Position,
    PriceData5Min,
    User,
)

# Test data seed - can be overridden with TEST_DATA_SEED env var for reproducibility
TEST_DATA_SEED = int(os.getenv("TEST_DATA_SEED", "100"))

fake = Faker()
Faker.seed(TEST_DATA_SEED)
random.seed(TEST_DATA_SEED)


def create_test_user(
    session: Session,
    email: str | None = None,
    is_superuser: bool = False,
    **kwargs: Any
) -> User:
    """Create a test user with sensible defaults."""
    if email is None:
        # Use UUID to ensure uniqueness even with persistent dev data
        email = f"test-{uuid.uuid4()}@example.com"

    user = User(
        email=email,
        hashed_password=get_password_hash("TestPassword123!"),
        full_name=kwargs.get("full_name", fake.name()),
        is_active=kwargs.get("is_active", True),
        is_superuser=is_superuser,
        timezone=kwargs.get("timezone", "UTC"),
        preferred_currency=kwargs.get("preferred_currency", "AUD"),
        risk_tolerance=kwargs.get("risk_tolerance", random.choice(["low", "medium", "high"])),
        trading_experience=kwargs.get("trading_experience", random.choice(["beginner", "intermediate", "advanced"])),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    return user


def create_test_price_data(
    session: Session,
    coin_type: str = "BTC",
    count: int = 100,
    start_price: Decimal = Decimal("65000.00"),
) -> list[PriceData5Min]:
    """Create test price data with realistic patterns."""
    prices = []
    current_time = datetime.now(timezone.utc) - timedelta(hours=count // 12)
    current_price = start_price

    for i in range(count):
        # Add some volatility
        change = Decimal(random.uniform(-0.02, 0.02))
        current_price = current_price * (Decimal("1") + change)

        spread = current_price * Decimal("0.001")

        price_data = PriceData5Min(
            timestamp=current_time,
            coin_type=coin_type,
            bid=current_price - spread,
            ask=current_price + spread,
            last=current_price,
            created_at=datetime.now(timezone.utc),
        )
        session.add(price_data)
        prices.append(price_data)

        current_time += timedelta(minutes=5)

    session.flush()
    for price in prices:
        session.refresh(price)

    return prices


def create_test_algorithm(
    session: Session,
    user: User,
    **kwargs: Any
) -> Algorithm:
    """Create a test algorithm."""
    algorithm = Algorithm(
        created_by=user.id,
        name=kwargs.get("name", f"Test Strategy {fake.word()}"),
        description=kwargs.get("description", "Test algorithm for unit tests"),
        algorithm_type=kwargs.get("algorithm_type", "ml_model"),
        version=kwargs.get("version", "1.0.0"),
        status=kwargs.get("status", "active"),
        configuration_json=kwargs.get("configuration_json", '{"test": true}'),
        default_execution_frequency=kwargs.get("default_execution_frequency", 300),
        default_position_limit=kwargs.get("default_position_limit", Decimal("5000.00")),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(algorithm)
    session.flush()
    session.refresh(algorithm)
    return algorithm


def create_test_position(
    session: Session,
    user: User,
    coin_type: str = "BTC",
    **kwargs: Any
) -> Position:
    """Create a test position."""
    quantity = kwargs.get("quantity", Decimal("0.5"))
    avg_price = kwargs.get("average_price", Decimal("65000.00"))

    position = Position(
        user_id=user.id,
        coin_type=coin_type,
        quantity=quantity,
        average_price=avg_price,
        total_cost=quantity * avg_price,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(position)
    session.flush()
    session.refresh(position)
    return position


def create_test_order(
    session: Session,
    user: User,
    coin_type: str = "BTC",
    **kwargs: Any
) -> Order:
    """Create a test order."""
    quantity = kwargs.get("quantity", Decimal("0.1"))
    price = kwargs.get("price", Decimal("65000.00"))

    order = Order(
        user_id=user.id,
        algorithm_id=kwargs.get("algorithm_id"),
        coin_type=coin_type,
        side=kwargs.get("side", "buy"),
        order_type=kwargs.get("order_type", "market"),
        quantity=quantity,
        price=price,
        filled_quantity=kwargs.get("filled_quantity", quantity),
        status=kwargs.get("status", "filled"),
        coinspot_order_id=kwargs.get("coinspot_order_id", f"CS{str(fake.uuid4())[:8]}"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(order)
    session.flush()
    session.refresh(order)
    return order


# Pytest fixtures for easy use in tests
@pytest.fixture
def test_user(db: Session) -> Generator[User, None, None]:
    """Fixture that creates a test user."""
    user = create_test_user(db)
    yield user


@pytest.fixture
def test_superuser(db: Session) -> Generator[User, None, None]:
    """Fixture that creates a test superuser."""
    user = create_test_user(db, email="superuser@test.com", is_superuser=True)
    yield user


@pytest.fixture
def test_price_data(db: Session) -> Generator[list[PriceData5Min], None, None]:
    """Fixture that creates test price data."""
    prices = create_test_price_data(db, count=50)
    yield prices


@pytest.fixture
def test_algorithm(db: Session, test_user: User) -> Generator[Algorithm, None, None]:
    """Fixture that creates a test algorithm."""
    algo = create_test_algorithm(db, test_user)
    yield algo
