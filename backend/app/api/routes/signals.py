"""Signal query API endpoints for accessing enrichment data."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import text
from sqlmodel import select

from app.api.deps import SessionDep
from app.enrichment.views import refresh_materialized_views
from app.models import NewsEnrichment, NewsItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/coin/{symbol}")
def get_coin_signals(
    session: SessionDep,
    symbol: str,
    hours: int = Query(24, description="Number of hours to look back"),
    enrichment_type: str | None = Query(
        None, description="Filter by enrichment type (optional)"
    ),
) -> dict[str, Any]:
    """
    Get all signals for a specific coin.

    Returns a list of enrichment signals and a summary with sentiment analysis.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    symbol_upper = symbol.upper()

    # Query enrichments where this symbol is in the currencies array
    statement = select(NewsEnrichment, NewsItem).where(
        NewsEnrichment.enriched_at >= cutoff,
    )

    if enrichment_type:
        statement = statement.where(NewsEnrichment.enrichment_type == enrichment_type)

    results = session.exec(statement).all()

    # Filter by symbol in currencies array (PostgreSQL ARRAY contains check)
    signals = []
    for enrichment, news_item in results:
        if symbol_upper in [c.upper() for c in (enrichment.currencies or [])]:
            signals.append((enrichment, news_item))

    # Build summary
    bullish_count = sum(
        1 for e, _ in signals if e.data and e.data.get("direction") == "bullish"
    )
    bearish_count = sum(
        1 for e, _ in signals if e.data and e.data.get("direction") == "bearish"
    )
    total = len(signals)
    neutral_count = total - bullish_count - bearish_count

    sentiment_score = (
        (bullish_count - bearish_count) / total * 100 if total > 0 else 0.0
    )
    avg_confidence = sum(e.confidence for e, _ in signals) / total if total > 0 else 0.0

    return {
        "coin": symbol_upper,
        "period_hours": hours,
        "signals": [
            {
                "id": e.id,
                "enricher": e.enricher_name,
                "type": e.enrichment_type,
                "data": e.data,
                "confidence": e.confidence,
                "enriched_at": e.enriched_at.isoformat() if e.enriched_at else None,
                "news_title": ni.title,
                "news_link": ni.link,
            }
            for e, ni in sorted(
                signals,
                key=lambda x: x[0].enriched_at
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
        ],
        "summary": {
            "total_signals": total,
            "avg_confidence": round(avg_confidence, 3),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "dominant_sentiment": (
                "bullish"
                if bullish_count > bearish_count
                else "bearish"
                if bearish_count > bullish_count
                else "neutral"
            ),
            "sentiment_score": round(sentiment_score, 1),
        },
    }


@router.get("/summary")
def get_signal_summary(session: SessionDep) -> list[dict[str, Any]]:
    """
    Get materialized view data for coin sentiment summary.

    Returns per-coin statistics from mv_coin_sentiment_24h.
    """
    try:
        result = session.execute(
            text("SELECT * FROM mv_coin_sentiment_24h ORDER BY signal_count DESC")
        )
        rows = result.fetchall()

        return [
            {
                "coin": row[0],
                "enrichment_type": row[1],
                "avg_confidence": float(row[2]) if row[2] else 0.0,
                "signal_count": int(row[3]) if row[3] else 0,
                "bullish_count": int(row[4]) if row[4] else 0,
                "bearish_count": int(row[5]) if row[5] else 0,
                "latest_signal": row[6].isoformat() if row[6] else None,
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"Failed to query mv_coin_sentiment_24h: {e}")
        return []


@router.get("/trends")
def get_signal_trends(
    session: SessionDep,
    coin: str | None = Query(None, description="Filter by coin (optional)"),
    hours: int = Query(168, description="Number of hours to look back"),
) -> list[dict[str, Any]]:
    """
    Get trend analysis from materialized view.

    Returns hourly aggregated signal data from mv_signal_summary.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = f"""
        SELECT coin, enricher_name, enrichment_type, hour_bucket, signal_count, avg_confidence, event_types
        FROM mv_signal_summary
        WHERE hour_bucket > '{cutoff.isoformat()}'
        """

        if coin:
            coin_upper = coin.upper()
            query += f" AND coin = '{coin_upper}'"

        query += " ORDER BY hour_bucket DESC"

        result = session.execute(text(query))
        rows = result.fetchall()

        return [
            {
                "coin": row[0],
                "enricher_name": row[1],
                "enrichment_type": row[2],
                "hour_bucket": row[3].isoformat() if row[3] else None,
                "signal_count": int(row[4]) if row[4] else 0,
                "avg_confidence": float(row[5]) if row[5] else 0.0,
                "event_types": row[6] if row[6] else [],
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"Failed to query mv_signal_summary: {e}")
        return []


@router.get("/entities")
def get_signal_entities(
    session: SessionDep,
    entity_name: str | None = Query(
        None, description="Filter by entity name (optional)"
    ),
    entity_type: str | None = Query(
        None, description="Filter by entity type (optional)"
    ),
    hours: int = Query(72, description="Number of hours to look back"),
) -> dict[str, Any]:
    """
    Get entity network from enrichment data.

    Extracts entities mentioned in enrichment signals and returns aggregated network data.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    statement = select(NewsEnrichment).where(
        NewsEnrichment.enrichment_type == "entity",
        NewsEnrichment.enriched_at >= cutoff,
    )

    results = session.exec(statement).all()

    # Aggregate entities
    entity_mentions: dict[str, dict[str, Any]] = {}
    relationships: list[dict[str, Any]] = []

    for enrichment in results:
        if not enrichment.data:
            continue

        entities_list = enrichment.data.get("entities", [])
        if not isinstance(entities_list, list):
            continue

        for entity in entities_list:
            if not isinstance(entity, dict):
                continue

            ent_name = entity.get("name")
            ent_type = entity.get("type")
            if not ent_name:
                continue

            # Filter if query params provided
            if entity_name and entity_name.lower() != ent_name.lower():
                continue
            if entity_type and ent_type and entity_type.lower() != ent_type.lower():
                continue

            if ent_name not in entity_mentions:
                entity_mentions[ent_name] = {
                    "name": ent_name,
                    "type": ent_type or "unknown",
                    "mention_count": 0,
                    "related_coins": set(),
                    "contexts": [],
                }

            entity_mentions[ent_name]["mention_count"] += 1
            entity_mentions[ent_name]["related_coins"].update(
                enrichment.currencies or []
            )
            context = entity.get("context")
            if context:
                entity_mentions[ent_name]["contexts"].append(context)

            # Track relationships
            related_entities = entity.get("related_entities", [])
            for related in related_entities:
                relationships.append(
                    {
                        "subject": ent_name,
                        "predicate": related.get("relationship", "related_to"),
                        "object": related.get("name", ""),
                        "count": 1,
                    }
                )

    return {
        "entities": [
            {
                "name": ent["name"],
                "type": ent["type"],
                "mention_count": ent["mention_count"],
                "related_coins": sorted(ent["related_coins"]),
                "contexts": ent["contexts"][:5],  # Limit to 5 contexts
            }
            for ent in sorted(
                entity_mentions.values(), key=lambda x: x["mention_count"], reverse=True
            )
        ],
        "relationships": relationships,
    }


@router.post("/refresh-views")
def refresh_views(session: SessionDep) -> dict[str, str]:
    """
    Trigger materialized view refresh.

    Refreshes mv_coin_sentiment_24h and mv_signal_summary.
    """
    try:
        refresh_materialized_views(session)
        return {"status": "refreshed"}
    except Exception as e:
        logger.error(f"Failed to refresh views: {e}")
        return {"status": "error", "detail": str(e)}
