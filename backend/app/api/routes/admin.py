from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import User
from app.services.trading.safety import TradingSafetyManager

router = APIRouter()

@router.post("/emergency-stop/activate")
async def activate_emergency_stop(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Activate the emergency stop (Kill Switch).
    Halt all trading activities immediately.
    """
    safety = TradingSafetyManager(session)
    try:
        await safety.activate_emergency_stop(actor_id=current_user.id)
        return {"message": "Emergency stop activated", "status": "active"}
    finally:
        await safety.disconnect()

@router.post("/emergency-stop/clear")
async def clear_emergency_stop(
    session: SessionDep,
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Clear the emergency stop.
    Resume trading activities.
    """
    safety = TradingSafetyManager(session)
    try:
        await safety.clear_emergency_stop(actor_id=current_user.id)
        return {"message": "Emergency stop cleared", "status": "inactive"}
    finally:
        await safety.disconnect()

@router.get("/emergency-stop/status", dependencies=[Depends(get_current_active_superuser)])
async def get_emergency_stop_status(session: SessionDep) -> Any:
    """
    Check the current status of the emergency stop.
    """
    safety = TradingSafetyManager(session)
    try:
        status = await safety.is_emergency_stopped()
        return {"status": "active" if status else "inactive"}
    finally:
        await safety.disconnect()
