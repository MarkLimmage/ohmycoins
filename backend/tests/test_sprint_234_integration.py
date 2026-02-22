import pytest
from unittest.mock import MagicMock
import sys
# Mock feedparser and ccxt to ensure tests run even without deps if we use mocks (but we want to test deps)
# Actually, the container should have them.

def test_sprint_2_34_imports():
    """Verify that all Sprint 2.34 components are importable and dependencies are met."""
    
    # Track A: Glass & Human
    from app.collectors.strategies.glass_chain_walker import GlassChainWalker
    assert GlassChainWalker
    
    from app.collectors.strategies.human_rss import HumanRSSCollector
    assert HumanRSSCollector
    import feedparser
    assert feedparser.__version__

    # Track B: Exchange & Catalyst (CCXT)
    try:
        from app.services.collectors.ccxt_collector import CCXTCollector
        assert CCXTCollector
        import ccxt
        assert ccxt.__version__
    except ImportError as e:
        pytest.fail(f"Failed to import CCXT components: {e}")

    # Track B: Catalyst Simulation (simulated_calendar)
    try:
        from app.services.collectors.catalyst.simulated_calendar import SimulatedCalendarCollector
        assert SimulatedCalendarCollector
    except ImportError as e:
        pytest.fail(f"Failed to import Catalyst components: {e}")

def test_collector_registration():
    """Verify that new collectors are registered in the config (if applicable)."""
    from app.services.collectors.config import setup_collectors
    assert setup_collectors