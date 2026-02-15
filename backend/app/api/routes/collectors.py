"""
API routes for data collectors.

Provides endpoints for:
- CRUD operations for Collector configuration
- Monitoring and manual triggering
"""

from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from app.api.deps import SessionDep, CurrentUser
from app.models import Message, Collector, CollectorCreate, CollectorUpdate, CollectorPublic, CollectorsPublic
from app.crud_collector import create_collector, get_collector, get_collectors, update_collector, delete_collector
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
    collectors = get_collectors(session=session, skip=skip, limit=limit)
    return CollectorsPublic(data=collectors, count=len(collectors))


@router.post("/", response_model=CollectorPublic)
def create_collector_endpoint(
    *,
    session: SessionDep,
    collector_in: CollectorCreate,
    current_user: CurrentUser,
) -> Any:
    """
    Create new collector.
    """
    collector = create_collector(session=session, collector_create=collector_in)
    
    # Register with orchestrator if active via side effect
    if collector.is_active:
        orchestrator = get_orchestrator()
        orchestrator.update_collector_from_model(collector)
        
    return collector


@router.get("/{collector_id}", response_model=CollectorPublic)
def read_collector(
    *,
    session: SessionDep,
    collector_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """
    Get collector by ID.
    """
    collector = get_collector(session=session, collector_id=collector_id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
    return collector


@router.put("/{collector_id}", response_model=CollectorPublic)
def update_collector_endpoint(
    *,
    session: SessionDep,
    collector_id: uuid.UUID,
    collector_in: CollectorUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a collector.
    """
    collector = get_collector(session=session, collector_id=collector_id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
    
    # Check if name changed to handle removal of old job name?
    # For now assuming name is immutable or we handle it by removing old and adding new?
    # CollectorUpdate model doesn't seem to have name? Let's assume name is identifying.
    # If name changes, we need to remove old job ID.
    old_name = collector.name
    
    collector = update_collector(session=session, db_collector=collector, collector_in=collector_in)
    
    orchestrator = get_orchestrator()
    
    if old_name != collector.name:
         orchestrator.remove_collector(old_name)

    if collector.is_active:
        orchestrator.update_collector_from_model(collector)
    else:
        orchestrator.remove_collector(collector.name)
        
    return collector


@router.delete("/{collector_id}", response_model=CollectorPublic)
def delete_collector_endpoint(
    *,
    session: SessionDep,
    collector_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """
    Delete a collector.
    """
    collector = get_collector(session=session, collector_id=collector_id)
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
        
    name_to_remove = collector.name
    collector = delete_collector(session=session, db_collector=collector)
    
    orchestrator = get_orchestrator()
    orchestrator.remove_collector(name_to_remove)
    
    return collector


@router.get("/health", response_model=dict[str, Any])
def get_collectors_health(
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """
    Get health status of all data collectors.
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_health_status()


@router.get("/name/{collector_name}/status", response_model=dict[str, Any])
def get_collector_status(
    collector_name: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """
    Get status of a specific collector (Orchestrator based).
    """
    orchestrator = get_orchestrator()
    
    try:
        return orchestrator.get_collector_status(collector_name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Collector '{collector_name}' not found"
        )


@router.post("/name/{collector_name}/trigger", response_model=Message)
async def trigger_collector(
    collector_name: str,
    current_user: CurrentUser,
) -> Message:
    """
    Manually trigger a collector to run immediately (Orchestrator based).
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
