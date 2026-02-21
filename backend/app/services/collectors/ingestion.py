from typing import Any, Dict, List
from sqlmodel import Session, select
from datetime import datetime, timezone
from app.models import NewsItem, Signal, SentimentScore
import logging

class DataIngestionService:
    """
    Normalizes and persists data collected from plugins.
    """
    
    def __init__(self, session: Session):
        self.session = session

    # ... (ingest method logic to remain, but fixing syntax below)
    
    def ingest(self, collector_name: str, data: List[Dict[str, Any]]) -> int:
        """
        Ingests a list of raw data items from a collector.
        Returns the count of new items added.
        """
        count = 0
        for item in data:
            try:
                # Basic heuristic
                if "title" in item and "link" in item:
                    # Likely a News Item
                    if self._save_news_item(collector_name, item):
                        count += 1
                elif "type" in item and "asset" in item and "strength" in item:
                    # Likely a Signal
                    if self._save_signal(collector_name, item):
                        count += 1
                elif "asset" in item and "score" in item:
                    # Likely a Sentiment Score
                    if self._save_sentiment(collector_name, item):
                        count += 1
                else:
                    logging.warning(f"Unknown data format from {collector_name}: {list(item.keys())}")
                    
            except Exception as e:
                logging.error(f"Error ingesting item from {collector_name}: {e}")
                
        try:
            self.session.commit()
        except Exception as e:
            logging.error(f"Commit failed during ingestion: {e}")
            self.session.rollback()
            return 0
            
        return count



    def _save_news_item(self, source: str, data: Dict[str, Any]) -> bool:
        # Check for duplicates using link
        url = data.get("link") or data.get("url")
        if not url:
            return False
            
        try:
            statement = select(NewsItem).where(NewsItem.link == url)
            existing = self.session.exec(statement).first()
        except Exception:
            # Fallback if link is not link
            return False
            
        if existing:
            return False
            
        # Basic date parsing placeholder
        published = data.get("published")
        if isinstance(published, str):
            try:
                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                published_dt = datetime.now(timezone.utc)
        else:
            published_dt = datetime.now(timezone.utc)
            
        news = NewsItem(
            title=data.get("title", "Untitled"),
            link=url,
            summary=data.get("summary") or data.get("content", ""),
            source=source,
            published_at=published_dt,
            collected_at=datetime.now(timezone.utc)
            # author not in existing model
        )
        self.session.add(news)
        return True

    def _save_signal(self, source: str, data: Dict[str, Any]) -> bool:
        signal = Signal(
            type=data.get("type", "unknown"),
            asset=data.get("asset") or data.get("symbol", "unknown"),
            strength=float(data.get("strength", 0.0)),
            source=source,
            context=data,  # Store full raw data in generic json field
            generated_at=datetime.now(timezone.utc)
            # symbol -> asset
        )
        self.session.add(signal)
        return True

    def _save_sentiment(self, source: str, data: Dict[str, Any]) -> bool:
        sentiment = SentimentScore(
            asset=data.get("asset") or data.get("symbol", "unknown"),
            score=float(data.get("score", 0.0)),
            magnitude=float(data.get("magnitude", 0.0)),
            timestamp=datetime.now(timezone.utc),
            source=source,
            raw_data=data
        )
        self.session.add(sentiment)
        return True

