import pytest
from app.services.collectors.scraper import WebScraperCollector
from app.services.collectors.factory import CollectorFactory

@pytest.mark.asyncio
async def test_web_scraper_collector_lifecycle():
    config = {
        "url": "https://example.com",
        "selectors": {"title": "h1"}
    }
    collector = WebScraperCollector(name="test_scraper", config=config)
    
    assert collector.name == "test_scraper"
    assert collector.target_url == "https://example.com"
    assert collector.selectors == {"title": "h1"}
    
    # Test collect method (mocked)
    data = await collector.collect()
    assert len(data) == 1
    assert data[0]["url"] == "https://example.com"
    assert data[0]["status"] == "mock_scraped"

def test_factory_creation():
    config = {
        "name": "factory_scraper",
        "url": "https://factory.com",
        "selectors": {"price": ".price"}
    }
    
    collector = CollectorFactory.create_collector("WebScraperCollector", config)
    
    assert isinstance(collector, WebScraperCollector)
    assert collector.name == "factory_scraper"
    assert collector.target_url == "https://factory.com"
    assert collector.selectors == {"price": ".price"}
