"""
Tests for Coinspot credentials API endpoints

Tests CRUD operations and validation for Coinspot credentials.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.db import engine
from app.models import CoinspotCredentials, UserCreate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


class TestCredentialsCreate:
    """Tests for POST /api/v1/credentials/coinspot"""

    def test_create_credentials_success(self, client: TestClient, db: Session) -> None:
        """Test successful credential creation"""
        # Create a test user and get auth headers
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        user = crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create credentials
        data = {
            "api_key": "test_api_key_12345",
            "api_secret": "test_api_secret_67890"
        }

        response = client.post(
            "/api/v1/credentials/coinspot",
            headers=headers,
            json=data
        )

        assert response.status_code == 200
        content = response.json()
        assert "id" in content
        assert content["user_id"] == str(user.id)
        assert content["api_key_masked"].endswith("2345")
        assert content["is_validated"] is False
        assert "created_at" in content
        assert "updated_at" in content

    def test_create_credentials_already_exist(self, client: TestClient, db: Session) -> None:
        """Test that creating credentials when they already exist fails"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        user = crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        data = {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        }

        # Create first time - should succeed
        response = client.post(
            "/api/v1/credentials/coinspot",
            headers=headers,
            json=data
        )
        assert response.status_code == 200

        # Try to create again - should fail
        response = client.post(
            "/api/v1/credentials/coinspot",
            headers=headers,
            json=data
        )
        assert response.status_code == 400
        assert "already exist" in response.json()["detail"].lower()

    def test_create_credentials_unauthorized(self, client: TestClient) -> None:
        """Test that creating credentials without auth fails"""
        data = {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        }

        response = client.post(
            "/api/v1/credentials/coinspot",
            json=data
        )
        assert response.status_code == 401


class TestCredentialsGet:
    """Tests for GET /api/v1/credentials/coinspot"""

    def test_get_credentials_success(self, client: TestClient, db: Session) -> None:
        """Test successful credential retrieval"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        user = crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create credentials
        data = {
            "api_key": "test_api_key_abcdef",
            "api_secret": "test_api_secret"
        }
        client.post("/api/v1/credentials/coinspot", headers=headers, json=data)

        # Get credentials
        response = client.get("/api/v1/credentials/coinspot", headers=headers)

        assert response.status_code == 200
        content = response.json()
        assert content["api_key_masked"].endswith("cdef")
        assert "api_secret" not in content  # Secret should never be returned

    def test_get_credentials_not_found(self, client: TestClient, db: Session) -> None:
        """Test getting credentials when none exist"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        response = client.get("/api/v1/credentials/coinspot", headers=headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_credentials_unauthorized(self, client: TestClient) -> None:
        """Test that getting credentials without auth fails"""
        response = client.get("/api/v1/credentials/coinspot")
        assert response.status_code == 401


class TestCredentialsUpdate:
    """Tests for PUT /api/v1/credentials/coinspot"""

    def test_update_credentials_success(self, client: TestClient, db: Session) -> None:
        """Test successful credential update"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        user = crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create initial credentials
        data = {
            "api_key": "old_api_key",
            "api_secret": "old_api_secret"
        }
        client.post("/api/v1/credentials/coinspot", headers=headers, json=data)

        # Update credentials
        update_data = {
            "api_key": "new_api_key_xyz123",
            "api_secret": "new_api_secret"
        }
        response = client.put(
            "/api/v1/credentials/coinspot",
            headers=headers,
            json=update_data
        )

        assert response.status_code == 200
        content = response.json()
        assert content["api_key_masked"].endswith("z123")
        # Validation status should be reset
        assert content["is_validated"] is False

    def test_update_credentials_partial(self, client: TestClient, db: Session) -> None:
        """Test partial credential update (only API key)"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create initial credentials
        data = {
            "api_key": "old_api_key_9999",
            "api_secret": "old_api_secret"
        }
        client.post("/api/v1/credentials/coinspot", headers=headers, json=data)

        # Update only API key
        update_data = {"api_key": "new_api_key_8888"}
        response = client.put(
            "/api/v1/credentials/coinspot",
            headers=headers,
            json=update_data
        )

        assert response.status_code == 200
        content = response.json()
        assert content["api_key_masked"].endswith("8888")

    def test_update_credentials_not_found(self, client: TestClient, db: Session) -> None:
        """Test updating credentials when none exist"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        update_data = {
            "api_key": "new_api_key",
            "api_secret": "new_api_secret"
        }
        response = client.put(
            "/api/v1/credentials/coinspot",
            headers=headers,
            json=update_data
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCredentialsDelete:
    """Tests for DELETE /api/v1/credentials/coinspot"""

    def test_delete_credentials_success(self, client: TestClient, db: Session) -> None:
        """Test successful credential deletion"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create credentials
        data = {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        }
        client.post("/api/v1/credentials/coinspot", headers=headers, json=data)

        # Delete credentials
        response = client.delete("/api/v1/credentials/coinspot", headers=headers)

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # Verify credentials are deleted
        get_response = client.get("/api/v1/credentials/coinspot", headers=headers)
        assert get_response.status_code == 404

    def test_delete_credentials_not_found(self, client: TestClient, db: Session) -> None:
        """Test deleting credentials when none exist"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        response = client.delete("/api/v1/credentials/coinspot", headers=headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCredentialsValidation:
    """Tests for POST /api/v1/credentials/coinspot/validate"""

    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, client: TestClient, db: Session) -> None:
        """Test successful credential validation"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        user = crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create credentials
        data = {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        }
        client.post("/api/v1/credentials/coinspot", headers=headers, json=data)

        # Mock successful Coinspot API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "balances": {}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            response = client.post(
                "/api/v1/credentials/coinspot/validate",
                headers=headers
            )

        assert response.status_code == 200
        assert "validated successfully" in response.json()["message"].lower()

        # Verify validation status updated in database
        with Session(engine) as session:
            credentials = session.exec(
                select(CoinspotCredentials).where(
                    CoinspotCredentials.user_id == user.id
                )
            ).first()
            assert credentials is not None
            assert credentials.is_validated is True
            assert credentials.last_validated_at is not None

    def test_validate_credentials_not_found(self, client: TestClient, db: Session) -> None:
        """Test validation when credentials don't exist"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        response = client.post(
            "/api/v1/credentials/coinspot/validate",
            headers=headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_validate_credentials_invalid(self, client: TestClient, db: Session) -> None:
        """Test validation with invalid credentials"""
        user_email = random_email()
        user_password = random_lower_string()
        user_in = UserCreate(email=user_email, password=user_password)
        crud.create_user(session=db, user_create=user_in)
        headers = user_authentication_headers(client=client, email=user_email, password=user_password)

        # Create credentials
        data = {
            "api_key": "invalid_key",
            "api_secret": "invalid_secret"
        }
        client.post("/api/v1/credentials/coinspot", headers=headers, json=data)

        # Mock failed Coinspot API response (401 Unauthorized)
        from httpx import HTTPStatusError, Request, Response

        mock_request = Request("POST", "https://www.coinspot.com.au/api/v2/ro/my/balances")
        mock_response = Response(401, request=mock_request)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "Unauthorized",
                    request=mock_request,
                    response=mock_response
                )
            )

            response = client.post(
                "/api/v1/credentials/coinspot/validate",
                headers=headers
            )

        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
