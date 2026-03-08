"""
API routes for Phase 2.5 data collectors.

Provides endpoints for:
- Discovering plugins (strategies)
- Managing collector instances (CRUD)
- Monitoring status and triggering runs
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import Integer, cast, func, text
from sqlalchemy.sql import Select
from sqlmodel import Session, desc, select

from app.api.deps import SessionDep
from app.core.collectors.registry import CollectorRegistry
from app.models import Collector, CollectorRuns, Message
from app.services.scheduler import get_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()

# -----------------------------------------------------------------------------
# PLUGINS (Strategies)
# -----------------------------------------------------------------------------


@router.get("/plugins", response_model=list[dict[str, Any]])
def list_plugins() -> Any:
    """
    List all available collector plugins (strategies).
    """
    CollectorRegistry.discover_strategies()
    strategies = CollectorRegistry.list_strategies()

    plugins = []
    for name, strategy_cls in strategies.items():
        # Inspect the class to extract metadata
        try:
            # Instantiate the strategy to access properties and methods
            strategy_instance = strategy_cls()

            # Check if config_schema is callable
            schema = {}
            if hasattr(strategy_instance, "get_config_schema"):
                schema = strategy_instance.get_config_schema()
            elif hasattr(strategy_instance, "config_schema"):
                schema = strategy_instance.config_schema

            plugins.append(
                {
                    "id": name,
                    "name": strategy_instance.name,
                    "description": strategy_instance.description,
                    "version": "1.0.0",
                    "schema": schema,
                }
            )
        except Exception as e:
            logger.error(f"Error loading plugin {name}: {e}")
            continue

    return plugins


# -----------------------------------------------------------------------------
# INSTANCES (Configured Collectors)
# -----------------------------------------------------------------------------


@router.get("/", response_model=list[Collector])
def list_instances(session: SessionDep) -> Any:
    """
    List all configured collector instances.
    This merges database-stored instances with system-defined collectors from the Orchestrator.
    """
    # 1. Get user-defined instances from Database
    db_instances = session.exec(select(Collector)).all()

    # 2. Merge (orchestrator now fully DB-driven; status is persisted in DB)
    result = []

    # Add DB instances
    for db_inst in db_instances:
        result.append(db_inst)

    return result


@router.post("/", response_model=Collector)
def create_instance(session: SessionDep, instance_in: Collector) -> Any:
    """
    Create a new collector instance.
    """
    # Validate plugin exists (unless it's legacy coinspot_price)
    if instance_in.plugin_name != "coinspot_price":
        # Check registry
        if not CollectorRegistry.get_strategy(instance_in.plugin_name):
            # Try discovering again just in case
            CollectorRegistry.discover_strategies()
            if not CollectorRegistry.get_strategy(instance_in.plugin_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Plugin '{instance_in.plugin_name}' not found",
                )

    session.add(instance_in)
    session.commit()
    session.refresh(instance_in)

    # Refresh scheduler to pick up new job
    try:
        get_scheduler().refresh_jobs()
    except Exception as e:
        logger.error(f"Error refreshing scheduler: {e}")

    return instance_in


@router.get("/{id}", response_model=Collector)
def get_instance(id: int, session: SessionDep) -> Any:
    """
    Get a specific collector instance.
    """
    instance = session.get(Collector, id)
    if not instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")
    return instance


@router.put("/{id}", response_model=Collector)
def update_instance(id: int, instance_in: Collector, session: SessionDep) -> Any:
    """
    Update a collector instance.
    """
    db_instance = session.get(Collector, id)
    if not db_instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")

    # Update fields
    instance_data = instance_in.model_dump(exclude_unset=True)
    db_instance.sqlmodel_update(instance_data)

    session.add(db_instance)
    session.commit()
    session.refresh(db_instance)

    # Refresh scheduler
    try:
        get_scheduler().refresh_jobs()
    except Exception as e:
        logger.error(f"Error refreshing scheduler: {e}")

    return db_instance


@router.patch("/{id}", response_model=Collector)
def patch_instance(id: int, instance_in: Collector, session: SessionDep) -> Any:
    """
    Partially update a collector instance (Schedule, Enabled status, etc).
    """
    # PATCH is same as PUT with exclude_unset=True in model_dump
    return update_instance(id, instance_in, session)


@router.delete("/{id}", response_model=Message)
def delete_instance(id: int, session: SessionDep) -> Any:
    """
    Delete a collector instance.
    """
    instance = session.get(Collector, id)
    if not instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")

    session.delete(instance)
    session.commit()

    # Refresh scheduler
    try:
        get_scheduler().refresh_jobs()
    except Exception as e:
        logger.error(f"Error refreshing scheduler: {e}")

    return Message(message="Collector instance deleted successfully")


@router.post("/{id}/toggle", response_model=Collector)
def toggle_instance(id: int, session: SessionDep) -> Any:
    """
    Toggle the enabled status of a collector instance.
    """
    instance = session.get(Collector, id)
    if not instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")

    instance.is_enabled = not instance.is_enabled
    session.add(instance)
    session.commit()
    session.refresh(instance)

    # Refresh scheduler
    try:
        get_scheduler().refresh_jobs()
    except Exception as e:
        logger.error(f"Error refreshing scheduler: {e}")

    return instance


@router.post("/{id}/trigger", response_model=Message)
def trigger_instance(
    id: int, session: SessionDep, background_tasks: BackgroundTasks
) -> Any:
    """
    Trigger a manual run for a specific collector instance.
    """
    instance = session.get(Collector, id)
    if not instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")

    # Run in background via scheduler
    background_tasks.add_task(get_scheduler().run_now, id)

    return Message(message=f"Collector '{instance.name}' run initiated")


@router.post("/{id}/run", response_model=Message)
def run_instance(
    id: int, session: SessionDep, background_tasks: BackgroundTasks
) -> Any:
    """
    Alias for trigger: Run a collector immediately.
    """
    return trigger_instance(id, session, background_tasks)


@router.get("/{id}/sample-records", response_model=dict[str, Any])
def get_sample_records_endpoint(
    id: int,
    session: SessionDep,
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
) -> Any:
    """Get sample records from the data table associated with this collector."""
    from app.core.collectors.sample_records import get_sample_records

    collector = session.get(Collector, id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")

    result = get_sample_records(session, collector.plugin_name, limit=limit)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail=f"No data table mapping for plugin '{collector.plugin_name}'",
        )
    return result


@router.get("/{id}/stats", response_model=list[dict[str, Any]])
def get_stats(
    id: int,
    session: SessionDep,
    range: str = Query("1h", description="Time range for stats (e.g., 1h, 24h, 7d)"),
) -> list[dict[str, Any]]:
    """
    Get statistical data (records collected) for a collector over time.
    """
    collector = session.get(Collector, id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")

    # Parse range (basic)
    now = datetime.now(timezone.utc)
    delta = timedelta(hours=1)
    if range == "24h":
        delta = timedelta(hours=24)
    elif range == "7d":
        delta = timedelta(days=7)
    elif range == "30d":
        delta = timedelta(days=30)

    start_time = now - delta

    statement = (
        select(CollectorRuns)
        .where(CollectorRuns.collector_name == collector.name)
        .where(CollectorRuns.started_at >= start_time)
        .order_by(CollectorRuns.started_at)  # type: ignore[arg-type]
    )
    runs = session.exec(statement).all()

    return [
        {
            "timestamp": run.started_at,
            "count": run.records_collected or 0,
            "status": run.status,
        }
        for run in runs
    ]


# ============================================================================
# AGGREGATE STATS ENDPOINTS
# ============================================================================


def _get_ledger_for_collector(session: Session, collector_name: str) -> str | None:
    """
    Determine which ledger a collector belongs to by instantiating it.
    Returns one of: "glass", "human", "catalyst", "exchange"
    """
    # Get the collector instance to find its plugin_name
    statement = select(Collector).where(Collector.name == collector_name)
    collector = session.exec(statement).first()

    if not collector:
        return None

    # Get the strategy and check if it has a ledger property
    strategy_instance = CollectorRegistry.get_strategy_instance(collector.plugin_name)
    if strategy_instance and hasattr(strategy_instance, "ledger"):
        ledger = getattr(strategy_instance, "ledger", None)
        if isinstance(ledger, str):
            return ledger

    # Fallback: infer from plugin_name pattern
    plugin_name = collector.plugin_name.lower()
    if any(x in plugin_name for x in ["defillama", "nansen", "chain_walker"]):
        return "glass"
    elif any(x in plugin_name for x in ["cryptopanic", "newscatcher", "reddit", "rss"]):
        return "human"
    elif any(x in plugin_name for x in ["sec", "coinspot_announce"]):
        return "catalyst"
    elif any(x in plugin_name for x in ["coinspot", "exchange"]):
        return "exchange"

    return None


@router.get("/stats/volume", response_model=list[dict[str, Any]])
def get_volume_stats(
    session: SessionDep,
    range: str = Query("24h", description="Time range for stats (1h, 24h, 7d)"),
) -> list[dict[str, Any]]:
    """
    Get records collected grouped by ledger over time.

    Response format: [{time: "HH:MM", Glass: N, Human: N, Catalyst: N, Exchange: N}]
    Supports time range parameter (1h, 24h, 7d).
    """
    # Parse range
    now = datetime.now(timezone.utc)
    delta = timedelta(hours=1)
    if range == "24h":
        delta = timedelta(hours=24)
    elif range == "7d":
        delta = timedelta(days=7)

    start_time = now - delta

    # Query all runs in the time range
    statement = (
        select(CollectorRuns)
        .where(CollectorRuns.started_at >= start_time)
        .order_by(CollectorRuns.started_at)  # type: ignore[arg-type]
    )
    runs = session.exec(statement).all()

    # Group by time (hourly buckets) and ledger
    time_buckets: dict[str, dict[str, Any]] = {}

    for run in runs:
        # Create hourly bucket key (HH:MM format)
        time_key = run.started_at.strftime("%H:%M")

        if time_key not in time_buckets:
            time_buckets[time_key] = {
                "time": time_key,
                "Glass": 0,
                "Human": 0,
                "Catalyst": 0,
                "Exchange": 0,
            }

        # Determine ledger for this collector
        ledger = _get_ledger_for_collector(session, run.collector_name)
        if not ledger:
            continue

        # Map ledger name to capitalized format
        ledger_display = ledger.capitalize()
        if ledger_display in time_buckets[time_key]:
            count = time_buckets[time_key][ledger_display]
            if isinstance(count, int):
                time_buckets[time_key][ledger_display] = count + (
                    run.records_collected or 0
                )

    # Return as sorted list
    return sorted(time_buckets.values(), key=lambda x: str(x.get("time", "")))


@router.get("/stats/activity", response_model=list[dict[str, Any]])
def get_activity_stats(session: SessionDep) -> list[dict[str, Any]]:
    """
    Get recent collector runs across all collectors.

    Returns last 50 runs ordered by started_at DESC.
    Response: [{id, timestamp, collector, status, items, duration}]
    """
    statement = select(CollectorRuns).order_by(desc(CollectorRuns.started_at)).limit(50)
    runs = session.exec(statement).all()

    result: list[dict[str, Any]] = []
    for run in runs:
        duration_seconds = 0
        if run.completed_at and run.started_at:
            duration_seconds = int((run.completed_at - run.started_at).total_seconds())

        result.append(
            {
                "id": run.id,
                "timestamp": run.started_at,
                "collector_name": run.collector_name,
                "status": run.status,
                "records_collected": run.records_collected or 0,
                "duration_seconds": duration_seconds,
            }
        )

    return result


@router.get("/stats/summary", response_model=list[dict[str, Any]])
def get_summary_stats(session: SessionDep) -> list[dict[str, Any]]:
    """
    Get aggregate stats per collector.

    Response: [{collector_name, total_runs, success_count, warning_count, error_count,
                total_records, avg_duration_seconds, last_success_at, error_rate}]
    """
    # Get all unique collectors
    statement = select(CollectorRuns.collector_name).distinct()
    collector_names = session.exec(statement).all()

    summary: list[dict[str, Any]] = []

    for collector_name in collector_names:
        # Get all runs for this collector
        runs_statement = (
            select(CollectorRuns)
            .where(CollectorRuns.collector_name == collector_name)
            .order_by(CollectorRuns.started_at)  # type: ignore[arg-type]
        )
        runs = session.exec(runs_statement).all()

        if not runs:
            continue

        total_runs = len(runs)
        success_count = sum(1 for r in runs if r.status == "success")
        error_count = sum(1 for r in runs if r.status == "failed")
        warning_count = sum(1 for r in runs if r.status == "warning")
        total_records = sum(r.records_collected or 0 for r in runs)

        # Calculate average duration
        durations: list[float] = []
        for run in runs:
            if run.completed_at and run.started_at:
                duration = (run.completed_at - run.started_at).total_seconds()
                durations.append(duration)
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        # Find last successful run
        last_success: datetime | None = None
        for run in reversed(runs):
            if run.status == "success":
                last_success = run.started_at
                break

        # Calculate error rate
        error_rate = (error_count / total_runs * 100) if total_runs > 0 else 0.0

        summary.append(
            {
                "collector_name": collector_name,
                "total_runs": total_runs,
                "success_count": success_count,
                "warning_count": warning_count,
                "error_count": error_count,
                "total_records": total_records,
                "avg_duration_seconds": round(avg_duration, 2),
                "last_success_at": last_success,
                "error_rate": round(error_rate, 1),
            }
        )

    return summary


@router.get("/stats/chart-data", response_model=list[dict[str, Any]])
def get_chart_data(
    session: SessionDep,
    collector_name: str | None = Query(None, description="Filter by collector name"),
    hours: int = Query(
        168, ge=1, le=2160, description="Hours to aggregate (default 168 = 7 days)"
    ),
) -> list[dict[str, Any]]:
    """
    Get 12-hour aggregated chart data for collector performance.

    Response: [{bucket: "2026-03-07T00:00:00Z", records: N, runs: M, errors: K}, ...]
    Default range: 7 days (168 hours = 14 buckets of 12 hours each).
    """
    # Parse hours into date range
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    # Build query with 12-hour bucketing
    base_select: Select[Any] = select(
        func.date_trunc(text("'12 hours'"), CollectorRuns.started_at).label("bucket"),
        func.sum(CollectorRuns.records_collected).label("records"),
        func.count(1).label("runs"),
        func.sum(cast(CollectorRuns.status == "failed", Integer)).label("errors"),
    )

    if collector_name:
        runs_query = (
            base_select.where(CollectorRuns.collector_name == collector_name)  # type: ignore[arg-type]
            .where(CollectorRuns.started_at >= start_time)  # type: ignore[arg-type]
            .group_by(text("bucket"))
            .order_by(text("bucket"))
        )
    else:
        runs_query = (
            base_select.where(CollectorRuns.started_at >= start_time)  # type: ignore[arg-type]
            .group_by(text("bucket"))
            .order_by(text("bucket"))
        )

    results = session.exec(runs_query).all()  # type: ignore[call-overload]

    return [
        {
            "bucket": bucket.isoformat() if bucket else None,
            "records": int(records or 0),
            "runs": int(runs or 0),
            "errors": int(errors or 0),
        }
        for bucket, records, runs, errors in results
    ]
