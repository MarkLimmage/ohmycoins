from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.trading.safety import TradingSafetyManager
from app.services.trading.watcher import HardStopWatcher


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    # Mock return values for common methods
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.from_url = AsyncMock(return_value=mock)
    return mock

@pytest.fixture
def mock_session():
    mock = AsyncMock()
    mock.exec = AsyncMock()
    # Mock exec().all() and exec().first()
    mock_result = AsyncMock()
    mock_result.all.return_value = []
    mock_result.first.return_value = None
    mock_result.one.return_value = Decimal("0")

    mock.exec.return_value = mock_result
    return mock

@pytest.mark.asyncio
async def test_initial_equity_setting(mock_redis):
    # Setup
    watcher = HardStopWatcher()
    watcher.redis_client = mock_redis

    # Mock Total Equity to be 10000
    with patch("app.services.trading.watcher.HardStopWatcher.calculate_total_equity", new_callable=AsyncMock) as mock_calc:
        mock_calc.return_value = Decimal("10000")

        # Test Case: Initial not set
        mock_redis.get.return_value = None

        with patch.object(TradingSafetyManager, "activate_emergency_stop", new_callable=AsyncMock) as mock_stop:
            await watcher.check_equity(mock_session)

            # Assertions
            mock_redis.set.assert_called_with("omc:initial_equity", str(Decimal("10000")))
            mock_stop.assert_not_called()

@pytest.mark.asyncio
async def test_hard_stop_trigger(mock_redis):
    # Setup
    watcher = HardStopWatcher()
    watcher.redis_client = mock_redis

    # Mock Initial Equity as 10000
    mock_redis.get.side_effect = lambda k: "10000" if k == "omc:initial_equity" else None

    # Mock Current Equity as 9000 (10% drop, triggers 5% stop)
    with patch("app.services.trading.watcher.HardStopWatcher.calculate_total_equity", new_callable=AsyncMock) as mock_calc:
        mock_calc.return_value = Decimal("9000")

        with patch.object(TradingSafetyManager, "activate_emergency_stop", new_callable=AsyncMock) as mock_stop:
            await watcher.check_equity(mock_session)

            # Assertions
            mock_stop.assert_called_once()

@pytest.mark.asyncio
async def test_hard_stop_safe(mock_redis):
    # Setup
    watcher = HardStopWatcher()
    watcher.redis_client = mock_redis

    # Mock Initial Equity as 10000
    mock_redis.get.side_effect = lambda k: "10000" if k == "omc:initial_equity" else None

    # Mock Current Equity as 9600 (4% drop, safe)
    with patch("app.services.trading.watcher.HardStopWatcher.calculate_total_equity", new_callable=AsyncMock) as mock_calc:
        mock_calc.return_value = Decimal("9600")

        with patch.object(TradingSafetyManager, "activate_emergency_stop", new_callable=AsyncMock) as mock_stop:
            await watcher.check_equity(mock_session)

            # Assertions
            mock_stop.assert_not_called()

# Integration style test with DB session mocking more deeply (optional, but good for coverage)
