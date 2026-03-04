"""
Tests for collector API endpoints, including the sample-records endpoint.
"""

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.collectors.sample_records import PLUGIN_DATA_MAP
from app.models import Collector, PriceData5Min


class TestSampleRecords:
    """Tests for GET /{id}/sample-records endpoint."""

    def test_get_sample_records_success(self, client: TestClient, session: Session) -> None:
        """Test successful retrieval of sample records for CoinspotExchange plugin."""
        # Create a collector instance with unique name
        collector = Collector(
            name=f"test_coinspot_{uuid.uuid4().hex[:8]}",
            plugin_name="CoinspotExchange",
            is_enabled=True,
        )
        session.add(collector)
        session.commit()
        session.refresh(collector)

        # Create sample price data
        price = PriceData5Min(
            coin_type="BTC",
            bid=50000.0,
            ask=50100.0,
            last=50050.0,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(price)
        session.commit()

        # Fetch sample records
        response = client.get(f"/api/v1/collectors/{collector.id}/sample-records")

        assert response.status_code == 200
        data = response.json()
        assert "data_type" in data
        assert data["data_type"] == "Price Data (5min)"
        assert "columns" in data
        assert "records" in data
        assert isinstance(data["records"], list)
        assert len(data["records"]) >= 1
        assert "total_count" in data
        assert data["total_count"] >= 1  # May have pre-existing data

        # Verify record structure
        record = data["records"][0]
        assert "coin_type" in record
        assert record["coin_type"] == "BTC"
        assert "bid" in record
        assert "ask" in record
        assert "last" in record
        assert "timestamp" in record

    def test_get_sample_records_with_limit(self, client: TestClient, session: Session) -> None:
        """Test sample records with custom limit parameter."""
        # Create a collector with unique name
        collector = Collector(
            name=f"test_coinspot_limit_{uuid.uuid4().hex[:8]}",
            plugin_name="CoinspotExchange",
            is_enabled=True,
        )
        session.add(collector)
        session.commit()
        session.refresh(collector)

        # Create multiple price data records
        for i in range(15):
            price = PriceData5Min(
                coin_type="ETH",
                bid=3000.0 + i,
                ask=3100.0 + i,
                last=3050.0 + i,
                timestamp=datetime.now(timezone.utc),
            )
            session.add(price)
        session.commit()

        # Fetch with limit=5
        response = client.get(f"/api/v1/collectors/{collector.id}/sample-records?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) == 5
        assert data["total_count"] >= 15  # May have pre-existing data

    def test_get_sample_records_not_found(self, client: TestClient) -> None:
        """Test 404 when collector does not exist."""
        response = client.get("/api/v1/collectors/999999/sample-records")
        assert response.status_code == 404
        assert "Collector not found" in response.json()["detail"]

    def test_get_sample_records_unknown_plugin(self, client: TestClient, session: Session) -> None:
        """Test 400 when collector plugin is not in PLUGIN_DATA_MAP."""
        # Create collector with unmapped plugin and unique name
        collector = Collector(
            name=f"test_unknown_plugin_{uuid.uuid4().hex[:8]}",
            plugin_name="nonexistent_plugin",
            is_enabled=True,
        )
        session.add(collector)
        session.commit()
        session.refresh(collector)

        response = client.get(f"/api/v1/collectors/{collector.id}/sample-records")
        assert response.status_code == 400
        assert "No data table mapping" in response.json()["detail"]

    def test_get_sample_records_empty_table(self, client: TestClient, session: Session) -> None:
        """Test empty records response when data table has no entries."""
        # Create collector with mapped plugin but no data and unique name
        collector = Collector(
            name=f"test_empty_news_{uuid.uuid4().hex[:8]}",
            plugin_name="news_cointelegraph",
            is_enabled=True,
        )
        session.add(collector)
        session.commit()
        session.refresh(collector)

        response = client.get(f"/api/v1/collectors/{collector.id}/sample-records")
        assert response.status_code == 200
        data = response.json()
        assert data["records"] == []
        assert data["total_count"] == 0
        assert data["data_type"] == "News Items"

    def test_plugin_data_map_covers_all_plugins(self) -> None:
        """Test that PLUGIN_DATA_MAP has entries for all expected plugins."""
        expected_plugins = {
            "glass_defillama",
            "GlassChainWalker",
            "glass_nansen",
            "news_cryptopanic",
            "human_newscatcher",
            "human_reddit",
            "catalyst_sec",
            "catalyst_coinspot_announcements",
            "CoinspotExchange",
            "HumanRSSCollector",
            "news_cointelegraph",
            "news_coindesk",
            "news_beincrypto",
            "news_cryptoslate",
            "news_cryptoslate_keywords",
            "news_decrypt",
            "news_newsbtc",
        }
        assert set(PLUGIN_DATA_MAP.keys()) == expected_plugins
        # Verify each entry has required attributes
        for plugin_name, config in PLUGIN_DATA_MAP.items():
            assert config.model is not None
            assert config.order_by is not None
            assert isinstance(config.display_columns, list)
            assert len(config.display_columns) > 0
            assert config.data_type_label is not None
