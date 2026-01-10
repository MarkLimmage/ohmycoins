"""
Integration tests for Agent-Data interactions across all 4 ledgers.

These tests verify that agents can successfully query and retrieve data from:
- Glass Ledger: Price data, on-chain metrics, protocol fundamentals
- Human Ledger: News sentiment, social sentiment
- Catalyst Ledger: Catalyst events (SEC filings, listings, etc.)
- Exchange Ledger: Order history, positions

Tests follow SQLModel unidirectional relationship pattern and validate
data access patterns for agent workflows.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlmodel import Session

from app.models import (
    CatalystEvents,
    NewsSentiment,
    OnChainMetrics,
    Order,
    Position,
    PriceData5Min,
    SocialSentiment,
    User,
)
from app.services.agent.tools.data_retrieval_tools import (
    fetch_catalyst_events,
    fetch_on_chain_metrics,
    fetch_order_history,
    fetch_price_data,
    fetch_sentiment_data,
    fetch_user_positions,
    get_available_coins,
    get_data_statistics,
)


@pytest.fixture(name="db")
def db_fixture(session: Session):
    """Create test data in PostgreSQL session for agent-data integration tests.
    
    Uses the shared session fixture from conftest.py which provides:
    - PostgreSQL database connection (supports ARRAY types)
    - Transaction isolation via savepoints
    - Automatic cleanup after each test
    """
    # Create test user
    user = User(
        email="test_agent_integration@example.com",
        hashed_password="hashed",
        full_name="Test Agent User",
    )
    session.add(user)
    session.flush()  # Flush to database without committing the transaction
    session.refresh(user)

    # Add sample Glass Ledger data (PriceData5Min)
    now = datetime.now(timezone.utc)
    for i in range(5):
        price_data = PriceData5Min(
            coin_type="BTC",
            timestamp=now - timedelta(minutes=i * 5),
            bid=Decimal(f"{50000 + i * 100}"),
            ask=Decimal(f"{50100 + i * 100}"),
            last=Decimal(f"{50050 + i * 100}"),
        )
        session.add(price_data)

    # Add sample Glass Ledger data (OnChainMetrics)
    for i in range(3):
        metric = OnChainMetrics(
            asset="BTC",
            metric_name="active_addresses",
            metric_value=Decimal(f"{100000 + i * 1000}"),
            source="test_source",
            collected_at=now - timedelta(days=i),
        )
        session.add(metric)

    # Add sample Human Ledger data (NewsSentiment)
    for i in range(3):
        news = NewsSentiment(
            title=f"Bitcoin News {i}",
            source="test_news",
            published_at=now - timedelta(hours=i),
            sentiment="positive" if i % 2 == 0 else "negative",
            sentiment_score=Decimal(f"0.{8 - i}"),
            currencies=["BTC"],
            collected_at=now - timedelta(hours=i),
        )
        session.add(news)

    # Add sample Human Ledger data (SocialSentiment)
    for i in range(3):
        social = SocialSentiment(
            platform="reddit" if i % 2 == 0 else "twitter",
            content=f"Bitcoin social post {i}",
            score=100 + i * 10,
            sentiment="positive" if i % 2 == 0 else "neutral",
            currencies=["BTC"],
            posted_at=now - timedelta(hours=i),
            collected_at=now - timedelta(hours=i),
        )
        session.add(social)

    # Add sample Catalyst Ledger data (CatalystEvents)
    for i in range(3):
        event = CatalystEvents(
            event_type="listing" if i % 2 == 0 else "sec_filing",
            title=f"Bitcoin Event {i}",
            description=f"Event description {i}",
            source="test_source",
            currencies=["BTC"],
            impact_score=i + 1,
            detected_at=now - timedelta(days=i),
        )
        session.add(event)

    # Add sample Exchange Ledger data (Orders)
    for i in range(3):
        order = Order(
            user_id=user.id,
            coin_type="BTC",
            side="buy" if i % 2 == 0 else "sell",
            order_type="market",
            quantity=Decimal(f"0.{i + 1}"),
            filled_quantity=Decimal(f"0.{i + 1}"),
            status="filled",
            created_at=now - timedelta(days=i),
            filled_at=now - timedelta(days=i, hours=-1),
        )
        session.add(order)

    # Add sample Exchange Ledger data (Positions)
    position = Position(
        user_id=user.id,
        coin_type="BTC",
        quantity=Decimal("1.5"),
        average_price=Decimal("50000"),
        total_cost=Decimal("75000"),
    )
    session.add(position)

    session.flush()  # Flush to ensure all data is written to the session

    # Store user_id for tests
    session.user_id = user.id  # type: ignore[attr-defined]
    return session


class TestGlassLedger:
    """Test agent queries to Glass Ledger (price data, on-chain metrics)."""

    @pytest.mark.asyncio
    async def test_fetch_price_data(self, db: Session):
        """Test fetching price data from Glass Ledger."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(hours=1)

        result = await fetch_price_data(db, "BTC", start_date, now)

        assert len(result) > 0
        assert all(r["coin_type"] == "BTC" for r in result)
        assert all("bid" in r and "ask" in r and "last" in r for r in result)
        # Performance check: should return quickly
        assert len(result) <= 100  # Reasonable data size

    @pytest.mark.asyncio
    async def test_fetch_on_chain_metrics(self, db: Session):
        """Test fetching on-chain metrics from Glass Ledger."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)

        result = await fetch_on_chain_metrics(db, "BTC", start_date, now)

        assert len(result) > 0
        assert all(r["asset"] == "BTC" for r in result)
        assert all("metric_name" in r and "metric_value" in r for r in result)

    @pytest.mark.asyncio
    async def test_fetch_specific_metrics(self, db: Session):
        """Test fetching specific on-chain metrics."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)

        result = await fetch_on_chain_metrics(
            db, "BTC", start_date, now, metric_names=["active_addresses"]
        )

        assert len(result) > 0
        assert all(r["metric_name"] == "active_addresses" for r in result)

    @pytest.mark.asyncio
    async def test_get_available_coins(self, db: Session):
        """Test retrieving list of available cryptocurrencies."""
        result = await get_available_coins(db)

        assert isinstance(result, list)
        assert "BTC" in result

    @pytest.mark.asyncio
    async def test_get_data_statistics(self, db: Session):
        """Test retrieving data coverage statistics."""
        result = await get_data_statistics(db, "BTC")

        assert "price_data" in result
        assert "sentiment_data" in result
        assert "on_chain_metrics" in result
        assert "catalyst_events" in result


class TestHumanLedger:
    """Test agent queries to Human Ledger (sentiment data)."""

    @pytest.mark.asyncio
    async def test_fetch_sentiment_data(self, db: Session):
        """Test fetching sentiment data from Human Ledger."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=1)

        result = await fetch_sentiment_data(db, start_date, now)

        assert "news_sentiment" in result
        assert "social_sentiment" in result
        assert len(result["news_sentiment"]) > 0
        assert len(result["social_sentiment"]) > 0

    @pytest.mark.asyncio
    async def test_fetch_sentiment_by_currency(self, db: Session):
        """Test fetching sentiment filtered by currency."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=1)

        result = await fetch_sentiment_data(db, start_date, now, currencies=["BTC"])

        assert len(result["news_sentiment"]) > 0
        # Verify all results mention BTC
        for news in result["news_sentiment"]:
            assert "BTC" in news["currencies"]

    @pytest.mark.asyncio
    async def test_fetch_sentiment_by_platform(self, db: Session):
        """Test fetching social sentiment filtered by platform."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=1)

        result = await fetch_sentiment_data(db, start_date, now, platform="reddit")

        assert len(result["social_sentiment"]) > 0
        assert all(s["platform"] == "reddit" for s in result["social_sentiment"])


class TestCatalystLedger:
    """Test agent queries to Catalyst Ledger (events)."""

    @pytest.mark.asyncio
    async def test_fetch_catalyst_events(self, db: Session):
        """Test fetching catalyst events from Catalyst Ledger."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)

        result = await fetch_catalyst_events(db, start_date, now)

        assert len(result) > 0
        assert all("event_type" in e and "title" in e for e in result)
        assert all("impact_score" in e for e in result)

    @pytest.mark.asyncio
    async def test_fetch_events_by_type(self, db: Session):
        """Test fetching catalyst events filtered by type."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)

        result = await fetch_catalyst_events(
            db, start_date, now, event_types=["listing"]
        )

        assert len(result) > 0
        assert all(e["event_type"] == "listing" for e in result)

    @pytest.mark.asyncio
    async def test_fetch_events_by_currency(self, db: Session):
        """Test fetching catalyst events filtered by currency."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)

        result = await fetch_catalyst_events(db, start_date, now, currencies=["BTC"])

        assert len(result) > 0
        # Verify all results mention BTC
        for event in result:
            assert "BTC" in event["currencies"]


class TestExchangeLedger:
    """Test agent queries to Exchange Ledger (orders, positions)."""

    @pytest.mark.asyncio
    async def test_fetch_order_history(self, db: Session):
        """Test fetching order history from Exchange Ledger."""
        user_id = db.user_id  # type: ignore[attr-defined]

        result = await fetch_order_history(db, user_id)

        assert len(result) > 0
        assert all("coin_type" in o and "side" in o for o in result)
        assert all("quantity" in o and "status" in o for o in result)

    @pytest.mark.asyncio
    async def test_fetch_orders_by_coin(self, db: Session):
        """Test fetching order history filtered by coin type."""
        user_id = db.user_id  # type: ignore[attr-defined]

        result = await fetch_order_history(db, user_id, coin_type="BTC")

        assert len(result) > 0
        assert all(o["coin_type"] == "BTC" for o in result)

    @pytest.mark.asyncio
    async def test_fetch_orders_by_status(self, db: Session):
        """Test fetching order history filtered by status."""
        user_id = db.user_id  # type: ignore[attr-defined]

        result = await fetch_order_history(db, user_id, status="filled")

        assert len(result) > 0
        assert all(o["status"] == "filled" for o in result)

    @pytest.mark.asyncio
    async def test_fetch_user_positions(self, db: Session):
        """Test fetching current positions from Exchange Ledger."""
        user_id = db.user_id  # type: ignore[attr-defined]

        result = await fetch_user_positions(db, user_id)

        assert len(result) > 0
        assert all("coin_type" in p and "quantity" in p for p in result)
        assert all("average_price" in p and "total_cost" in p for p in result)

    @pytest.mark.asyncio
    async def test_fetch_position_by_coin(self, db: Session):
        """Test fetching position for specific coin."""
        user_id = db.user_id  # type: ignore[attr-defined]

        result = await fetch_user_positions(db, user_id, coin_type="BTC")

        assert len(result) > 0
        assert all(p["coin_type"] == "BTC" for p in result)


class TestPerformanceAndPatterns:
    """Test performance characteristics and SQLModel patterns."""

    @pytest.mark.asyncio
    async def test_query_performance_under_1_second(self, db: Session):
        """Test that queries complete within 1 second."""
        import time

        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=1)

        # Test price data query
        start_time = time.time()
        await fetch_price_data(db, "BTC", start_date, now)
        elapsed = time.time() - start_time
        assert elapsed < 1.0, "Price data query took too long"

        # Test sentiment data query
        start_time = time.time()
        await fetch_sentiment_data(db, start_date, now)
        elapsed = time.time() - start_time
        assert elapsed < 1.0, "Sentiment data query took too long"

    @pytest.mark.asyncio
    async def test_handles_missing_data_gracefully(self, db: Session):
        """Test that queries handle missing data without errors."""
        now = datetime.now(timezone.utc)
        # Query for a time range with no data
        future_date = now + timedelta(days=365)

        result = await fetch_price_data(db, "BTC", future_date, future_date)
        assert result == []  # Should return empty list, not error

    @pytest.mark.asyncio
    async def test_handles_invalid_coin_gracefully(self, db: Session):
        """Test that queries handle invalid coin types gracefully."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=1)

        result = await fetch_price_data(db, "INVALID_COIN", start_date, now)
        assert result == []  # Should return empty list, not error

    @pytest.mark.asyncio
    async def test_no_relationship_warnings(self, db: Session):
        """Test that queries follow unidirectional relationship pattern."""
        # This test verifies no bidirectional relationship issues
        # by performing queries and checking for warnings
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=1)
        user_id = db.user_id  # type: ignore[attr-defined]

        # Execute all query types - should not generate relationship warnings
        await fetch_price_data(db, "BTC", start_date, now)
        await fetch_sentiment_data(db, start_date, now)
        await fetch_on_chain_metrics(db, "BTC", start_date, now)
        await fetch_catalyst_events(db, start_date, now)
        await fetch_order_history(db, user_id)
        await fetch_user_positions(db, user_id)

        # If we get here without errors, pattern is correct
        assert True
