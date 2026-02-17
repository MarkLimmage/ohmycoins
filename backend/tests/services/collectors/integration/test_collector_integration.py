"""
Integration tests for Phase 2.5 collectors.

These tests validate end-to-end collector functionality with a real database.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlmodel import func, select

from app.models import (
    CatalystEvents,
    NewsSentiment,
    PriceData5Min,
)
from app.services.collectors.config import setup_collectors
from app.services.collectors.metrics import get_metrics_tracker
from app.services.collectors.orchestrator import get_orchestrator
from app.services.collectors.quality_monitor import get_quality_monitor


@pytest.mark.integration
class TestCollectorIntegration:
    """Integration tests for collectors."""

    @pytest.mark.asyncio
    async def test_orchestrator_registration(self):
        """Test that all collectors are properly registered."""
        orchestrator = get_orchestrator()

        # Setup collectors
        setup_collectors()

        # Check collectors are registered (at least 4 without API keys)
        assert len(orchestrator.collectors) >= 4

        # Check specific collectors that don't require API keys
        expected_collectors = [
            "defillama_api",
            "reddit_api",
            "sec_edgar_api",
            "coinspot_announcements",
        ]

        for collector_name in expected_collectors:
            assert collector_name in orchestrator.collectors

    @pytest.mark.asyncio
    async def test_quality_monitor_with_empty_database(self, db):
        """Test quality monitor with empty database."""
        monitor = get_quality_monitor()

        # Check with empty database
        metrics = await monitor.check_all(db)

        # Should have low completeness score
        assert metrics.completeness_score < 1.0

        # Should have issues or warnings
        assert len(metrics.issues) > 0 or len(metrics.warnings) > 0

    @pytest.mark.asyncio
    async def test_quality_monitor_with_data(self, db):
        """Test quality monitor with sample data."""
        # Insert sample data
        now = datetime.now(timezone.utc)

        # Add price data
        price = PriceData5Min(
            coin_type="BTC",
            timestamp=now,
            bid=Decimal("50000"),
            ask=Decimal("51000"),
            last=Decimal("50500"),
        )
        db.add(price)

        # Add sentiment data
        sentiment = NewsSentiment(
            title="Bitcoin surges",
            source="Test",
            url="https://example.com",
            published_at=now,
            sentiment="bullish",
            sentiment_score=Decimal("0.8"),
            currencies=["BTC"],
            collected_at=now,
        )
        db.add(sentiment)

        # Add catalyst event
        catalyst = CatalystEvents(
            event_type="listing",
            title="Test Bitcoin Listing",
            description="Test event",
            source="Test",
            impact_score=7,
            currencies=["BTC"],
            detected_at=now,
            url="https://example.com",
            collected_at=now,
        )
        db.add(catalyst)

        db.commit()

        # Check quality
        monitor = get_quality_monitor()
        metrics = await monitor.check_all(db)

        # Should have better scores with data
        assert metrics.completeness_score > 0.5
        assert metrics.timeliness_score > 0.5
        assert metrics.accuracy_score > 0.5
        assert metrics.overall_score > 0.5

    def test_metrics_tracker_records_success(self):
        """Test metrics tracker records successful runs."""
        tracker = get_metrics_tracker()
        tracker.reset_metrics()  # Clean slate

        # Record success
        tracker.record_success("test_collector", 100, 2.5)

        # Check metrics
        metrics = tracker.get_collector_metrics("test_collector")
        assert metrics.total_runs == 1
        assert metrics.successful_runs == 1
        assert metrics.failed_runs == 0
        assert metrics.total_records_collected == 100
        assert metrics.success_rate == 100.0


@pytest.mark.integration
class TestDataIntegrity:
    """Test data integrity and relationships."""

    @pytest.mark.asyncio
    async def test_price_data_integrity(self, db):
        """Test price data maintains integrity."""
        now = datetime.now(timezone.utc)

        # Insert multiple price records
        for i in range(3):
            price = PriceData5Min(
                coin_type="BTC",
                timestamp=now + timedelta(minutes=i*5),
                bid=Decimal(f"{50000 + i*100}"),
                ask=Decimal(f"{51000 + i*100}"),
                last=Decimal(f"{50500 + i*100}"),
            )
            db.add(price)

        db.commit()

        # Query and verify - count only records we just inserted
        count = db.exec(
            select(func.count(PriceData5Min.id))
            .where(PriceData5Min.timestamp >= now)
        ).one()

        assert count == 3
