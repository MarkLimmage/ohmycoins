"""
Tests for Data Retrieval Tools - Week 3-4 Implementation

Tests all data retrieval tools with mock data and database interactions.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from app.services.agent.tools.data_retrieval_tools import (
    fetch_price_data,
    fetch_sentiment_data,
    fetch_on_chain_metrics,
    fetch_catalyst_events,
    get_available_coins,
    get_data_statistics,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock()
    session.exec = Mock()
    return session


@pytest.fixture
def sample_date_range():
    """Create a sample date range for testing."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    return start_date, end_date


class TestFetchPriceData:
    """Tests for fetch_price_data function."""
    
    @pytest.mark.asyncio
    async def test_fetch_price_data_basic(self, mock_session, sample_date_range):
        """Test basic price data fetching."""
        start_date, end_date = sample_date_range
        
        # Mock price data
        mock_price = Mock()
        mock_price.timestamp = datetime.now()
        mock_price.coin_type = "BTC"
        mock_price.bid = Decimal("50000.00")
        mock_price.ask = Decimal("50100.00")
        mock_price.last = Decimal("50050.00")
        
        mock_session.exec.return_value.all.return_value = [mock_price]
        
        # Execute
        result = await fetch_price_data(mock_session, "BTC", start_date, end_date)
        
        # Verify
        assert len(result) == 1
        assert result[0]["coin_type"] == "BTC"
        assert result[0]["bid"] == 50000.00
        assert result[0]["ask"] == 50100.00
        assert result[0]["last"] == 50050.00
    
    @pytest.mark.asyncio
    async def test_fetch_price_data_empty(self, mock_session, sample_date_range):
        """Test fetching when no data is available."""
        start_date, end_date = sample_date_range
        
        mock_session.exec.return_value.all.return_value = []
        
        result = await fetch_price_data(mock_session, "BTC", start_date, end_date)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_fetch_price_data_default_end_date(self, mock_session):
        """Test fetching with default end date."""
        start_date = datetime.now() - timedelta(days=7)
        
        mock_session.exec.return_value.all.return_value = []
        
        result = await fetch_price_data(mock_session, "ETH", start_date)
        
        assert result == []
        mock_session.exec.assert_called_once()


class TestFetchSentimentData:
    """Tests for fetch_sentiment_data function."""
    
    @pytest.mark.asyncio
    async def test_fetch_sentiment_data_complete(self, mock_session, sample_date_range):
        """Test fetching sentiment data with news and social."""
        start_date, end_date = sample_date_range
        
        # Mock news sentiment
        mock_news = Mock()
        mock_news.title = "Bitcoin hits new high"
        mock_news.source = "CoinDesk"
        mock_news.published_at = datetime.now()
        mock_news.sentiment = "positive"
        mock_news.sentiment_score = Decimal("0.8")
        mock_news.currencies = ["BTC"]
        
        # Mock social sentiment
        mock_social = Mock()
        mock_social.platform = "reddit"
        mock_social.content = "Bitcoin looking bullish!"
        mock_social.score = 100
        mock_social.sentiment = "positive"
        mock_social.currencies = ["BTC"]
        mock_social.posted_at = datetime.now()
        
        # Setup mock to return different results for different calls
        mock_session.exec.return_value.all.side_effect = [[mock_news], [mock_social]]
        
        # Execute
        result = await fetch_sentiment_data(mock_session, start_date, end_date)
        
        # Verify
        assert "news_sentiment" in result
        assert "social_sentiment" in result
        assert len(result["news_sentiment"]) == 1
        assert len(result["social_sentiment"]) == 1
        assert result["news_sentiment"][0]["sentiment"] == "positive"
        assert result["social_sentiment"][0]["platform"] == "reddit"
    
    @pytest.mark.asyncio
    async def test_fetch_sentiment_data_with_platform_filter(self, mock_session, sample_date_range):
        """Test fetching sentiment data filtered by platform."""
        start_date, end_date = sample_date_range
        
        mock_session.exec.return_value.all.side_effect = [[], []]
        
        result = await fetch_sentiment_data(
            mock_session, start_date, end_date, platform="reddit"
        )
        
        assert result["news_sentiment"] == []
        assert result["social_sentiment"] == []


class TestFetchOnChainMetrics:
    """Tests for fetch_on_chain_metrics function."""
    
    @pytest.mark.asyncio
    async def test_fetch_on_chain_metrics_basic(self, mock_session, sample_date_range):
        """Test basic on-chain metrics fetching."""
        start_date, end_date = sample_date_range
        
        # Mock metric
        mock_metric = Mock()
        mock_metric.asset = "BTC"
        mock_metric.metric_name = "active_addresses"
        mock_metric.metric_value = Decimal("1000000")
        mock_metric.source = "glassnode"
        mock_metric.collected_at = datetime.now()
        
        mock_session.exec.return_value.order_by.return_value.all.return_value = [mock_metric]
        
        # Execute
        result = await fetch_on_chain_metrics(mock_session, "BTC", start_date, end_date)
        
        # Verify
        assert len(result) == 1
        assert result[0]["asset"] == "BTC"
        assert result[0]["metric_name"] == "active_addresses"
        assert result[0]["metric_value"] == 1000000.0
    
    @pytest.mark.asyncio
    async def test_fetch_on_chain_metrics_with_filter(self, mock_session, sample_date_range):
        """Test fetching specific metrics."""
        start_date, end_date = sample_date_range
        
        mock_session.exec.return_value.order_by.return_value.all.return_value = []
        
        result = await fetch_on_chain_metrics(
            mock_session, "ETH", start_date, end_date,
            metric_names=["active_addresses", "transaction_volume"]
        )
        
        assert result == []


class TestFetchCatalystEvents:
    """Tests for fetch_catalyst_events function."""
    
    @pytest.mark.asyncio
    async def test_fetch_catalyst_events_basic(self, mock_session, sample_date_range):
        """Test basic catalyst event fetching."""
        start_date, end_date = sample_date_range
        
        # Mock event
        mock_event = Mock()
        mock_event.event_type = "sec_filing"
        mock_event.title = "Coinbase files 10-K"
        mock_event.description = "Annual report filed"
        mock_event.source = "SEC"
        mock_event.currencies = ["BTC", "ETH"]
        mock_event.impact_score = 7
        mock_event.detected_at = datetime.now()
        
        mock_session.exec.return_value.order_by.return_value.all.return_value = [mock_event]
        
        # Execute
        result = await fetch_catalyst_events(mock_session, start_date, end_date)
        
        # Verify
        assert len(result) == 1
        assert result[0]["event_type"] == "sec_filing"
        assert result[0]["impact_score"] == 7
        assert "BTC" in result[0]["currencies"]
    
    @pytest.mark.asyncio
    async def test_fetch_catalyst_events_with_filters(self, mock_session, sample_date_range):
        """Test fetching with event type and currency filters."""
        start_date, end_date = sample_date_range
        
        mock_session.exec.return_value.order_by.return_value.all.return_value = []
        
        result = await fetch_catalyst_events(
            mock_session, start_date, end_date,
            event_types=["listing", "sec_filing"],
            currencies=["BTC"]
        )
        
        assert result == []


class TestGetAvailableCoins:
    """Tests for get_available_coins function."""
    
    @pytest.mark.asyncio
    async def test_get_available_coins(self, mock_session):
        """Test getting list of available coins."""
        mock_session.exec.return_value.all.return_value = ["BTC", "ETH", "ADA", "SOL"]
        
        result = await get_available_coins(mock_session)
        
        assert len(result) == 4
        assert "BTC" in result
        assert "ETH" in result
        # Should be sorted
        assert result == ["ADA", "BTC", "ETH", "SOL"]
    
    @pytest.mark.asyncio
    async def test_get_available_coins_empty(self, mock_session):
        """Test when no coins are available."""
        mock_session.exec.return_value.all.return_value = []
        
        result = await get_available_coins(mock_session)
        
        assert result == []


class TestGetDataStatistics:
    """Tests for get_data_statistics function."""
    
    @pytest.mark.asyncio
    async def test_get_data_statistics_general(self, mock_session):
        """Test getting general data statistics."""
        # Mock price data stats
        price_stats_mock = Mock()
        price_stats_mock.earliest = datetime.now() - timedelta(days=30)
        price_stats_mock.latest = datetime.now()
        price_stats_mock.total_records = 8640  # 30 days * 24 hours * 12 (5-min intervals)
        
        # Setup multiple exec calls for different queries
        mock_session.exec.side_effect = [
            Mock(one=Mock(return_value=price_stats_mock)),  # Price stats
            Mock(one=Mock(return_value=100)),  # News count
            Mock(one=Mock(return_value=500)),  # Social count
            Mock(one=Mock(return_value=50)),   # On-chain count
            Mock(one=Mock(return_value=10)),   # Catalyst count
        ]
        
        # Execute
        result = await get_data_statistics(mock_session)
        
        # Verify
        assert "price_data" in result
        assert "sentiment_data" in result
        assert "on_chain_metrics" in result
        assert "catalyst_events" in result
        
        assert result["price_data"]["total_records"] == 8640
        assert result["sentiment_data"]["news_articles"] == 100
        assert result["sentiment_data"]["social_posts"] == 500
        assert result["on_chain_metrics"]["total_metrics"] == 50
        assert result["catalyst_events"]["total_events"] == 10
    
    @pytest.mark.asyncio
    async def test_get_data_statistics_for_specific_coin(self, mock_session):
        """Test getting statistics for a specific coin."""
        price_stats_mock = Mock()
        price_stats_mock.earliest = datetime.now() - timedelta(days=7)
        price_stats_mock.latest = datetime.now()
        price_stats_mock.total_records = 2016  # 7 days * 24 hours * 12
        
        mock_session.exec.side_effect = [
            Mock(one=Mock(return_value=price_stats_mock)),
            Mock(one=Mock(return_value=50)),
            Mock(one=Mock(return_value=200)),
            Mock(one=Mock(return_value=20)),
            Mock(one=Mock(return_value=5)),
        ]
        
        result = await get_data_statistics(mock_session, coin_type="BTC")
        
        assert result["price_data"]["total_records"] == 2016
