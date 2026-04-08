"""Enrichment scheduler for processing unenriched social sentiment rows."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import and_
from sqlmodel import Session, select

from app.enrichment.pipeline import EnrichmentPipeline
from app.enrichment.providers.gemini import GeminiSentimentProvider
from app.enrichment.social_enricher import SocialSentimentEnricher
from app.models import EnrichmentRecord, EnrichmentRun, SocialSentiment

logger = logging.getLogger(__name__)

# Maximum items to process per scheduler run
BATCH_LIMIT = 100


async def run_social_enrichment(session: Session) -> EnrichmentRun:
    """
    Enrich SocialSentiment rows that haven't been processed yet.

    Queries for rows with no matching EnrichmentRecord, processes them
    through the SocialSentimentEnricher, and stores provenance records.

    Schedule: */30 * * * * (every 30 min) — wired by Supervisor in Phase 3.
    """
    # Find unenriched SocialSentiment rows via NOT EXISTS subquery
    enriched_subquery = (
        select(EnrichmentRecord.source_id)
        .where(
            and_(
                EnrichmentRecord.source_table == "social_sentiment",
                EnrichmentRecord.enricher_name == "social_llm_sentiment",
                EnrichmentRecord.enrichment_type == "sentiment",
            )
        )
    )

    statement = (
        select(SocialSentiment)
        .where(SocialSentiment.id.notin_(enriched_subquery))  # type: ignore[union-attr]
        .order_by(SocialSentiment.collected_at.desc())  # type: ignore[union-attr]
        .limit(BATCH_LIMIT)
    )

    items = list(session.exec(statement).all())
    if not items:
        logger.info("No unenriched social sentiment items found.")
        return _empty_run(session)

    logger.info(f"Found {len(items)} unenriched social sentiment items.")

    # Build enrichment pipeline
    provider = GeminiSentimentProvider(session=session)
    enricher = SocialSentimentEnricher(provider=provider, session=session)
    pipeline = EnrichmentPipeline(enrichers=[enricher])

    # Run the generalized pipeline
    run = await pipeline.run(items=items, session=session, trigger="auto")

    # Store EnrichmentRecord entries for processed items
    _store_enrichment_records(items, enricher, session)

    return run


def _store_enrichment_records(
    items: list[SocialSentiment],
    enricher: SocialSentimentEnricher,
    session: Session,
) -> None:
    """Write EnrichmentRecord entries for all processed items."""
    for item in items:
        try:
            savepoint = session.begin_nested()
            try:
                record = EnrichmentRecord(
                    source_table="social_sentiment",
                    source_id=item.id,  # type: ignore[arg-type]
                    enricher_name=enricher.name,
                    enrichment_type="sentiment",
                    data={"status": "processed"},
                    enriched_at=datetime.now(timezone.utc),
                )
                session.add(record)
                session.flush()
                savepoint.commit()
            except Exception as e:
                savepoint.rollback()
                logger.warning(
                    f"Failed to store EnrichmentRecord for id={item.id}: {e}"
                )
        except Exception as e:
            logger.warning(f"Savepoint error for id={item.id}: {e}")

    try:
        session.commit()
    except Exception as e:
        logger.error(f"Failed to commit EnrichmentRecords: {e}")


def _empty_run(session: Session) -> EnrichmentRun:
    """Create and persist an empty enrichment run record."""
    now = datetime.now(timezone.utc)
    run = EnrichmentRun(
        enricher_name="social_pipeline",
        items_processed=0,
        items_enriched=0,
        items_skipped=0,
        items_failed=0,
        started_at=now,
        completed_at=now,
        status="completed",
        error_message=None,
        trigger="auto",
    )
    session.add(run)
    session.commit()
    return run
