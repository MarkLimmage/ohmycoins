
import logging
import sys
from datetime import datetime, timezone
from sqlmodel import Session, select, delete

# Add parent directory to path to import app
sys.path.append(".")

from app.core.db import engine, init_db
from app.models import NewsItem, Signal, SentimentScore
from app.services.collectors.ingestion import DataIngestionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ingestion():
    with Session(engine) as session:
        # cleanup
        session.exec(delete(NewsItem).where(NewsItem.source == "test_ingestion"))
        session.exec(delete(Signal).where(Signal.source == "test_ingestion"))
        session.exec(delete(SentimentScore).where(SentimentScore.source == "test_ingestion"))
        session.commit()

        service = DataIngestionService(session)
        
        # Test Data
        test_data = [
            {
                "title": "Test News Article",
                "link": "https://example.com/news/1",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "summary": "This is a test summary.",
                "sentiment_score": 0.8,
                "sentiment_label": "positive"
            },
            {
                "type": "buy",
                "asset": "BTC",
                "strength": 0.9,
                "context": {"reason": "Test signal"}
            },
            {
                "asset": "ETH",
                "score": 0.5,
                "magnitude": 0.7,
                "raw_data": {"test": "data"}
            }
        ]
        
        logger.info("Ingesting test data...")
        count = service.ingest("test_ingestion", test_data)
        logger.info(f"Ingested {count} items.")
        
        # Verify
        news = session.exec(select(NewsItem).where(NewsItem.source == "test_ingestion")).all()
        signals = session.exec(select(Signal).where(Signal.source == "test_ingestion")).all()
        sentiments = session.exec(select(SentimentScore).where(SentimentScore.source == "test_ingestion")).all()
        
        logger.info(f"News items: {len(news)}")
        logger.info(f"Signals: {len(signals)}")
        logger.info(f"Sentiment scores: {len(sentiments)}")
        
        if len(news) == 1 and len(signals) == 1 and len(sentiments) == 1:
            logger.info("SUCCESS: All models populated correctly.")
        else:
            logger.error("FAILURE: Incorrect number of items.")

if __name__ == "__main__":
    test_ingestion()
