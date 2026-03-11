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
