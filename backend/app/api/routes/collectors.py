"""
API routes for Phase 2.5 data collectors.

Provides endpoints for:
- Discovering plugins (strategies)
- Managing collector instances (CRUD)
- Monitoring status and triggering runs
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from sqlmodel import Session, select, func

from app.api.deps import SessionDep
from app.core.collectors.registry import CollectorRegistry
from app.models import Collector, Message, CollectorRuns
from app.services.scheduler import get_scheduler

router = APIRouter()

# -----------------------------------------------------------------------------
# PLUGINS (Strategies)
# -----------------------------------------------------------------------------

@router.get("/plugins", response_model=List[dict])
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
            
            plugins.append({
                "id": name,
                "name": strategy_instance.name, 
                "description": strategy_instance.description,
                "version": "1.0.0", 
                "schema": schema
            })
        except Exception as e:
            print(f"Error loading plugin {name}: {e}")
            continue
            
    return plugins

# -----------------------------------------------------------------------------
# INSTANCES (Configured Collectors)
# -----------------------------------------------------------------------------

@router.get("/", response_model=List[Collector])
def list_instances(session: SessionDep) -> Any:
    """
    List all configured collector instances.
    This merges database-stored instances with system-defined collectors from the Orchestrator.
    """
    # 1. Get user-defined instances from Database
    db_instances = session.exec(select(Collector)).all()
    
    # 2. Get system-defined instances from Orchestrator (memory)
    # Since we are moving to fully DB-managed collectors, the orchestrator primarily
    # reflects what's in the DB. However, checking orchestrator is still useful for *status*
    from app.services.collectors.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    # system_collectors = orchestrator.collectors # Deprecated: Orchestrator should now only run DB-instances
    
    # 3. Merge them
    result = []
    
    # Add DB instances first
    for db_inst in db_instances:
        # Check if it's active in orchestrator?
        status = "idle" 
        # Ideally we query orchestrator for running status of this ID
        # Since API and Orchestrator are separate processes now (in Prod), 
        # we can't check orchestrator memory directly unless we use Redis/DB for status sync.
        # For now, we rely on the DB status field updated by the Orchestrator?
        # Or just return "unknown" / rely on the static field
        
        # db_inst.status is persisted in DB by the runner?
        result.append(db_inst)

    return result

@router.post("/", response_model=Collector)
def create_instance(
    session: SessionDep, 
    instance_in: Collector
) -> Any:
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
                 raise HTTPException(status_code=400, detail=f"Plugin '{instance_in.plugin_name}' not found")

    session.add(instance_in)
    session.commit()
    session.refresh(instance_in)
    
    # Refresh scheduler to pick up new job
    try:
        get_scheduler().refresh_jobs()
    except Exception as e:
        print(f"Error refreshing scheduler: {e}")

    return instance_in

@router.get("/{id}", response_model=Collector)
def get_instance(
    id: int,
    session: SessionDep
) -> Any:
    """
    Get a specific collector instance.
    """
    instance = session.get(Collector, id)
    if not instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")
    return instance

@router.put("/{id}", response_model=Collector)
def update_instance(
    id: int,
    instance_in: Collector,
    session: SessionDep
) -> Any:
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
        print(f"Error refreshing scheduler: {e}")

    return db_instance

@router.patch("/{id}", response_model=Collector)
def patch_instance(
    id: int,
    instance_in: Collector,
    session: SessionDep
) -> Any:
    """
    Partially update a collector instance (Schedule, Enabled status, etc).
    """
    # PATCH is same as PUT with exclude_unset=True in model_dump
    return update_instance(id, instance_in, session)

@router.delete("/{id}", response_model=Message)
def delete_instance(
    id: int,
    session: SessionDep
) -> Any:
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
        print(f"Error refreshing scheduler: {e}")

    return Message(message="Collector instance deleted successfully")

@router.post("/{id}/toggle", response_model=Collector)
def toggle_instance(
    id: int,
    session: SessionDep
) -> Any:
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
        print(f"Error refreshing scheduler: {e}")

    return instance

@router.post("/{id}/trigger", response_model=Message)
def trigger_instance(
    id: int,
    session: SessionDep,
    background_tasks: BackgroundTasks
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
    id: int,
    session: SessionDep,
    background_tasks: BackgroundTasks
) -> Any:
    """
    Alias for trigger: Run a collector immediately.
    """
    return trigger_instance(id, session, background_tasks)

@router.get("/{id}/stats", response_model=List[dict])
def get_stats(
    id: int,
    session: SessionDep,
    range: str = Query("1h", description="Time range for stats (e.g., 1h, 24h, 7d)")
) -> Any:
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
        .order_by(CollectorRuns.started_at)
    )
    runs = session.exec(statement).all()
    
    return [
        {
            "timestamp": run.started_at,
            "count": run.records_collected or 0,
            "status": run.status
        }
        for run in runs
    ]

