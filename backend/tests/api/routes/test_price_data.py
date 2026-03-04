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


def test_available_coins_returns_distinct_types(client: TestClient, session: Session) -> None:
    """Test available-coins returns distinct coin symbols in sorted order."""
    # Create test data directly (fixture data gets rolled back due to savepoint)
    base_time = datetime.now(timezone.utc)
    coins_data = [
        ("BTC", base_time),
        ("ETH", base_time + timedelta(minutes=1)),
        ("SOL", base_time + timedelta(minutes=2)),
    ]

    for coin, timestamp in coins_data:
        record = PriceData5Min(
            coin_type=coin,
            bid=Decimal("1000.00"),
            ask=Decimal("1010.00"),
            last=Decimal("1005.00"),
            timestamp=timestamp,
        )
        session.add(record)
    session.flush()  # Flush without commit to ensure data is visible in same transaction

    response = client.get("/api/v1/utils/available-coins/")
    assert response.status_code == 200
    data = response.json()
    assert "coins" in data
    assert data["coins"] == ["BTC", "ETH", "SOL"]  # Should be distinct and sorted


def test_available_coins_empty_db(client: TestClient) -> None:
    """Test available-coins returns empty list when no price data exists."""
    # This test doesn't use fixtures, so it should always have empty DB
    response = client.get("/api/v1/utils/available-coins/")
    assert response.status_code == 200
    data = response.json()
    assert data["coins"] == []


def test_price_data_ledger_filter_exchange(client: TestClient) -> None:
    """Test price-data with ledger=exchange parameter is accepted (returns empty without data)."""
    # Test that the ledger=exchange parameter is accepted and processed
    # Without creating data, this verifies the endpoint accepts the parameter
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=BTC&ledger=exchange&start_date=2026-02-01T00:00:00Z&end_date=2026-03-02T23:59:59Z"
    )

    assert response.status_code == 200
    data = response.json()
    # Should return valid response even with no data
    assert "data" in data
    assert "total_points" in data
    assert isinstance(data["data"], list)
    assert isinstance(data["total_points"], int)


def test_price_data_ledger_filter_human(client: TestClient) -> None:
    """Test price-data with ledger=human returns empty data (no price data from human ledger)."""
    # Test the ledger filter logic - should return empty for non-exchange ledgers
    response = client.get(
        "/api/v1/utils/price-data/?coin_type=BTC&ledger=human&start_date=2026-02-01T00:00:00Z&end_date=2026-03-02T23:59:59Z"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total_points"] == 0
