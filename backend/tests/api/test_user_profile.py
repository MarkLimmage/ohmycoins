"""
Tests for user profile management endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings


def test_read_user_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test reading user profile"""
    r = client.get(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200
    profile = r.json()
    assert "email" in profile
    assert "timezone" in profile
    assert "preferred_currency" in profile
    assert "risk_tolerance" in profile
    assert "trading_experience" in profile
    assert "has_coinspot_credentials" in profile
    # Default values
    assert profile["timezone"] == "UTC"
    assert profile["preferred_currency"] == "AUD"
    assert profile["risk_tolerance"] == "medium"
    assert profile["trading_experience"] == "beginner"


def test_update_user_profile(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test updating user profile"""
    data = {
        "full_name": "Updated Name",
        "timezone": "Australia/Sydney",
        "preferred_currency": "USD",
        "risk_tolerance": "high",
        "trading_experience": "advanced",
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    profile = r.json()
    assert profile["full_name"] == "Updated Name"
    assert profile["timezone"] == "Australia/Sydney"
    assert profile["preferred_currency"] == "USD"
    assert profile["risk_tolerance"] == "high"
    assert profile["trading_experience"] == "advanced"


def test_update_user_profile_partial(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test partial profile update"""
    data = {
        "risk_tolerance": "low",
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 200
    profile = r.json()
    assert profile["risk_tolerance"] == "low"
    # Other fields should remain unchanged
    assert profile["timezone"] in ["UTC", "Australia/Sydney"]
    assert profile["preferred_currency"] in ["AUD", "USD"]


def test_update_profile_invalid_risk_tolerance(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test validation of risk tolerance field"""
    data = {
        "risk_tolerance": "extreme",  # Invalid value
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 422


def test_update_profile_invalid_experience(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test validation of trading experience field"""
    data = {
        "trading_experience": "expert",  # Invalid value
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 422


def test_update_profile_invalid_timezone(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test validation of timezone field"""
    data = {
        "timezone": "Invalid/Timezone",  # Invalid value
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 422


def test_update_profile_invalid_currency(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test validation of currency field"""
    data = {
        "preferred_currency": "INVALID",  # Invalid value
    }
    r = client.patch(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
        json=data,
    )
    assert r.status_code == 422


def test_profile_without_credentials(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test profile shows no credentials by default"""
    r = client.get(
        f"{settings.API_V1_STR}/users/me/profile",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200
    profile = r.json()
    assert profile["has_coinspot_credentials"] is False
