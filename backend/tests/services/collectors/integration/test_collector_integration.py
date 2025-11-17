"""
Integration tests for Phase 2.5 collectors.

These tests validate end-to-end collector functionality with a real database.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlmodel import Session, select, func

from app.models import (
    PriceData5Min,
    NewsSentiment,
    CatalystEvents,
    ProtocolFundamentals,
)
from app.services.collectors.orchestrator import get_orchestrator
from app.services.collectors.quality_monitor import get_quality_monitor
from app.services.collectors.metrics import get_metrics_tracker
from app.services.collectors.config import setup_collectors


@pytest.fixture
def db_session(engine):
    """Create a database session for testing."""
    with Session(engine) as session:
        yield session


@pytest.mark.integration
class TestCollectorIntegration:
    """Integration tests for collectors."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_registration(self):
        """Test that all collectors are properly registered."""
        orchestrator = get_orchestrator()
        
        # Setup collectors
        setup_collectors()
        
        # Check collectors are registered
        assert len(orchestrator._collectors) >= 5
        
        # Check specific collectors
        expected_collectors = [
            "defillama_api",
            "cryptopanic",
            "reddit_api",
            "sec_edgar_api",
            "coinspot_announcements",
        ]
        
        for collector_name in expected_collectors:
            assert collector_name in orchestrator._collectors
    
    @pytest.mark.asyncio
    async def test_quality_monitor_with_empty_database(self, db_session):
        """Test quality monitor with empty database."""
        monitor = get_quality_monitor()
        
        # Check with empty database
        metrics = await monitor.check_all(db_session)
        
        # Should have low completeness score
        assert metrics.completeness_score < 1.0
        
        # Should have issues or warnings
        assert len(metrics.issues) > 0 or len(metrics.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_quality_monitor_with_data(self, db_session):
        """Test quality monitor with sample data."""
        # Insert sample data
        now = datetime.now(timezone.utc)
        
        # Add price data
        price = PriceData5Min(
            coin_type="BTC",
            timestamp=now,
            open_price=Decimal("50000"),
            high_price=Decimal("51000"),
            low_price=Decimal("49000"),
            close_price=Decimal("50500"),
            volume=Decimal("1000"),
        )
        db_session.add(price)
        
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
        db_session.add(sentiment)
        
        # Add catalyst event
        catalyst = CatalystEvents(
            event_type="listing",
            event_date=now.date(),
            source="Test",
            description="Test event",
            impact_score=Decimal("0.7"),
            currencies=["BTC"],
            url="https://example.com",
            collected_at=now,
        )
        db_session.add(catalyst)
        
        db_session.commit()
        
        # Check quality
        monitor = get_quality_monitor()
        metrics = await monitor.check_all(db_session)
        
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
    async def test_price_data_integrity(self, db_session):
        """Test price data maintains integrity."""
        now = datetime.now(timezone.utc)
        
        # Insert multiple price records
        for i in range(3):
            price = PriceData5Min(
                coin_type="BTC",
                timestamp=now + timedelta(minutes=i*5),
                open_price=Decimal(f"{50000 + i*100}"),
                high_price=Decimal(f"{51000 + i*100}"),
                low_price=Decimal(f"{49000 + i*100}"),
                close_price=Decimal(f"{50500 + i*100}"),
                volume=Decimal("1000"),
            )
            db_session.add(price)
        
        db_session.commit()
        
        # Query and verify
        count = db_session.exec(
            select(func.count(PriceData5Min.id))
        ).one()
        
        assert count == 3
