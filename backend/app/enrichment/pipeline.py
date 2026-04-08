"""Enrichment pipeline that orchestrates enrichers and stores results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.collectors.strategies.keyword_taxonomy import aggregate_sentiment
from app.enrichment.base import IEnricher
from app.enrichment.views import refresh_materialized_views
from app.models import EnrichmentRun, NewsEnrichment, NewsItem

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """Runs enrichers on items and stores results in database."""

    def __init__(self, enrichers: list[IEnricher]):
        """Initialize with a list of enrichers."""
        self.enrichers = enrichers

    async def run(
        self, items: list[Any], session: Session, trigger: str = "auto"
    ) -> EnrichmentRun:
        """
        Run all enrichers on items and store results.

        Args:
            items: News items to enrich
            session: Database session for storing results
            trigger: "auto" or "manual" to track run source

        Returns:
            EnrichmentRun record with statistics
        """
        started_at = datetime.now(timezone.utc)
        total_items = len(items)
        items_enriched = 0
        items_skipped = 0
        items_failed = 0
        error_message = None

        try:
            # Process each item through all enrichers
            for item in items:
                try:
                    # Check which enrichers can process this item
                    usable_enrichers = [e for e in self.enrichers if e.can_enrich(item)]
                    if not usable_enrichers:
                        items_skipped += 1
                        continue

                    # Run all usable enrichers
                    enrichment_created = False
                    for enricher in usable_enrichers:
                        try:
                            results = await enricher.enrich(item)
                            if results:
                                self._store_results(
                                    item, enricher.name, results, session
                                )
                                enrichment_created = True
                        except Exception as e:
                            logger.error(f"Enricher {enricher.name} failed: {e}")

                    if enrichment_created:
                        items_enriched += 1
                    else:
                        items_skipped += 1

                except Exception as e:
                    item_id = getattr(item, "link", None) or getattr(item, "id", "?")
                    logger.error(f"Error enriching item {item_id}: {e}")
                    items_failed += 1

            # Commit changes
            session.commit()
            logger.info(
                f"Enrichment pipeline completed: "
                f"{items_enriched} enriched, {items_skipped} skipped, {items_failed} failed"
            )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            error_message = str(e)
            items_failed = total_items

        # Record the run
        completed_at = datetime.now(timezone.utc)
        run = EnrichmentRun(
            enricher_name="pipeline",
            items_processed=total_items,
            items_enriched=items_enriched,
            items_skipped=items_skipped,
            items_failed=items_failed,
            started_at=started_at,
            completed_at=completed_at,
            status="completed" if error_message is None else "failed",
            error_message=error_message,
            trigger=trigger,
        )
        session.add(run)
        session.commit()

        # Refresh materialized views
        try:
            refresh_materialized_views(session)
        except Exception as e:
            logger.warning(f"Failed to refresh materialized views: {e}")

        return run

    def _store_results(
        self,
        item: Any,
        enricher_name: str,
        results: list[Any],
        session: Session,
    ) -> None:
        """
        Store enrichment results in database.

        For NewsItem: stores in NewsEnrichment table.
        For other items: enrichers handle their own storage (e.g. SocialSentimentEnricher).
        """
        # Only store in NewsEnrichment for NewsItem-linked results
        if not isinstance(item, NewsItem):
            return

        for result in results:
            try:
                # Use savepoint to allow per-result rollback on unique constraint violation
                savepoint = session.begin_nested()
                try:
                    enrichment = NewsEnrichment(
                        news_item_link=item.link,
                        enricher_name=result.enricher_name,
                        enrichment_type=result.enrichment_type,
                        data=result.data,
                        currencies=result.currencies,
                        confidence=result.confidence,
                    )
                    session.add(enrichment)
                    session.flush()
                    savepoint.commit()
                except Exception as e:
                    savepoint.rollback()
                    logger.warning(f"Failed to store enrichment: {e}")
            except Exception as e:
                logger.warning(f"Failed to store enrichment: {e}")

        # Update item sentiment score from keyword results if this is a keyword enricher
        if enricher_name == "keyword":
            self._update_sentiment_from_keywords(item, results, session)

    def _update_sentiment_from_keywords(
        self, item: NewsItem, results: list[Any], session: Session
    ) -> None:
        """Update item sentiment score from keyword enrichment results."""
        all_keywords = []

        for result in results:
            data = result.data
            all_keywords.append(
                {
                    "keyword": data["keyword"],
                    "category": data["category"],
                    "direction": data["direction"],
                    "impact": data["impact"],
                }
            )

        # Update item sentiment score from aggregated keywords
        if all_keywords:
            # Import KeywordEntry to use aggregate_sentiment correctly
            from app.collectors.strategies.keyword_taxonomy import KeywordEntry

            # Convert dicts to KeywordEntry-like objects
            keyword_entries = [
                KeywordEntry(
                    keyword=kw["keyword"],
                    pattern=__import__("re").compile(kw["keyword"]),
                    category=kw["category"],
                    direction=kw["direction"],
                    impact=kw["impact"],
                    temporal_signal="",
                )
                for kw in all_keywords
            ]
            sentiment_score, sentiment_label = aggregate_sentiment(keyword_entries)
            if item.sentiment_score is None:  # Don't override existing sentiment
                item.sentiment_score = sentiment_score
                item.sentiment_label = sentiment_label
