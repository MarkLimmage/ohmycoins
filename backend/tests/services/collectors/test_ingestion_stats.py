import pytest
from datetime import datetime, timezone
from sqlmodel import Session, select, delete
from app.services.collectors.ingestion import DataIngestionService
from app.services.collectors.stats import CollectorStatsService
from app.services.collectors.metrics import get_metrics_tracker
from app.models import Signal, NewsItem, SentimentScore

def test_ingestion_service_news(db: Session):
    service = DataIngestionService(db)
    raw_data = [{
        "title": "Bitcoin Hits 100k",
        "link": "https://example.com/btc100k",
        "summary": "It happened!",
        "published": "2025-12-25T12:00:00Z",
        "author": "Satoshi"
    }]
    
    # Ensure fresh state
    db.exec(delete(NewsItem).where(NewsItem.link == "https://example.com/btc100k"))
    db.commit()
    
    count = service.ingest("test_collector", raw_data)
    assert count == 1
    
    # Verify DB
    news = db.exec(select(NewsItem).where(NewsItem.link == "https://example.com/btc100k")).first()
    assert news.title == "Bitcoin Hits 100k"
    assert news.source == "test_collector"

def test_ingestion_service_signal(db: Session):
    service = DataIngestionService(db)
    raw_data = [{
        "type": "price_update",
        "asset": "BTC/USDT",
        "strength": 0.8,
        "context": {"price": 100000}
    }]
    
    count = service.ingest("test_collector", raw_data)
    assert count == 1
    
    signal = db.exec(select(Signal).where(Signal.asset == "BTC/USDT").where(Signal.source == "test_collector")).first()
    assert signal is not None
    assert signal.type == "price_update"
    assert signal.strength == 0.8
    
def test_collector_stats_service():
    tracker = get_metrics_tracker()
    tracker.reset_metrics()
    
    # Simulate some activity
    tracker.record_success("test_collector", 10, 0.5)
    
    stats_service = CollectorStatsService()
    stats = stats_service.get_dashboard_stats()
    
    assert "collectors" in stats
    collectors = stats["collectors"]
    # Find test_collector
    found = next((c for c in collectors if c["name"] == "test_collector"), None)
    assert found is not None
    assert found["items_per_minute"] >= 0 # Depends on elapsed time which is small
    
    # Create another entry
    tracker.record_failure("failed_collector", "Timeout", 1.0)
    stats = stats_service.get_dashboard_stats()
    failed = next((c for c in stats["collectors"] if c["name"] == "failed_collector"), None)
    assert failed is not None
    assert failed["error_count"] == 1

