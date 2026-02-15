"""
API routes for Phase 2.5 data collectors.

Provides endpoints for:
- Collector health monitoring
- Manual trigger of collectors
- Collection status and metrics
- CRUD operations for dynamic collectors
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import SessionDep, CurrentUser
from app.models import (
    Collector,
    CollectorCreate,
    CollectorPublic,
    CollectorsPublic,
    CollectorUpdate,
    Message,
)
from app.services.collectors.orchestrator import get_orchestrator

router = APIRouter()


@router.get("/", response_model=CollectorsPublic)
def read_collectors(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve collectors.
    """
    count_statement = select(func.count()).select_from(Collector)
    count = session.exec(count_statement).one()
    statement = select(Collector).offset(skip).limit(limit)
    collectors = session.exec(statement).all()
    return CollectorsPublic(data=collectors, count=count)


@router.get("/{id}", response_model=CollectorPublic)
def read_collector(
    id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get collector by ID.
    """
    collector = session.get(Collector, id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
    return collector


@router.post("/", response_model=CollectorPublic)
def create_collector(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    collector_in: CollectorCreate,
) -> Any:
    """
    Create new collector.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    collector = Collector.model_validate(collector_in)
    session.add(collector)
    session.commit()
    session.refresh(collector)
    return collector


@router.put("/{id}", response_model=CollectorPublic)
def update_collector(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    collector_in: CollectorUpdate,
) -> Any:
    """
    Update a collector.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    collector = session.get(Collector, id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
    
    update_data = collector_in.model_dump(exclude_unset=True)
    collector.sqlmodel_update(update_data)
    session.add(collector)
    session.commit()
    session.refresh(collector)
    return collector


@router.delete("/{id}", response_model=Message)
def delete_collector(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Delete a collector.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    collector = session.get(Collector, id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
    
    session.delete(collector)
    session.commit()
    return Message(message="Collector deleted successfully")


@router.get("/health", response_model=dict[str, Any])
def get_collectors_health(current_user: CurrentUser) -> dict[str, Any]:
    """
    Get health status of all data collectors.
    
    Returns:
        Dictionary containing:
        - orchestrator_status: running or stopped
        - collector_count: number of registered collectors
        - collectors: list of collector statuses
        - timestamp: current timestamp
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_health_status()


@router.get("/name/{collector_name}/status", response_model=dict[str, Any])
def get_collector_status(collector_name: str, current_user: CurrentUser) -> dict[str, Any]:
    """
    Get status of a specific collector.
    
    Args:
        collector_name: Name of the collector (e.g., "defillama_api")
    
    Returns:
        Dictionary containing collector status and metrics
    
    Raises:
        HTTPException: If collector not found
    """
    orchestrator = get_orchestrator()
    # TODO: check if collector exists in DB too?
    return orchestrator.get_collector_status(collector_name)

@router.post("/{id}/run", response_model=Message)
def run_collector(
    id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Trigger a collector run manually.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")

    collector = session.get(Collector, id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
    
    # Logic to trigger run via orchestrator
    orchestrator = get_orchestrator()
    # Assuming orchestrator has a method to run by name or we register it dynamically
    # For now simply attempt to run if registered
    success = orchestrator.force_run_collector_by_name(collector.name) # We need to implement this
    if not success:
         # If not registered, maybe register and run? 
         # This implies dynamic loading logic which is part of "Refactor collector_engine"
         return Message(message=f"Collector {collector.name} scheduled for run (if active)")

    return Message(message=f"Triggered collector {collector.name}")

    try:
        return orchestrator.get_collector_status(collector_name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Collector '{collector_name}' not found"
        )


@router.post("/{collector_name}/trigger", response_model=Message)
async def trigger_collector(collector_name: str) -> Message:
    """
    Manually trigger a collector to run immediately.
    
    Args:
        collector_name: Name of the collector to trigger
    
    Returns:
        Success or error message
    
    Raises:
        HTTPException: If collector not found or execution fails
    """
    orchestrator = get_orchestrator()
    
    try:
        success = await orchestrator.trigger_manual(collector_name)
        
        if success:
            return Message(message=f"Collector '{collector_name}' executed successfully")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Collector '{collector_name}' execution failed. Check logs for details."
            )
            
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Collector '{collector_name}' not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger collector: {str(e)}"
        )
