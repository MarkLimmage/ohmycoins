from typing import Annotated

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status, WebSocketException
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.api.deps import get_db, get_current_active_superuser
from app.models import TokenPayload, User
from app.services.websocket_manager import manager
from pydantic import BaseModel

router = APIRouter()

class BroadcastMessage(BaseModel):
    channel: str
    message: dict

@router.post("/broadcast", include_in_schema=False)
async def broadcast_message(
    body: BroadcastMessage,
    user: Annotated[User, Depends(get_current_active_superuser)]
):
    """
    Internal endpoint to test WebSocket broadcasts.
    """
    await manager.broadcast_json(body.message, body.channel)
    return {"status": "ok"}

async def get_websocket_user(
    token: Annotated[str, Query()],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Authenticate WebSocket connection using JWT token in query parameter.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        
    user = session.get(User, token_data.sub)
    if not user:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        
    if not user.is_active:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user")
        
    return user

@router.websocket("/catalyst/live")
async def websocket_catalyst_live(
    websocket: WebSocket,
    user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for Catalyst Ledger (events).
    """
    channel_id = "catalyst"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            # Wait for messages (keep connection open)
            # We can handle client messages here if needed (e.g. heartbeat)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)

@router.websocket("/glass/live")
async def websocket_glass_live(
    websocket: WebSocket,
    user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for Glass Ledger (TVL/Fees).
    """
    channel_id = "glass"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)

@router.websocket("/human/live")
async def websocket_human_live(
    websocket: WebSocket,
    user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for Human Ledger (Sentiment).
    """
    channel_id = "human"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)

@router.websocket("/exchange/live")
async def websocket_exchange_live(
    websocket: WebSocket,
    user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for Exchange Ledger (Prices).
    """
    channel_id = "exchange"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)

@router.websocket("/trading/live")
async def websocket_trading_live(
    websocket: WebSocket,
    user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for Trading updates (Orders, Positions).
    Channel ID is unique to the user: 'trading_{user_id}'
    """
    channel_id = f"trading_{user.id}"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)
