"""Tests for price data API endpoint."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.main import api_router
from app.main import app
from app.models import PriceData5Min
from decimal import Decimal


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def price_data_sample(session: Session) -> None:
    """Create sample price data."""
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=24)

    for i in range(5):
        record = PriceData5Min(
            coin_type="BTC",
            bid=Decimal("45000.00"),
            ask=Decimal("45010.00"),
            last=Decimal("45005.00") + Decimal(str(i * 100)),
            timestamp=base_time + timedelta(hours=i * 4),
        )
        session.add(record)

    session.commit()


def test_get_price_data(client: TestClient, price_data_sample: None) -> None:
    """Test getting price data for a coin."""
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=BTC&start_date=2026-02-01T00:00:00Z&end_date=2026-03-02T23:59:59Z&limit=10"
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total_points" in data
    assert len(data["data"]) > 0
    assert data["total_points"] > 0

    # Verify data structure
    point = data["data"][0]
    assert "timestamp" in point
    assert "coin_type" in point
    assert "price" in point
    assert point["coin_type"] == "BTC"
    assert isinstance(point["price"], (int, float))


def test_get_price_data_empty(client: TestClient) -> None:
    """Test getting price data with no matching records."""
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=NONEXISTENT&start_date=2026-02-01T00:00:00Z&end_date=2026-02-02T23:59:59Z"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total_points"] == 0


def test_get_price_data_limit(client: TestClient, price_data_sample: None) -> None:
    """Test limit parameter."""
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=BTC&start_date=2026-02-01T00:00:00Z&end_date=2026-03-02T23:59:59Z&limit=2"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2


def test_get_price_data_missing_coin_type(client: TestClient) -> None:
    """Test error when coin_type is missing."""
    response = client.get(
        "/api/v1/utils/price-data/?start_date=2026-02-01T00:00:00Z&end_date=2026-02-02T23:59:59Z"
    )

    assert response.status_code == 422  # Unprocessable Entity
