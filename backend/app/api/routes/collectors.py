"""
API routes for Phase 2.5 data collectors.

Provides endpoints for:
- Collector health monitoring
- Manual trigger of collectors
- Collection status and metrics
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.models import Message
from app.services.collectors.orchestrator import get_orchestrator

router = APIRouter()


@router.get("/health", response_model=dict[str, Any])
def get_collectors_health() -> dict[str, Any]:
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


@router.get("/{collector_name}/status", response_model=dict[str, Any])
def get_collector_status(collector_name: str) -> dict[str, Any]:
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
