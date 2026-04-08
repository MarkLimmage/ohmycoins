"""Materialized views for enrichment data and feature store."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)

# Enrichment views (existing)
ENRICHMENT_VIEWS = [
    "mv_coin_sentiment_24h",
    "mv_signal_summary",
]

# Feature Store views (must refresh in dependency order)
FEATURE_STORE_VIEWS = [
    "mv_coin_targets_5min",
    "mv_sentiment_signals_1h",
    "mv_catalyst_impact_decay",
    "mv_training_set_v1",
]

# --- Materialized View SQL Definitions ---
# These are the canonical SQL for each view. Used by migrations to CREATE/REPLACE.

MV_COIN_SENTIMENT_24H_SQL = """\
SELECT
    coin,
    enrichment_type,
    AVG(avg_confidence) AS avg_confidence,
    SUM(signal_count) AS signal_count,
    SUM(bullish_count) AS bullish_count,
    SUM(bearish_count) AS bearish_count,
    MAX(latest_signal) AS latest_signal
FROM (
    -- News enrichment signals
    SELECT
        unnest(ne.currencies) AS coin,
        ne.enrichment_type,
        ne.confidence AS avg_confidence,
        1 AS signal_count,
        CASE WHEN ne.data->>'direction' = 'bullish'
             OR ne.data->'coins' @> '[{"direction": "bullish"}]' THEN 1 ELSE 0 END AS bullish_count,
        CASE WHEN ne.data->>'direction' = 'bearish'
             OR ne.data->'coins' @> '[{"direction": "bearish"}]' THEN 1 ELSE 0 END AS bearish_count,
        ne.enriched_at AS latest_signal
    FROM news_enrichment ne
    WHERE ne.enriched_at > NOW() - INTERVAL '24 hours'

    UNION ALL

    -- Social sentiment scores (reddit_llm, news_llm)
    SELECT
        ss.asset AS coin,
        'sentiment' AS enrichment_type,
        ss.magnitude AS avg_confidence,
        1 AS signal_count,
        CASE WHEN ss.score > 0.1 THEN 1 ELSE 0 END AS bullish_count,
        CASE WHEN ss.score < -0.1 THEN 1 ELSE 0 END AS bearish_count,
        ss.timestamp AS latest_signal
    FROM sentiment_score ss
    WHERE ss.source IN ('reddit_llm', 'news_llm')
      AND ss.timestamp > NOW() - INTERVAL '24 hours'
) combined
GROUP BY coin, enrichment_type
"""

MV_SIGNAL_SUMMARY_SQL = """\
SELECT
    coin,
    enricher_name,
    enrichment_type,
    hour_bucket,
    SUM(signal_count) AS signal_count,
    AVG(avg_confidence) AS avg_confidence,
    jsonb_agg(DISTINCT event_types) FILTER (WHERE event_types IS NOT NULL) AS event_types
FROM (
    -- News enrichment signals
    SELECT
        unnest(ne.currencies) AS coin,
        ne.enricher_name,
        ne.enrichment_type,
        date_trunc('hour', ne.enriched_at) AS hour_bucket,
        1 AS signal_count,
        ne.confidence AS avg_confidence,
        ne.data->'event_type' AS event_types
    FROM news_enrichment ne
    WHERE ne.enriched_at > NOW() - INTERVAL '7 days'

    UNION ALL

    -- Social sentiment signals
    SELECT
        ss.asset AS coin,
        ss.source AS enricher_name,
        'sentiment' AS enrichment_type,
        date_trunc('hour', ss.timestamp) AS hour_bucket,
        1 AS signal_count,
        ss.magnitude AS avg_confidence,
        NULL AS event_types
    FROM sentiment_score ss
    WHERE ss.source IN ('reddit_llm', 'news_llm')
      AND ss.timestamp > NOW() - INTERVAL '7 days'
) combined
GROUP BY coin, enricher_name, enrichment_type, hour_bucket
"""


def refresh_materialized_views(session: Session) -> None:
    """Refresh all enrichment-related materialized views."""
    _refresh_views(session, ENRICHMENT_VIEWS)


def refresh_feature_store_views(session: Session) -> None:
    """Refresh all Feature Store materialized views in dependency order."""
    _refresh_views(session, FEATURE_STORE_VIEWS)


def refresh_all_views(session: Session) -> None:
    """Refresh all materialized views (enrichment + feature store)."""
    _refresh_views(session, ENRICHMENT_VIEWS + FEATURE_STORE_VIEWS)


def _refresh_views(session: Session, views: list[str]) -> None:
    """Refresh a list of materialized views concurrently."""
    for view_name in views:
        try:
            session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
            logger.info("Refreshed materialized view: %s", view_name)
        except Exception as e:
            logger.warning("Failed to refresh view %s: %s", view_name, e)

    try:
        session.commit()
    except Exception as e:
        logger.warning("Failed to commit materialized view refresh: %s", e)
