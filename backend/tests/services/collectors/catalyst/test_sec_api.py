from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import Session

from app.models import CatalystEvents
from app.services.collectors.catalyst.sec_api import SECAPICollector

# Mock data
MOCK_SEC_RESPONSE_COINBASE = {
    "cik": "0001679788",
    "name": "Coinbase Global, Inc.",
    "filings": {
        "recent": {
            "accessionNumber": [
                "0001679788-24-000001",
                "0001679788-24-000002",
                "0001679788-24-000003"
            ],
            "filingDate": [
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d"),
                "2020-01-01"  # Old filing
            ],
            "reportDate": [
                "2024-01-01",
                "2024-01-02",
                "2020-01-01"
            ],
            "form": [
                "8-K",
                "4",
                "10-K"
            ],
            "primaryDocument": [
                "filing1.htm",
                "filing2.xml",
                "filing3.htm"
            ],
            "primaryDocDescription": [
                "Current Report",
                "Statement of Changes in Beneficial Ownership",
                "Annual Report"
            ]
        }
    }
}

@pytest.fixture
def collector():
    return SECAPICollector()

@pytest.mark.asyncio
async def test_collect_success(collector):
    """Test successful collection of SEC filings."""
    # Mock fetch_json to return simulated SEC data
    collector.fetch_json = AsyncMock(return_value=MOCK_SEC_RESPONSE_COINBASE)

    # We only want to test one company to be fast
    collector.MONITORED_COMPANIES = {"0001679788": "Coinbase"}

    filings = await collector.collect()

    # Expect 2 filings (8-K and 4), 10-K is too old
    assert len(filings) == 2

    # Verify first filing (8-K)
    filing_8k = next(f for f in filings if "8-K" in f["title"])
    assert filing_8k["event_type"] == "sec_filing_8_k"
    assert "Coinbase" in filing_8k["title"]
    assert filing_8k["impact_score"] == 8
    assert "BTC" in filing_8k["currencies"]
    assert "ETH" in filing_8k["currencies"]
    assert "https://www.sec.gov/Archives/edgar/data/0001679788/000167978824000001/filing1.htm" == filing_8k["url"]

    # Verify second filing (4)
    filing_4 = next(f for f in filings if "Form 4" in f["title"])
    assert filing_4["event_type"] == "sec_filing_4"
    assert filing_4["impact_score"] == 5

@pytest.mark.asyncio
async def test_collect_api_error(collector):
    """Test handling of API errors."""
    collector.fetch_json = AsyncMock(side_effect=Exception("API Error"))
    collector.MONITORED_COMPANIES = {"0001679788": "Coinbase"}

    filings = await collector.collect()

    assert filings == []

@pytest.mark.asyncio
async def test_validate_data(collector):
    """Test data validation logic."""
    raw_data = [
        {
            "title": "Valid Filing",
            "event_type": "sec_filing_8_k",
            "impact_score": 8,
            "detected_at": datetime.now(timezone.utc),
            "collected_at": datetime.now(timezone.utc)
        },
        {
            "title": "Invalid Score",
            "event_type": "sec_filing_4",
            "impact_score": 99,  # Invalid
            "detected_at": datetime.now(timezone.utc),
            "collected_at": datetime.now(timezone.utc)
        },
        {
            "event_type": "sec_filing_4"
            # Missing title
        }
    ]

    validated = await collector.validate_data(raw_data)

    assert len(validated) == 2
    assert validated[0]["title"] == "Valid Filing"
    assert validated[1]["title"] == "Invalid Score"
    assert validated[1]["impact_score"] == 5  # Should be corrected to default

@pytest.mark.asyncio
async def test_store_data(collector):
    """Test storing data to database."""
    session = MagicMock(spec=Session)

    data = [
        {
            "title": "Filing 1",
            "event_type": "sec_filing_8_k",
            "impact_score": 8,
            "detected_at": datetime.now(timezone.utc),
            "collected_at": datetime.now(timezone.utc),
            "url": "http://example.com/1"
        }
    ]

    count = await collector.store_data(data, session)

    assert count == 1
    session.add.assert_called_once()
    session.commit.assert_called_once()

    # Verify the object added
    call_args = session.add.call_args
    stored_obj = call_args[0][0]
    assert isinstance(stored_obj, CatalystEvents)
    assert stored_obj.title == "Filing 1"
    assert stored_obj.event_type == "sec_filing_8_k"
