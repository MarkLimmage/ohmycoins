"""Signal query tools for Lab agents to access enrichment data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session, select

from app.core.db import engine
from app.models import NewsEnrichment


def query_market_signals(coin: str, hours: int = 24) -> dict[str, Any]:
    """Query enrichment signals for a cryptocurrency.

    Returns sentiment summary and recent signals for trading decisions.

    Args:
        coin: Cryptocurrency symbol (e.g., "BTC", "ETH")
        hours: Number of hours to look back

    Returns:
        Dictionary with sentiment summary and recent signals
    """
    with Session(engine) as session:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        statement = select(NewsEnrichment).where(
            NewsEnrichment.enriched_at >= cutoff,
        )
        results = session.exec(statement).all()

        # Filter by coin in currencies array
        coin_upper = coin.upper()
        signals = [
            r
            for r in results
            if coin_upper in [c.upper() for c in (r.currencies or [])]
        ]

        # Build summary
        bullish = sum(
            1 for r in signals if r.data and r.data.get("direction") == "bullish"
        )
        bearish = sum(
            1 for r in signals if r.data and r.data.get("direction") == "bearish"
        )
        total = len(signals)
        neutral = total - bullish - bearish

        avg_confidence = (
            sum(r.confidence for r in signals) / total if total > 0 else 0.0
        )
        sentiment_score = (bullish - bearish) / total * 100 if total > 0 else 0.0

        return {
            "coin": coin_upper,
            "period_hours": hours,
            "total_signals": total,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "sentiment_score": round(sentiment_score, 1),
            "avg_confidence": round(avg_confidence, 3),
            "recent_signals": [
                {
                    "enricher": r.enricher_name,
                    "type": r.enrichment_type,
                    "data": r.data,
                    "confidence": r.confidence,
                    "enriched_at": r.enriched_at.isoformat() if r.enriched_at else None,
                }
                for r in sorted(
                    signals,
                    key=lambda x: x.enriched_at
                    or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True,
                )[:10]
            ],
        }
