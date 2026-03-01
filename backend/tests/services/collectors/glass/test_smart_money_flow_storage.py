"""
Integration tests for SmartMoneyFlow model and storage.

Tests validate SmartMoneyFlow model CRUD operations, database constraints,
data validation, and Nansen collector integration with storage.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, select

from app.models import SmartMoneyFlow
from app.collectors.strategies.glass_nansen import GlassNansen


class TestSmartMoneyFlowModel:
    """Test suite for SmartMoneyFlow database model."""

    def test_create_smart_money_flow(self, session: Session):
        """Test creating a SmartMoneyFlow record."""
        flow = SmartMoneyFlow(
            token="ETH",
            net_flow_usd=Decimal("1500000.50"),
            buying_wallet_count=10,
            selling_wallet_count=3,
            buying_wallets=[
                "0x1234567890abcdef1234567890abcdef12345678",
                "0xabcdef1234567890abcdef1234567890abcdef12",
            ],
            selling_wallets=["0xfedcba0987654321fedcba0987654321fedcba09"],
            collected_at=datetime.now(timezone.utc),
        )

        session.add(flow)
        session.commit()
        session.refresh(flow)

        assert flow.id is not None
        assert flow.token == "ETH"
        assert flow.net_flow_usd == Decimal("1500000.50")
        assert flow.buying_wallet_count == 10
        assert flow.selling_wallet_count == 3
        assert len(flow.buying_wallets) == 2
        assert len(flow.selling_wallets) == 1

    def test_create_smart_money_flow_minimal(self, session: Session):
        """Test creating SmartMoneyFlow with minimal required fields."""
        flow = SmartMoneyFlow(
            token="BTC",
            net_flow_usd=Decimal("-500000.00"),
            buying_wallet_count=0,
            selling_wallet_count=5,
        )

        session.add(flow)
        session.commit()
        session.refresh(flow)

        assert flow.id is not None
        assert flow.token == "BTC"
        assert flow.net_flow_usd == Decimal("-500000.00")
        assert flow.buying_wallets is None
        assert flow.selling_wallets is None

    def test_query_smart_money_flow_by_token(self, session: Session):
        """Test querying SmartMoneyFlow records by token."""
        # Create multiple records
        flows = [
            SmartMoneyFlow(
                token="ETH",
                net_flow_usd=Decimal("1000000.00"),
                buying_wallet_count=10,
                selling_wallet_count=2,
                collected_at=datetime.now(timezone.utc),
            ),
            SmartMoneyFlow(
                token="ETH",
                net_flow_usd=Decimal("2000000.00"),
                buying_wallet_count=15,
                selling_wallet_count=3,
                collected_at=datetime.now(timezone.utc),
            ),
            SmartMoneyFlow(
                token="BTC",
                net_flow_usd=Decimal("500000.00"),
                buying_wallet_count=5,
                selling_wallet_count=1,
                collected_at=datetime.now(timezone.utc),
            ),
        ]

        for flow in flows:
            session.add(flow)
        session.commit()

        # Query ETH flows
        eth_flows = session.exec(
            select(SmartMoneyFlow).where(SmartMoneyFlow.token == "ETH")
        ).all()

        assert len(eth_flows) == 2
        assert all(flow.token == "ETH" for flow in eth_flows)

    def test_query_smart_money_flow_by_date(self, session: Session):
        """Test querying SmartMoneyFlow records by collection date."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        # Create records with different timestamps
        flows = [
            SmartMoneyFlow(
                token="ETH",
                net_flow_usd=Decimal("1000000.00"),
                buying_wallet_count=10,
                selling_wallet_count=2,
                collected_at=yesterday,
            ),
            SmartMoneyFlow(
                token="ETH",
                net_flow_usd=Decimal("2000000.00"),
                buying_wallet_count=15,
                selling_wallet_count=3,
                collected_at=now,
            ),
        ]

        for flow in flows:
            session.add(flow)
        session.commit()

        # Query recent flows (last hour)
        recent_cutoff = now - timedelta(hours=1)
        recent_flows = session.exec(
            select(SmartMoneyFlow).where(SmartMoneyFlow.collected_at > recent_cutoff)
        ).all()

        assert len(recent_flows) == 1
        assert recent_flows[0].net_flow_usd == Decimal("2000000.00")

    def test_update_smart_money_flow(self, session: Session):
        """Test updating a SmartMoneyFlow record."""
        flow = SmartMoneyFlow(
            token="ETH",
            net_flow_usd=Decimal("1000000.00"),
            buying_wallet_count=10,
            selling_wallet_count=2,
        )

        session.add(flow)
        session.commit()
        session.refresh(flow)

        # Update the flow
        flow.net_flow_usd = Decimal("1500000.00")
        flow.buying_wallet_count = 12
        session.add(flow)
        session.commit()
        session.refresh(flow)

        assert flow.net_flow_usd == Decimal("1500000.00")
        assert flow.buying_wallet_count == 12

    def test_delete_smart_money_flow(self, session: Session):
        """Test deleting a SmartMoneyFlow record."""
        flow = SmartMoneyFlow(
            token="ETH",
            net_flow_usd=Decimal("1000000.00"),
            buying_wallet_count=10,
            selling_wallet_count=2,
        )

        session.add(flow)
        session.commit()
        flow_id = flow.id

        # Delete the flow
        session.delete(flow)
        session.commit()

        # Verify deletion
        deleted_flow = session.get(SmartMoneyFlow, flow_id)
        assert deleted_flow is None

    def test_smart_money_flow_negative_net_flow(self, session: Session):
        """Test SmartMoneyFlow with negative net flow (net selling)."""
        flow = SmartMoneyFlow(
            token="USDT",
            net_flow_usd=Decimal("-2500000.00"),
            buying_wallet_count=2,
            selling_wallet_count=15,
            collected_at=datetime.now(timezone.utc),
        )

        session.add(flow)
        session.commit()
        session.refresh(flow)

        assert flow.net_flow_usd == Decimal("-2500000.00")
        assert flow.selling_wallet_count > flow.buying_wallet_count

    def test_smart_money_flow_large_wallet_list(self, session: Session):
        """Test SmartMoneyFlow with large wallet lists."""
        # Create 20 wallet addresses
        buying_wallets = [f"0x{i:040x}" for i in range(20)]
        selling_wallets = [f"0x{i+100:040x}" for i in range(15)]

        flow = SmartMoneyFlow(
            token="SOL",
            net_flow_usd=Decimal("750000.00"),
            buying_wallet_count=20,
            selling_wallet_count=15,
            buying_wallets=buying_wallets,
            selling_wallets=selling_wallets,
            collected_at=datetime.now(timezone.utc),
        )

        session.add(flow)
        session.commit()
        session.refresh(flow)

        assert len(flow.buying_wallets) == 20
        assert len(flow.selling_wallets) == 15
        assert flow.buying_wallet_count == 20
        assert flow.selling_wallet_count == 15


class TestNansenCollectorStorage:
    """Test suite for Nansen collector integration with SmartMoneyFlow storage."""

    def test_collector_exists(self) -> None:
        """Test that GlassNansen collector exists and is instantiable."""
        collector = GlassNansen()
        assert collector.name == "glass_nansen"

    @pytest.mark.asyncio
    async def test_query_performance(self, session: Session):
        """Test query performance with indexed fields."""
        import time

        # Create 100 records
        for i in range(100):
            flow = SmartMoneyFlow(
                token=f"TOKEN{i % 10}",  # 10 different tokens
                net_flow_usd=Decimal(str(i * 1000)),
                buying_wallet_count=i % 20,
                selling_wallet_count=i % 15,
                collected_at=datetime.now(timezone.utc),
            )
            session.add(flow)
        session.commit()

        # Query by indexed field (token)
        start_time = time.time()
        flows = session.exec(
            select(SmartMoneyFlow).where(SmartMoneyFlow.token == "TOKEN5")
        ).all()
        query_time = time.time() - start_time

        assert len(flows) == 10
        # Should be fast due to index (< 100ms requirement)
        assert query_time < 0.1, f"Query took {query_time}s, expected < 0.1s"
