"""Enrichment pipeline API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func
from sqlmodel import select

from app.api.deps import SessionDep
from app.enrichment.keyword_enricher import KeywordEnricher
from app.enrichment.llm_enricher import LLMEnricher
from app.enrichment.pipeline import EnrichmentPipeline
from app.enrichment.providers.gemini import GeminiSentimentProvider
from app.models import EnrichmentRun, NewsItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run")
async def trigger_enrichment(
    session: SessionDep,
    enricher: str = Query(
        "all", description="Enricher to use: 'all', 'keyword', 'llm'"
    ),
    limit: int = Query(100, description="Max items to enrich"),
) -> dict[str, int]:
    """
    Trigger batch enrichment on un-enriched news items.

    Returns number of items queued for enrichment.
    """
    # Find items without enrichment (no matching NewsKeywordMatch records)
    statement = select(NewsItem).limit(limit)
    items_result = session.exec(statement).all()
    items: list[NewsItem] = items_result  # type: ignore[assignment]

    if not items:
        return {"enrichment_run_id": 0, "items_queued": 0}

    # Build enricher list
    enrichers: list[Any] = []
    if enricher in ["all", "keyword"]:
        enrichers.append(KeywordEnricher())
    if enricher in ["all", "llm"]:
        try:
            provider = GeminiSentimentProvider(session)
            enrichers.append(LLMEnricher(provider))
        except ValueError as e:
            logger.warning(f"Skipping LLM enricher: {e}")

    if not enrichers:
        raise HTTPException(
            status_code=400, detail="No enrichers available for the requested type"
        )

    # Run pipeline
    pipeline = EnrichmentPipeline(enrichers)
    run = await pipeline.run(items, session, trigger="manual")

    return {
        "enrichment_run_id": run.id or 0,
        "items_queued": run.items_processed,
    }


@router.get("/stats")
def get_enrichment_stats(session: SessionDep) -> dict[str, Any]:
    """
    Get enrichment statistics.

    Returns overall coverage and per-enricher stats.
    """
    from app.models import NewsKeywordMatch

    # Total items
    total_items_statement = select(func.count()).select_from(NewsItem)
    total_items_result = session.exec(total_items_statement).one()
    total_items = total_items_result if isinstance(total_items_result, int) else 0

    # Enriched items (have at least one NewsKeywordMatch)
    enriched_items_statement = select(
        func.count(func.distinct(NewsKeywordMatch.news_item_link))
    )
    enriched_items_result = session.exec(enriched_items_statement).one()
    enriched_items = (
        enriched_items_result if isinstance(enriched_items_result, int) else 0
    )

    unenriched_items = total_items - enriched_items
    coverage_pct = (enriched_items / total_items * 100) if total_items > 0 else 0.0

    # Per-enricher stats - get list of all enrichment runs
    enricher_stats: list[dict[str, Any]] = []
    all_runs_statement = select(EnrichmentRun)
    all_runs_result = session.exec(all_runs_statement).all()
    all_runs: list[EnrichmentRun] = all_runs_result  # type: ignore[assignment]

    # Group by enricher name
    from collections import defaultdict

    enricher_data: dict[str, list[EnrichmentRun]] = defaultdict(list)
    for run in all_runs:
        enricher_data[run.enricher_name].append(run)

    for enricher_name, runs in enricher_data.items():
        total_runs = len(runs)
        items_enriched = sum(r.items_enriched for r in runs)
        last_run = max((r.completed_at for r in runs if r.completed_at), default=None)

        enricher_stats.append(
            {
                "name": enricher_name,
                "total_runs": total_runs,
                "items_enriched": items_enriched,
                "last_run": last_run,
                "avg_duration_secs": 0.0,
            }
        )

    return {
        "total_items": total_items,
        "enriched_items": enriched_items,
        "unenriched_items": unenriched_items,
        "coverage_pct": round(coverage_pct, 2),
        "by_enricher": enricher_stats,
    }


@router.get("/runs")
def get_enrichment_runs(
    session: SessionDep,
    limit: int = Query(50, description="Max recent runs to return"),
) -> dict[str, Any]:
    """Get recent enrichment runs."""
    # Get all runs and sort by completed_at in Python
    statement = select(EnrichmentRun).limit(limit * 2)
    runs_result = session.exec(statement).all()
    runs_all: list[EnrichmentRun] = runs_result  # type: ignore[assignment]

    # Sort by completed_at, with None values last
    runs = sorted(
        runs_all,
        key=lambda r: (r.completed_at is None, r.completed_at),
        reverse=True,
    )[:limit]

    return {
        "runs": [
            {
                "id": r.id,
                "enricher_name": r.enricher_name,
                "items_processed": r.items_processed,
                "items_enriched": r.items_enriched,
                "items_skipped": r.items_skipped,
                "items_failed": r.items_failed,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "status": r.status,
                "error_message": r.error_message,
                "trigger": r.trigger,
            }
            for r in runs
        ],
        "count": len(runs),
    }
