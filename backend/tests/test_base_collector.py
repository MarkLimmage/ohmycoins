
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.collectors.base import BaseCollector
from sqlmodel import Session

class MockCollector(BaseCollector):
    async def collect(self):
        return [{"test": "data"}]

    async def store_data(self, data, session):
        return len(data)

@pytest.fixture
def mock_collector():
    return MockCollector(name="test_collector", ledger="test_ledger")

@pytest.mark.asyncio
async def test_validate_data_default(mock_collector):
    data = [{"test": "data"}]
    validated = await mock_collector.validate_data(data)
    assert validated == data

@pytest.mark.asyncio
async def test_validate_data_invalid(mock_collector):
    data = "invalid"  # Not a list
    with pytest.raises(ValueError):
        await mock_collector.validate_data(data)

@pytest.mark.asyncio
async def test_collect_retry_success(mock_collector):
    mock_collector.collect = AsyncMock(return_value=[{"test": "data"}])
    result = await mock_collector._collect_with_retry()
    assert result == [{"test": "data"}]
    assert mock_collector.collect.call_count == 1

@pytest.mark.asyncio
async def test_collect_retry_failure(mock_collector):
    mock_collector.collect = AsyncMock(side_effect=Exception("API Error"))
    
    # We patch sleep to speed up tests
    with patch("tenacity.nap.time.sleep"):
        with pytest.raises(Exception, match="API Error"):
            await mock_collector._collect_with_retry()
            
    assert mock_collector.collect.call_count == 3  # stop_after_attempt(3)

