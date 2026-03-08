"""Materialized views for enrichment data."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)


def refresh_materialized_views(session: Session) -> None:
    """Refresh all enrichment-related materialized views."""
    views_to_refresh = [
        "mv_coin_sentiment_24h",
        "mv_signal_summary",
    ]

    for view_name in views_to_refresh:
        try:
            session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
            logger.info(f"Refreshed materialized view: {view_name}")
        except Exception as e:
            logger.warning(f"Failed to refresh view {view_name}: {e}")

    try:
        session.commit()
    except Exception as e:
        logger.warning(f"Failed to commit materialized view refresh: {e}")
