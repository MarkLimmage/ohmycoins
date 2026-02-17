import os
from collections.abc import Generator

# Set encryption key BEFORE any app imports
# This is for testing only - production uses AWS Secrets Manager
os.environ["ENCRYPTION_KEY"] = "_KLoPGOzT2wEFRDU1Rmb7-85GIDf4QJUVGPzkTKRTis="

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import (
    AgentArtifact,
    AgentSession,
    AgentSessionMessage,
    Algorithm,
    AuditLog,
    CatalystEvents,
    CoinspotCredentials,
    DeployedAlgorithm,
    NewsSentiment,
    Order,
    Position,
    PriceData5Min,
    SmartMoneyFlow,
    StrategyPromotion,
    User,
    UserLLMCredentials,
)

# Import test fixtures for use across tests
from app.utils.test_fixtures import (
    create_test_algorithm,
    create_test_price_data,
    create_test_user,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db_init() -> None:
    SQLModel.metadata.create_all(engine)
    yield
    # No teardown here as we just want the schema created once

@pytest.fixture(scope="function", autouse=True)
@pytest.mark.usefixtures("db_init")
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Clean up test data with cascading deletes in correct order
        # Delete child records first to avoid foreign key violations
        try:
            # Delete agent-related data
            session.execute(delete(AgentArtifact))
            session.execute(delete(AgentSessionMessage))
            session.execute(delete(AgentSession))

            # Delete trading-related data
            session.execute(delete(Order))
            session.execute(delete(Position))
            session.execute(delete(DeployedAlgorithm))
            session.execute(delete(StrategyPromotion))

            # Delete algorithms
            session.execute(delete(Algorithm))

            # Delete credentials
            session.execute(delete(CoinspotCredentials))
            session.execute(delete(UserLLMCredentials))

            # Delete ledger data
            session.execute(delete(CatalystEvents))
            session.execute(delete(NewsSentiment))
            session.execute(delete(SmartMoneyFlow))

            # Delete audit logs
            session.execute(delete(AuditLog))

            # Finally delete users
            session.execute(delete(User))

            session.commit()
        except Exception:
            session.rollback()
            # Log but don't fail - test cleanup is best effort


@pytest.fixture(scope="function")
def session(db: Session) -> Generator[Session, None, None]:
    """Alias for db fixture to support tests expecting 'session' parameter with transaction isolation"""
    # Start a savepoint for this test
    db.begin_nested()
    try:
        yield db
    finally:
        # Always rollback the savepoint to undo any changes made during the test
        # This prevents test data from persisting and causing conflicts
        try:
            db.rollback()
        except Exception:
            # If rollback fails, the session is already in a bad state
            # Close and create a new session
            db.close()
            pass

        # Additional cleanup: explicitly delete test-created price data
        # to ensure test isolation (savepoint rollback doesn't always work properly
        # for PriceData5Min, likely due to timestamp/cascade behavior)
        # Note: We use a fresh transaction context since the savepoint is rolled back
        try:
            db.execute(delete(PriceData5Min))
            db.commit()
        except Exception:
            # Ignore cleanup errors - they shouldn't prevent test execution
            # This could happen if the session is already in a bad state
            try:
                db.rollback()
            except Exception:
                pass


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="function")
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
def normal_user(db: Session) -> Generator[User, None, None]:
    """Fixture that creates a normal (non-superuser) test user for use in tests."""
    user = create_test_user(db)
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
