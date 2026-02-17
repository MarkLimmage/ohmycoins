# mypy: ignore-errors
import asyncio
import json
import random
from datetime import datetime
from typing import Annotated

import jwt
from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, ValidationError
from sqlmodel import Session

from app.api.deps import get_current_active_superuser, get_db
from app.core import security
from app.core.config import settings
from app.models import TokenPayload, User
from app.services.websocket_manager import manager

router = APIRouter()

class BroadcastMessage(BaseModel):
    channel: str
    message: dict

@router.post("/broadcast", include_in_schema=False)
async def broadcast_message(
    body: BroadcastMessage,
    _user: Annotated[User, Depends(get_current_active_superuser)]
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
    _user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for Catalyst Ledger (events).
    """
    channel_id = "catalyst"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)

@router.websocket("/glass/live")
async def websocket_glass_live(
    websocket: WebSocket,
    _user: Annotated[User, Depends(get_websocket_user)],
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
    _user: Annotated[User, Depends(get_websocket_user)],
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
    _user: Annotated[User, Depends(get_websocket_user)],
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

@router.websocket("/floor/pnl")
async def websocket_floor_pnl(
    websocket: WebSocket,
    _user: Annotated[User, Depends(get_websocket_user)],
):
    """
    Real-time feed for The Floor (P&L and Algorithm Status).
    """
    channel_id = "floor_pnl"
    await manager.connect(websocket, channel_id)

    # Start a background task for mock data (for DEMO/Integration purposes)
    async def send_mock_data():
        try:
            while True:
                await asyncio.sleep(2)
                ticker = {
                   "type": "ticker",
                   "payload": {
                       "total_pnl": 1234.56 + random.uniform(-10, 10),
                       "pnl_percentage": 0.023,
                       "active_count": 3,
                       "paused_count": 1,
                       "last_update": datetime.now().isoformat()
                   }
                }
                await websocket.send_text(json.dumps(ticker))

                # Send algos
                algos = {
                    "type": "algorithms",
                    "payload": [
                        {
                            "id": "1",
                            "name": "BTC Arb v2",
                            "pnl_amount": 542.30 + random.uniform(-5, 5),
                            "pnl_percentage": 0.018,
                            "uptime_seconds": 720,
                            "trade_count": 12,
                            "win_count": 8,
                            "loss_count": 4,
                            "status": "active"
                        },
                         {
                            "id": "2",
                            "name": "ETH Grid",
                            "pnl_amount": 320.50,
                            "pnl_percentage": 0.009,
                            "uptime_seconds": 2700,
                            "trade_count": 45,
                            "win_count": 30,
                            "loss_count": 15,
                            "status": "active"
                        },
                         {
                            "id": "3",
                            "name": "SOL MeanRev",
                            "pnl_amount": 371.76,
                            "pnl_percentage": 0.012,
                            "uptime_seconds": 480,
                            "trade_count": 5,
                            "win_count": 3,
                            "loss_count": 2,
                            "status": "paused"
                        }
                    ]
                }
                await websocket.send_text(json.dumps(algos))
        except Exception:
            pass

    task = asyncio.create_task(send_mock_data())

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        task.cancel()
        manager.disconnect(websocket, channel_id)
