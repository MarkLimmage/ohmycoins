import pytest
from app.core.collectors.registry import CollectorRegistry
from app.core.collectors.base import ICollector

class MockCollector(ICollector):
    @property
    def name(self) -> str:
        return "mock_strategy"
        
    @property
    def description(self) -> str:
        return "Mock Description"
        
    def get_config_schema(self):
        return {}
        
    def validate_config(self, config):
        return True
        
    async def test_connection(self, config):
        return True
        
    async def collect(self, config):
        return []

def test_manual_registration():
    CollectorRegistry.register(MockCollector)
    strategy = CollectorRegistry.get_strategy("mock_strategy")
    assert strategy is not None
    assert strategy().name == "mock_strategy"

def test_auto_discovery():
    # Trigger discovery - this should find the CoinDesk strategy we added
    CollectorRegistry.discover_strategies()
    strategies = CollectorRegistry.list_strategies()
    
    assert "news_coindesk" in strategies, "CoinDesk strategy should be auto-discovered"
    
    coindesk_cls = strategies["news_coindesk"]
    instance = coindesk_cls()
    assert instance.name == "news_coindesk"
    assert "RSS feed" in instance.description
