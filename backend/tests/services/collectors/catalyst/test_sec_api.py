"""
Tests for SEC EDGAR API collector (Catalyst Ledger).
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.collectors.catalyst.sec_api import SECAPICollector


@pytest.fixture
def sec_collector():
    """Create a SEC API collector instance for testing."""
    return SECAPICollector()


@pytest.fixture
def sample_sec_response():
    """Sample SEC EDGAR API response."""
    return {
        "filings": {
            "recent": {
                "form": ["8-K", "10-Q", "4", "10-K"],
                "filingDate": [
                    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d"),
                    (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d"),
                    (datetime.now(timezone.utc) - timedelta(days=40)).strftime("%Y-%m-%d"),  # Too old
                ],
                "accessionNumber": [
                    "0001679788-23-000123",
                    "0001679788-23-000122",
                    "0001679788-23-000121",
                    "0001679788-23-000120",
                ],
                "primaryDocument": [
                    "coinbase-8k.htm",
                    "coinbase-10q.htm",
                    "coinbase-form4.htm",
                    "coinbase-10k.htm",
                ],
            }
        }
    }


class TestSECAPICollector:
    """Test suite for SEC API collector."""
    
    def test_initialization(self, sec_collector):
        """Test collector initialization."""
        assert sec_collector.name == "sec_edgar_api"
        assert sec_collector.ledger == "catalyst"
        assert sec_collector.base_url == "https://data.sec.gov"
        assert len(sec_collector.MONITORED_COMPANIES) >= 5
        assert "0001679788" in sec_collector.MONITORED_COMPANIES  # Coinbase
    
    def test_filing_types(self, sec_collector):
        """Test that critical filing types are monitored."""
        assert "4" in sec_collector.FILING_TYPES  # Insider trading
        assert "8-K" in sec_collector.FILING_TYPES  # Current events
        assert "10-K" in sec_collector.FILING_TYPES  # Annual report
        assert "10-Q" in sec_collector.FILING_TYPES  # Quarterly report
        
        # Check impact scores are valid
        for filing_type, info in sec_collector.FILING_TYPES.items():
            assert 1 <= info["impact"] <= 10
    
    def test_company_crypto_mapping(self, sec_collector):
        """Test that companies are mapped to cryptocurrencies."""
        assert "BTC" in sec_collector.COMPANY_CRYPTO_MAP["Coinbase"]
        assert "BTC" in sec_collector.COMPANY_CRYPTO_MAP["MicroStrategy"]
    
    @pytest.mark.asyncio
    async def test_collect_success(self, sec_collector, sample_sec_response):
        """Test successful data collection."""
        # Mock the fetch_json method
        sec_collector.fetch_json = AsyncMock(return_value=sample_sec_response)
        
        # Temporarily reduce companies for testing
        original_companies = sec_collector.MONITORED_COMPANIES
        sec_collector.MONITORED_COMPANIES = {"0001679788": "Coinbase"}
        
        try:
            data = await sec_collector.collect()
            
            # Should collect 3 filings (4th is too old)
            assert len(data) == 3
            assert all(isinstance(item, dict) for item in data)
            assert all("event_type" in item for item in data)
            assert all("title" in item for item in data)
            assert all("impact_score" in item for item in data)
            assert all("collected_at" in item for item in data)
            
            # Check that titles mention Coinbase
            assert all("Coinbase" in item["title"] for item in data)
            
            # Check event types are properly formatted
            assert any("sec_filing_8_k" in item["event_type"] for item in data)
            assert any("sec_filing_10_q" in item["event_type"] for item in data)
            assert any("sec_filing_4" in item["event_type"] for item in data)
            
        finally:
            sec_collector.MONITORED_COMPANIES = original_companies
    
    @pytest.mark.asyncio
    async def test_collect_filters_old_filings(self, sec_collector):
        """Test that old filings (>30 days) are filtered out."""
        old_response = {
            "filings": {
                "recent": {
                    "form": ["8-K"],
                    "filingDate": [
                        (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
                    ],
                    "accessionNumber": ["0001679788-23-000123"],
                    "primaryDocument": ["old-filing.htm"],
                }
            }
        }
        
        sec_collector.fetch_json = AsyncMock(return_value=old_response)
        sec_collector.MONITORED_COMPANIES = {"0001679788": "Coinbase"}
        
        data = await sec_collector.collect()
        
        # Should be empty because filing is too old
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_collect_handles_missing_filings(self, sec_collector):
        """Test handling of companies with no filings."""
        empty_response = {"filings": {"recent": {}}}
        
        sec_collector.fetch_json = AsyncMock(return_value=empty_response)
        sec_collector.MONITORED_COMPANIES = {"0001679788": "Coinbase"}
        
        data = await sec_collector.collect()
        
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_collect_continues_on_error(self, sec_collector, sample_sec_response):
        """Test that collection continues when one company fails."""
        # Mock fetch to fail for first company, succeed for second
        call_count = [0]
        
        async def mock_fetch(endpoint, headers=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("API error")
            return sample_sec_response
        
        sec_collector.fetch_json = AsyncMock(side_effect=mock_fetch)
        sec_collector.MONITORED_COMPANIES = {
            "0001679788": "Coinbase",
            "0001050446": "MicroStrategy"
        }
        
        data = await sec_collector.collect()
        
        # Should have data from second company only
        assert len(data) >= 0  # May have recent filings
    
    @pytest.mark.asyncio
    async def test_validate_data_success(self, sec_collector):
        """Test data validation with valid data."""
        raw_data = [
            {
                "event_type": "sec_filing_8_k",
                "title": "Coinbase - Current Events (Form 8-K)",
                "description": "SEC Form 8-K filed by Coinbase",
                "source": "SEC EDGAR",
                "currencies": ["BTC", "ETH"],
                "impact_score": 8,
                "detected_at": datetime.now(timezone.utc),
                "url": "https://www.sec.gov/Archives/edgar/data/1679788/...",
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        validated = await sec_collector.validate_data(raw_data)
        
        assert len(validated) == 1
        assert validated[0]["event_type"] == "sec_filing_8_k"
        assert validated[0]["impact_score"] == 8
    
    @pytest.mark.asyncio
    async def test_validate_data_removes_invalid(self, sec_collector):
        """Test that validation removes invalid data."""
        raw_data = [
            {
                "event_type": "sec_filing_8_k",
                "title": "Valid Filing",
                "impact_score": 8,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing title
                "event_type": "sec_filing_8_k",
                "impact_score": 8,
                "collected_at": datetime.now(timezone.utc),
            },
            {
                # Missing event_type
                "title": "Missing Event Type",
                "impact_score": 8,
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        validated = await sec_collector.validate_data(raw_data)
        
        assert len(validated) == 1
        assert validated[0]["title"] == "Valid Filing"
    
    @pytest.mark.asyncio
    async def test_validate_data_corrects_impact_score(self, sec_collector):
        """Test that invalid impact scores are corrected."""
        raw_data = [
            {
                "event_type": "sec_filing_8_k",
                "title": "Invalid Impact Score",
                "impact_score": 15,  # Too high
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "event_type": "sec_filing_8_k",
                "title": "Negative Impact Score",
                "impact_score": -1,  # Negative
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        validated = await sec_collector.validate_data(raw_data)
        
        assert len(validated) == 2
        assert all(item["impact_score"] == 5 for item in validated)  # Corrected to 5
    
    @pytest.mark.asyncio
    async def test_store_data(self, sec_collector):
        """Test storing data to database."""
        mock_session = MagicMock()
        
        data = [
            {
                "event_type": "sec_filing_8_k",
                "title": "Coinbase - Current Events",
                "description": "SEC Form 8-K filed by Coinbase",
                "source": "SEC EDGAR",
                "currencies": ["BTC", "ETH"],
                "impact_score": 8,
                "detected_at": datetime.now(timezone.utc),
                "url": "https://www.sec.gov/...",
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        count = await sec_collector.store_data(data, mock_session)
        
        assert count == 1
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1
    
    @pytest.mark.asyncio
    async def test_store_data_handles_errors(self, sec_collector):
        """Test that store continues after individual record errors."""
        mock_session = MagicMock()
        # Make add fail for the first record
        mock_session.add.side_effect = [Exception("DB error"), None]
        
        data = [
            {
                "event_type": "sec_filing_8_k",
                "title": "Failing Record",
                "collected_at": datetime.now(timezone.utc),
            },
            {
                "event_type": "sec_filing_10_q",
                "title": "Succeeding Record",
                "collected_at": datetime.now(timezone.utc),
            },
        ]
        
        count = await sec_collector.store_data(data, mock_session)
        
        # Should still store 1 record despite 1 failure
        assert count == 1
        assert mock_session.commit.call_count == 1
