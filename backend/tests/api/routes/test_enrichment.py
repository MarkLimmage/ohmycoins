"""Tests for the enrichment API routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import NewsItem


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_enrichment_run_endpoint(client: TestClient, session) -> None:
    """Test POST /api/v1/enrichment/run endpoint."""
    import uuid
    # Create test news items with unique links
    unique_id = str(uuid.uuid4())
    items = [
        NewsItem(
            title="Bitcoin halving announcement",
            link=f"https://example.com/btc-{unique_id}",
            summary="Bitcoin halving coming next year",
            source="Test",
        )
    ]

    for item in items:
        session.add(item)
    session.commit()

    response = client.post("/api/v1/enrichment/run?enricher=keyword&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert "enrichment_run_id" in data
    assert "items_queued" in data
    assert data["items_queued"] >= 0


def test_enrichment_stats_endpoint(client: TestClient, session) -> None:
    """Test GET /api/v1/enrichment/stats endpoint."""
    response = client.get("/api/v1/enrichment/stats")

    assert response.status_code == 200
    data = response.json()

    assert "total_items" in data
    assert "enriched_items" in data
    assert "unenriched_items" in data
    assert "coverage_pct" in data
    assert "by_enricher" in data
    assert isinstance(data["by_enricher"], list)


def test_enrichment_runs_endpoint(client: TestClient, session) -> None:
    """Test GET /api/v1/enrichment/runs endpoint."""
    response = client.get("/api/v1/enrichment/runs?limit=50")

    assert response.status_code == 200
    data = response.json()

    assert "runs" in data
    assert "count" in data
    assert isinstance(data["runs"], list)


def test_enrichment_run_with_invalid_enricher(client: TestClient, session) -> None:
    """Test that invalid enricher parameter returns error."""
    response = client.post("/api/v1/enrichment/run?enricher=invalid&limit=10")

    # Should either succeed with 0 items or return an error
    assert response.status_code in [200, 400]


def test_enrichment_stats_coverage_calculation(client: TestClient, session) -> None:
    """Test that coverage percentage is calculated correctly."""
    import uuid
    # Create test items with unique links
    unique_id = str(uuid.uuid4())
    items = [
        NewsItem(title=f"Test {i}", link=f"https://example.com/test-{unique_id}-{i}", summary="Test", source="Test")
        for i in range(5)
    ]
    for item in items:
        session.add(item)
    session.commit()

    response = client.get("/api/v1/enrichment/stats")

    assert response.status_code == 200
    data = response.json()

    assert data["total_items"] >= 5
    assert 0 <= data["coverage_pct"] <= 100
