from typing import Generator
import pytest
from sqlmodel import Session, SQLModel, create_engine
from app.core import db
from app.models import Collector, NewsItem, Signal, SentimentScore
from app.services.collectors.ingestion import DataIngestionService

# Use an in-memory SQLite database for testing ingestion logic
# to avoid polluting the main test DB or needing complex setup
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=None
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_ingest_news_item(session: Session):
    service = DataIngestionService(session)
    
    data = [{
        "title": "Test News",
        "link": "https://example.com/news/1",
        "published": "2023-10-26T12:00:00Z",
        "summary": "This is a test summary.",
        "source": "Test Source"
    }]
    
    count = service.ingest("TestCollector", data)
    assert count == 1
    
    # Verify DB
    news = session.query(NewsItem).first()
    assert news is not None
    assert news.title == "Test News"
    assert news.source == "TestCollector"

def test_ingest_duplicate_news(session: Session):
    service = DataIngestionService(session)
    data = [{
        "title": "Test News",
        "link": "https://example.com/news/1", 
        "source": "Test"
    }]
    
    # First ingest
    service.ingest("TestCollector", data)
    
    # Second ingest of same link
    count = service.ingest("TestCollector", data)
    assert count == 0
    
    items = session.query(NewsItem).all()
    assert len(items) == 1

def test_ingest_signal(session: Session):
    service = DataIngestionService(session)
    data = [{
        "type": "buy",
        "asset": "BTC",
        "strength": 0.8,
        "context": {"reason": "RSI oversold"}
    }]
    
    count = service.ingest("SignalBot", data)
    assert count == 1
    
    signal = session.query(Signal).first()
    assert signal.asset == "BTC"
    assert signal.type == "buy"
    assert signal.source == "SignalBot"

def test_ingest_unknown_format(session: Session):
    service = DataIngestionService(session)
    data = [{"random": "data"}]
    
    # Should handle gracefully and return 0
    count = service.ingest("BadCollector", data)
    assert count == 0
