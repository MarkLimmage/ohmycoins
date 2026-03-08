"""Tests for the signals API routes."""

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.models import NewsEnrichment, NewsItem


def test_get_coin_signals(client: TestClient, session) -> None:
    """Test GET /api/v1/signals/coin/{symbol} endpoint."""
    unique_id = str(uuid.uuid4())
    link = f"https://example.com/btc-{unique_id}"

    news_item = NewsItem(
        title="Bitcoin price surge",
        link=link,
        summary="Bitcoin is rising",
        source="TestSource",
    )
    session.add(news_item)
    session.commit()

    enrichment = NewsEnrichment(
        news_item_link=link,
        enricher_name=f"test_enricher_{unique_id}",
        enrichment_type="sentiment",
        data={"direction": "bullish"},
        currencies=["BTC"],
        confidence=0.85,
        enriched_at=datetime.now(timezone.utc),
    )
    session.add(enrichment)
    session.commit()

    response = client.get("/api/v1/signals/coin/BTC?hours=24")

    assert response.status_code == 200
    data = response.json()
    assert data["coin"] == "BTC"
    assert data["period_hours"] == 24
    assert "signals" in data
    assert "summary" in data
    assert data["summary"]["total_signals"] >= 1


def test_get_coin_signals_empty(client: TestClient) -> None:
    """Test that empty signals return valid response."""
    unique_id = str(uuid.uuid4())[:8]
    response = client.get(f"/api/v1/signals/coin/NOEXIST{unique_id}?hours=24")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_signals"] == 0


def test_get_signal_summary(client: TestClient) -> None:
    """Test GET /api/v1/signals/summary endpoint."""
    response = client.get("/api/v1/signals/summary")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_signal_trends(client: TestClient) -> None:
    """Test GET /api/v1/signals/trends endpoint."""
    response = client.get("/api/v1/signals/trends?hours=168")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_signal_entities(client: TestClient, session) -> None:
    """Test GET /api/v1/signals/entities endpoint."""
    unique_id = str(uuid.uuid4())
    link = f"https://example.com/entity-{unique_id}"

    news_item = NewsItem(
        title="Company announcement",
        link=link,
        summary="Entity test",
        source="TestSource",
    )
    session.add(news_item)
    session.commit()

    enrichment = NewsEnrichment(
        news_item_link=link,
        enricher_name=f"entity_enricher_{unique_id}",
        enrichment_type="entity",
        data={"entities": [{"name": "Vitalik", "type": "person"}]},
        currencies=["ETH"],
        confidence=0.9,
        enriched_at=datetime.now(timezone.utc),
    )
    session.add(enrichment)
    session.commit()

    response = client.get("/api/v1/signals/entities?hours=72")

    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert "relationships" in data


def test_refresh_views(client: TestClient) -> None:
    """Test POST /api/v1/signals/refresh-views endpoint."""
    response = client.post("/api/v1/signals/refresh-views")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
