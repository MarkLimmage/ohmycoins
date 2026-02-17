import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.crud import create_user
from app.models import UserCreate
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email, random_lower_string


@pytest.fixture
def disabled_whitelist():
    original_val = settings.EMAIL_WHITELIST_ENABLED
    settings.EMAIL_WHITELIST_ENABLED = False
    yield
    settings.EMAIL_WHITELIST_ENABLED = original_val

@pytest.fixture
def enabled_whitelist():
    original_val = settings.EMAIL_WHITELIST_ENABLED
    settings.EMAIL_WHITELIST_ENABLED = True
    yield
    settings.EMAIL_WHITELIST_ENABLED = original_val

def test_whitelist_disabled_by_default(client: TestClient, db: Session, disabled_whitelist) -> None:
    # Ensure whitelist is disabled (default state)
    
        email = random_email()
        password = random_lower_string()
        user_in = UserCreate(email=email, password=password)
        create_user(session=db, user_create=user_in)

        # Get token
        headers = authentication_token_from_email(client=client, email=email, db=db)

        # Access protected endpoint
        r = client.post(f"{settings.API_V1_STR}/login/test-token", headers=headers)
        assert r.status_code == 200


def test_whitelist_enabled_user_blocked(client: TestClient, db: Session, enabled_whitelist) -> None:
    # Enable whitelist
    original_whitelist = settings.EMAIL_WHITELIST
    settings.EMAIL_WHITELIST = ["allowed@example.com"]

    try:
        # Create a user NOT in whitelist
        email = random_email()
        password = random_lower_string()
        user_in = UserCreate(email=email, password=password)
        create_user(session=db, user_create=user_in)

        # Get token
        headers = authentication_token_from_email(client=client, email=email, db=db)

        # Access protected endpoint - should fail
        r = client.post(f"{settings.API_V1_STR}/login/test-token", headers=headers)
        assert r.status_code == 403
    finally:
        settings.EMAIL_WHITELIST = original_whitelist


def test_whitelist_enabled_user_allowed(client: TestClient, db: Session, enabled_whitelist) -> None:
    # Enable whitelist
    original_whitelist = settings.EMAIL_WHITELIST
    settings.EMAIL_WHITELIST = ["allowed@example.com", "another@example.com"]

    try:
        # Create a user IN whitelist
        email = "allowed@example.com"

        # Access protected endpoint
        r = client.post(f"{settings.API_V1_STR}/login/test-token", headers=headers)
        assert r.status_code == 403
        assert r.json()["detail"] == "Access denied. Account is not whitelisted."
    finally:
        settings.EMAIL_WHITELIST_ENABLED = original_enabled
        settings.EMAIL_WHITELIST = original_whitelist

def test_whitelist_enabled_user_allowed(client: TestClient, db: Session) -> None:
    # Enable whitelist
    original_enabled = settings.EMAIL_WHITELIST_ENABLED
    original_whitelist = settings.EMAIL_WHITELIST

    email = random_email()
    settings.EMAIL_WHITELIST_ENABLED = True
    settings.EMAIL_WHITELIST = [email, "another@example.com"]

    try:
        # Create a user IN whitelist
        password = random_lower_string()
        user_in = UserCreate(email=email, password=password)
        create_user(session=db, user_create=user_in)

        # Get token
        headers = authentication_token_from_email(client=client, email=email, db=db)

        # Access protected endpoint
        r = client.post(f"{settings.API_V1_STR}/login/test-token", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == email
    finally:
        settings.EMAIL_WHITELIST_ENABLED = original_enabled
        settings.EMAIL_WHITELIST = original_whitelist
