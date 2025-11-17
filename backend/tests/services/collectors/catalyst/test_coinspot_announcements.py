"""
Tests for CoinSpot announcements scraper (Catalyst Ledger).
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.collectors.catalyst.coinspot_announcements import (
    CoinSpotAnnouncementsCollector
)


@pytest.fixture
def coinspot_collector():
    """Create a CoinSpot announcements collector instance for testing."""
    return CoinSpotAnnouncementsCollector()


@pytest.fixture
def sample_html_with_announcements():
    """Sample HTML with announcement structure."""
    from datetime import datetime, timezone
    # Use recent dates for testing
    now = datetime.now(timezone.utc)
    date1 = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    date2 = (now).strftime("%Y-%m-%dT%H:%M:%SZ")
    date1_display = now.strftime("%d/%m/%Y")
    date2_display = now.strftime("%d/%m/%Y")
    
    return f"""
    <html>
        <body>
            <div class="news-section">
                <article class="announcement">
                    <h2>New Listing: Polygon (MATIC) Now Available</h2>
                    <p class="content">
                        We're excited to announce that Polygon (MATIC) is now 
                        available for trading on CoinSpot.
                    </p>
                    <time datetime="{date1}">{date1_display}</time>
                    <a href="/news/polygon-listing">Read more</a>
                </article>
                <article class="announcement">
                    <h2>Scheduled Maintenance Notice</h2>
                    <p class="content">
                        CoinSpot will undergo scheduled maintenance on Sunday.
                        Trading will be temporarily unavailable.
                    </p>
                    <time datetime="{date2}">{date2_display}</time>
                </article>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_no_announcements():
    """Sample HTML without announcements."""
    return """
    <html>
        <body>
            <h1>Welcome to CoinSpot</h1>
            <p>Trade cryptocurrencies</p>
        </body>
    </html>
    """


class TestCoinSpotAnnouncementsCollector:
    """Test suite for CoinSpot announcements collector."""
    
    def test_initialization(self, coinspot_collector):
        """Test collector initialization."""
        assert coinspot_collector.name == "coinspot_announcements"
        assert coinspot_collector.ledger == "catalyst"
        assert "coinspot.com.au" in coinspot_collector.url
        assert coinspot_collector.use_playwright is False
    
    def test_event_types_configuration(self, coinspot_collector):
        """Test that event types are properly configured."""
        assert "listing" in coinspot_collector.EVENT_TYPES
        assert "maintenance" in coinspot_collector.EVENT_TYPES
        assert "trading" in coinspot_collector.EVENT_TYPES
        
        # Check impact scores are valid
        for event_type, info in coinspot_collector.EVENT_TYPES.items():
            assert 1 <= info["impact"] <= 10
            assert "keywords" in info
            assert "event_type" in info
    
    @pytest.mark.asyncio
    async def test_scrape_static_success(
        self, coinspot_collector, sample_html_with_announcements
    ):
        """Test successful scraping of announcements."""
        # Mock aiohttp response
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Create mock response
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value=sample_html_with_announcements)
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            # Create mock session
            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Configure the session class to return our mock session
            mock_session_class.return_value = mock_session
            
            data = await coinspot_collector.scrape_static()
            
            # Should find announcements
            assert len(data) >= 1
            assert all(isinstance(item, dict) for item in data)
            
            # Check for required fields
            for item in data:
                assert "event_type" in item
                assert "title" in item
                assert "source" in item
                assert item["source"] == "CoinSpot"
    
    @pytest.mark.asyncio
    async def test_scrape_static_no_announcements(
        self, coinspot_collector, sample_html_no_announcements
    ):
        """Test scraping when no announcements are found."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            # Create mock response
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value=sample_html_no_announcements)
            mock_response.raise_for_status = MagicMock()
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            
            # Create mock session
            mock_session = AsyncMock()
            mock_session.get = MagicMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # Configure the session class to return our mock session
            mock_session_class.return_value = mock_session
            
            data = await coinspot_collector.scrape_static()
            
            # Should return empty list
            assert isinstance(data, list)
    
    def test_classify_announcement_listing(self, coinspot_collector):
        """Test classification of listing announcements."""
        result = coinspot_collector._classify_announcement(
            "New Listing: Solana (SOL)",
            "Solana is now available for trading"
        )
        
        assert result["event_type"] == "exchange_listing"
        assert result["impact"] == 9  # Listings have high impact
    
    def test_classify_announcement_maintenance(self, coinspot_collector):
        """Test classification of maintenance announcements."""
        result = coinspot_collector._classify_announcement(
            "Scheduled Maintenance",
            "System maintenance scheduled for Sunday"
        )
        
        assert result["event_type"] == "exchange_maintenance"
        assert result["impact"] == 4  # Maintenance has lower impact
    
    def test_classify_announcement_default(self, coinspot_collector):
        """Test classification falls back to default for unknown types."""
        result = coinspot_collector._classify_announcement(
            "General Information",
            "Some general information about the platform"
        )
        
        assert result["event_type"] == "exchange_announcement"
        assert result["impact"] == 5  # Default impact
    
    def test_extract_currencies_from_text(self, coinspot_collector):
        """Test extraction of cryptocurrency symbols."""
        currencies = coinspot_collector._extract_currencies(
            "New Listing: Bitcoin (BTC) and Ethereum (ETH)",
            "BTC and ETH are now available"
        )
        
        assert "BTC" in currencies
        assert "ETH" in currencies
    
    def test_extract_currencies_none_found(self, coinspot_collector):
        """Test when no currencies are mentioned."""
        currencies = coinspot_collector._extract_currencies(
            "System Maintenance",
            "General maintenance announcement"
        )
        
        assert currencies == []
    
    @pytest.mark.asyncio
    async def test_validate_data_success(self, coinspot_collector):
        """Test data validation with valid data."""
        raw_data = [
            {
                "event_type": "exchange_listing",
                "title": "CoinSpot: New Listing - MATIC",
                "description": "Polygon now available",
                "source": "CoinSpot",
                "currencies": ["MATIC"],
                "impact_score": 9,
                "detected_at": datetime.now(timezone.utc),
                "url": "https://www.coinspot.com.au/news",
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        validated = await coinspot_collector.validate_data(raw_data)
        
        assert len(validated) == 1
        assert validated[0]["event_type"] == "exchange_listing"
        assert validated[0]["impact_score"] == 9
    
    @pytest.mark.asyncio
    async def test_validate_data_removes_invalid(self, coinspot_collector):
        """Test that validation removes invalid data."""
        raw_data = [
            {
                "event_type": "exchange_listing",
                "title": "Valid Announcement",
                "impact_score": 9,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing title
                "event_type": "exchange_listing",
                "impact_score": 9,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing event_type
                "title": "Missing Event Type",
                "impact_score": 9,
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        validated = await coinspot_collector.validate_data(raw_data)
        
        assert len(validated) == 1
        assert validated[0]["title"] == "Valid Announcement"
    
    @pytest.mark.asyncio
    async def test_validate_data_corrects_impact_score(self, coinspot_collector):
        """Test that invalid impact scores are corrected."""
        raw_data = [
            {
                "event_type": "exchange_listing",
                "title": "Invalid Impact",
                "impact_score": 20,  # Too high
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        validated = await coinspot_collector.validate_data(raw_data)
        
        assert len(validated) == 1
        assert validated[0]["impact_score"] == 5  # Corrected to default
    
    @pytest.mark.asyncio
    async def test_store_data(self, coinspot_collector):
        """Test storing data to database."""
        mock_session = MagicMock()
        
        data = [
            {
                "event_type": "exchange_listing",
                "title": "CoinSpot: New Listing",
                "description": "New token available",
                "source": "CoinSpot",
                "currencies": ["SOL"],
                "impact_score": 9,
                "detected_at": datetime.now(timezone.utc),
                "url": "https://www.coinspot.com.au",
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        count = await coinspot_collector.store_data(data, mock_session)
        
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_store_data_handles_errors(self, coinspot_collector):
        """Test that store continues after individual record errors."""
        mock_session = MagicMock()
        # Make add fail for the first record
        mock_session.add.side_effect = [Exception("DB error"), None]
        
        data = [
            {
                "event_type": "exchange_listing",
                "title": "Failing Record",
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "event_type": "exchange_maintenance",
                "title": "Succeeding Record",
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        count = await coinspot_collector.store_data(data, mock_session)
        
        # Should still store 1 record despite 1 failure
        assert count == 1
        assert mock_session.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_scrape_dynamic_not_implemented(self, coinspot_collector):
        """Test that dynamic scraping raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            await coinspot_collector.scrape_dynamic()
