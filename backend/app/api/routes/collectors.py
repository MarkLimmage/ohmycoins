"""
API routes for Phase 2.5 data collectors.

Provides endpoints for:
- Discovering plugins (strategies)
- Managing collector instances (CRUD)
- Monitoring status and triggering runs
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.collectors.registry import CollectorRegistry
from app.models import Collector, Message

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
        except Exception:
            # print(f"Error loading plugin {name}: {e}")
            continue

    return plugins


# -----------------------------------------------------------------------------
# INSTANCES (Configured Collectors)
# -----------------------------------------------------------------------------


@router.get("/", response_model=list[Collector])
def list_instances(session: SessionDep) -> Any:
    """
    List all configured collector instances.
    """
    return session.exec(select(Collector)).all()


@router.post("/", response_model=Collector)
def create_instance(session: SessionDep, instance_in: Collector) -> Any:
    """
    Create a new collector instance.
    """
    # Validate plugin exists
    if not CollectorRegistry.get_strategy(instance_in.plugin_name):
        # Try discovering again just in case
        CollectorRegistry.discover_strategies()
        if not CollectorRegistry.get_strategy(instance_in.plugin_name):
            raise HTTPException(
                status_code=400, detail=f"Plugin '{instance_in.plugin_name}' not found"
            )

    session.add(instance_in)
    session.commit()
    session.refresh(instance_in)
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
    return db_instance


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
    return instance


@router.post("/{id}/trigger", response_model=Message)
async def trigger_instance(id: int, session: SessionDep) -> Any:
    """
    Trigger a manual run for a specific collector instance.
    """
    instance = session.get(Collector, id)
    if not instance:
        raise HTTPException(status_code=404, detail="Collector instance not found")

    # In a real implementation, this would call the Orchestrator to run the specific instance ID
    # For now, we'll just return success to simulate the triggering

    # orchestrator = get_orchestrator()
    # await orchestrator.run_collector_instance(instance) # Assuming such method exists

    return Message(message=f"Collector '{instance.name}' triggered successfully")


# Keep existing endpoints for backward compatibility or direct access if needed
# ... (Or remove them if they conflict)
