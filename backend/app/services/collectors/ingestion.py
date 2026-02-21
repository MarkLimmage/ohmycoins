from typing import Any, Dict, List
from sqlmodel import Session, select
from datetime import datetime
from decimal import Decimal
from app.models import NewsItem, Signal, SentimentScore, PriceData5Min
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
                # Determine item type
                item_type = item.get("type", "unknown")
                
                if item_type == "price":
                    if self._save_price_data(item):
                        count += 1
                elif "title" in item and "link" in item:
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
        
    def _save_price_data(self, data: Dict[str, Any]) -> bool:
        """Save price data to PriceData5Min table."""
        coin_type = data.get("coin_type")
        timestamp_str = data.get("timestamp")
        
        if not coin_type or not timestamp_str:
            return False
            
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            # Check for existing record
            statement = select(PriceData5Min).where(
                PriceData5Min.coin_type == coin_type,
                PriceData5Min.timestamp == timestamp
            )
            existing = self.session.exec(statement).first()
            if existing:
                return False
                
            price_record = PriceData5Min(
                coin_type=coin_type,
                bid=Decimal(str(data.get("bid"))),
                ask=Decimal(str(data.get("ask"))),
                last=Decimal(str(data.get("last"))),
                timestamp=timestamp
            )
            self.session.add(price_record)
            return True
        except Exception as e:
            logging.error(f"Error saving price data for {coin_type}: {e}")
            return False

    def _save_news_item(self, source: str, data: Dict[str, Any]) -> bool:
        # Check for duplicates using link
        query = select(NewsItem).where(NewsItem.link == data["link"])
        existing = self.session.exec(query).first()
        if existing:
            return False
            
        # Basic date parsing placeholder
        published = data.get("published")
        # In real scenario, parse published which is likely a string
        
        news = NewsItem(
            title=data.get("title"),
            link=data.get("link"),
            # published_at=published, # Assume pre-parsed or valid type for now
            summary=data.get("summary"),
            source=source,
            collected_at=datetime.utcnow()
        )
        self.session.add(news)
        return True

    def _save_signal(self, source: str, data: Dict[str, Any]) -> bool:
        signal = Signal(
            type=data.get("type"),
            asset=data.get("asset"),
            strength=data.get("strength"),
            source=source,
            context=data.get("context", {}),
            generated_at=datetime.utcnow()
        )
        self.session.add(signal)
        return True

    def _save_sentiment(self, source: str, data: Dict[str, Any]) -> bool:
        sentiment = SentimentScore(
            asset=data.get("asset"),
            source=source,
            score=data.get("score"),
            magnitude=data.get("magnitude"),
            raw_data=data.get("raw_data", {}),
            timestamp=datetime.utcnow()
        )
        self.session.add(sentiment)
        return True
