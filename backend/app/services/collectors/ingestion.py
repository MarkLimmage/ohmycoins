import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import NewsItem, SentimentScore, Signal


class DataIngestionService:
    """
    Normalizes and persists data collected from plugins.
    """

    def __init__(self, session: Session):
        self.session = session

    # ... (ingest method logic to remain, but fixing syntax below)

    def ingest(self, collector_name: str, data: list[dict[str, Any]]) -> int:
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
                    logging.warning(
                        f"Unknown data format from {collector_name}: {list(item.keys())}"
                    )

            except Exception as e:
                logging.error(f"Error ingesting item from {collector_name}: {e}")

        try:
            self.session.commit()
        except Exception as e:
            logging.error(f"Commit failed during ingestion: {e}")
            self.session.rollback()
            return 0

        return count

    def _save_news_item(self, source: str, data: dict[str, Any]) -> bool:
        # Check for duplicates using link
        query = select(NewsItem).where(NewsItem.link == data["link"])
        existing = self.session.exec(query).first()
        if existing:
            return False

        # Basic date parsing placeholder
        _published = data.get("published")
        # In real scenario, parse published which is likely a string

        news = NewsItem(
            title=data.get("title"),
            link=data.get("link"),
            # published_at=published, # Assume pre-parsed or valid type for now
            summary=data.get("summary"),
            source=source,
            collected_at=datetime.utcnow(),
        )
        self.session.add(news)
        return True

    def _save_signal(self, source: str, data: dict[str, Any]) -> bool:
        signal = Signal(
            type=data.get("type"),
            asset=data.get("asset"),
            strength=data.get("strength"),
            source=source,
            context=data.get("context", {}),
            generated_at=datetime.utcnow(),
        )
        self.session.add(signal)
        return True

    def _save_sentiment(self, source: str, data: dict[str, Any]) -> bool:
        sentiment = SentimentScore(
            asset=data.get("asset"),
            source=source,
            score=data.get("score"),
            magnitude=data.get("magnitude"),
            raw_data=data.get("raw_data", {}),
            timestamp=datetime.utcnow(),
        )
        self.session.add(sentiment)
        return True
