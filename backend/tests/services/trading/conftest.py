"""
Shared fixtures for trading service tests
"""
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.models import User


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user with unique email for each test"""
    user = User(
        id=uuid4(),
        email=f"{uuid4()}@test.com",  # Use UUID to ensure uniqueness
        hashed_password="test_hash",
        is_active=True,
        is_superuser=False
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
