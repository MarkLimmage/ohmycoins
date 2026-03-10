"""Tests for backtest API endpoints."""

import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Algorithm, BacktestRun


@pytest.fixture
def auth_headers(client: TestClient, session: Session) -> dict[str, str]:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email
    email = random_email()
    return authentication_token_from_email(client=client, email=email, db=session)


@pytest.fixture
def user_id_from_headers(auth_headers: dict[str, str], client: TestClient) -> uuid.UUID:
    """Extract user ID from auth headers."""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    return uuid.UUID(response.json()["id"])


@pytest.fixture
def test_algorithm(session: Session, user_id_from_headers: uuid.UUID) -> Algorithm:
    """Create a test algorithm."""
    algo = Algorithm(
        name=f"Test Algo {uuid.uuid4().hex[:8]}",
        algorithm_type="rule_based",
        created_by=user_id_from_headers,
        configuration_json=json.dumps({"short_window": 5, "long_window": 10}),
    )
    session.add(algo)
    session.commit()
    session.refresh(algo)
    return algo


class TestBacktestAPI:
    @patch("app.api.routes.backtests.BacktestEngine")
    def test_create_backtest(
        self,
        mock_engine_cls: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        test_algorithm: Algorithm,
    ) -> None:
        """Test creating a backtest."""
        now = datetime.now(timezone.utc)
        mock_run = BacktestRun(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            algorithm_id=test_algorithm.id,
            coin_type="BTC",
            start_date=now - timedelta(days=30),
            end_date=now,
            initial_capital=Decimal("10000"),
            status="completed",
            results_json=json.dumps({"total_return": 0.05}),
            created_at=now,
        )
        mock_engine_cls.return_value.run.return_value = mock_run

        response = client.post(
            "/api/v1/floor/backtests",
            json={
                "algorithm_id": str(test_algorithm.id),
                "coin_type": "BTC",
                "start_date": (now - timedelta(days=30)).isoformat(),
                "end_date": now.isoformat(),
                "initial_capital": 10000,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_get_backtest_not_found(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test getting a non-existent backtest."""
        response = client.get(
            f"/api/v1/floor/backtests/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_list_backtests(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test listing backtests."""
        response = client.get(
            "/api/v1/floor/backtests",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_backtest_requires_auth(
        self,
        client: TestClient,
    ) -> None:
        """Test that backtest endpoints require authentication."""
        response = client.get(f"/api/v1/floor/backtests/{uuid.uuid4()}")
        assert response.status_code == 401
