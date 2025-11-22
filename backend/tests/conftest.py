from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import User, Algorithm, PriceData5Min
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

# Import test fixtures for use across tests
from app.utils.test_fixtures import (
    create_test_user,
    create_test_algorithm,
    create_test_position,
    create_test_order,
    create_test_price_data,
)


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Clean up users after tests
        statement = delete(User)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="function")
def session(db: Session) -> Generator[Session, None, None]:
    """Alias for db fixture to support tests expecting 'session' parameter"""
    yield db


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


# Test data fixtures for convenient use across tests
@pytest.fixture
def test_user(db: Session) -> Generator[User, None, None]:
    """Fixture that creates a test user for use in tests."""
    user = create_test_user(db)
    yield user


@pytest.fixture
def test_superuser(db: Session) -> Generator[User, None, None]:
    """Fixture that creates a test superuser for use in tests."""
    user = create_test_user(db, email="test_superuser@example.com", is_superuser=True)
    yield user


@pytest.fixture
def test_price_data(db: Session) -> Generator[list[PriceData5Min], None, None]:
    """Fixture that creates test price data for use in tests."""
    prices = create_test_price_data(db, count=50)
    yield prices


@pytest.fixture
def test_algorithm(db: Session, test_user: User) -> Generator[Algorithm, None, None]:
    """Fixture that creates a test algorithm for use in tests."""
    algo = create_test_algorithm(db, test_user)
    yield algo
