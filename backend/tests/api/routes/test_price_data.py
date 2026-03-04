"""Tests for price data API endpoint."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import PriceData5Min


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


@pytest.fixture
def price_data_multiple_coins(session: Session) -> None:
    """Create sample price data with multiple distinct coin types."""
    now = datetime.now(timezone.utc)

    for coin in ["BTC", "ETH", "BTC", "SOL", "ETH"]:
        record = PriceData5Min(
            coin_type=coin,
            bid=Decimal("1000.00"),
            ask=Decimal("1010.00"),
            last=Decimal("1005.00"),
            timestamp=now,
        )
        session.add(record)

    session.commit()


def test_available_coins_returns_distinct_types(
    client: TestClient, price_data_multiple_coins: None
) -> None:
    """Test available-coins returns distinct coin symbols in sorted order."""
    response = client.get("/api/v1/utils/available-coins/")
    assert response.status_code == 200
    data = response.json()
    assert "coins" in data
    assert data["coins"] == ["BTC", "ETH", "SOL"]  # Should be distinct and sorted


def test_available_coins_empty_db(client: TestClient) -> None:
    """Test available-coins returns empty list when no price data exists."""
    response = client.get("/api/v1/utils/available-coins/")
    assert response.status_code == 200
    data = response.json()
    assert data["coins"] == []


def test_price_data_ledger_filter_exchange(
    client: TestClient, price_data_sample: None
) -> None:
    """Test price-data with ledger=exchange returns data normally."""
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=BTC&ledger=exchange&start_date=2026-02-01T00:00:00Z&end_date=2026-03-02T23:59:59Z"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["total_points"] > 0


def test_price_data_ledger_filter_human(client: TestClient, price_data_sample: None) -> None:
    """Test price-data with ledger=human returns empty data (no price data from human ledger)."""
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=BTC&ledger=human&start_date=2026-02-01T00:00:00Z&end_date=2026-03-02T23:59:59Z"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total_points"] == 0
