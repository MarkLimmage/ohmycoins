import asyncio
import json
import random
import uuid
from datetime import datetime
from typing import Annotated, Any, cast

import jwt
import redis.asyncio as aioredis
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
from sqlmodel import Session, select

from app.api.deps import get_current_active_superuser, get_db
from app.core import security
from app.core.config import settings
from app.models import AgentSession, AgentSessionMessage, TokenPayload, User
from app.services.websocket_manager import manager

router = APIRouter()


class BroadcastMessage(BaseModel):
    channel: str
    message: dict[str, Any]


@router.post("/broadcast", include_in_schema=False)
async def broadcast_message(
    body: BroadcastMessage,
    _user: Annotated[User, Depends(get_current_active_superuser)],
) -> dict[str, str]:
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
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token"
        )

    user = session.get(User, token_data.sub)
    if not user:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )

    if not user.is_active:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user"
        )

    return user


@router.websocket("/catalyst/live")
async def websocket_catalyst_live(
    websocket: WebSocket,
    _user: Annotated[User, Depends(get_websocket_user)],
) -> None:
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
) -> None:
    """
    Real-time feed for Glass (market data).
    """
    channel_id = "glass"
    await manager.connect(websocket, channel_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel_id)


@router.websocket("/lab/{session_id}")
async def websocket_lab(
    websocket: WebSocket,
    session_id: str,
    # _user: Annotated[User, Depends(get_websocket_user)], # authentication for later
) -> None:
    """
    Bi-directional WebSocket for 'The Lab' LangGraph agent.
    """
    await websocket.accept()

    from langchain_core.messages import HumanMessage

    from app.services.agent.lab_graph import app as lab_agent
    from app.services.agent.lab_schema import LabState, NodeStatus, StageID

    try:
        while True:
            data = await websocket.receive_text()
            # Expecting JSON with user message or command
            # For simplicity assuming raw text for now or simple JSON
            try:
                payload = json.loads(data)
                user_input = payload.get("message", "")
            except (json.JSONDecodeError, TypeError):
                user_input = data

            # Initialize state if needed
            initial_state: LabState = {
                "messages": [HumanMessage(content=user_input)],
                "session_id": session_id,
                "current_stage": StageID.BUSINESS_UNDERSTANDING,  # Default for new runs
                "status": NodeStatus.PENDING,
                "retry_count": 0,
                # Required fields with defaults
                "user_goal": "",
                "dataset_name": None,
                "features": [],
                "data_acquisition_result": None,
                "exploration_result": None,
                "modeling_result": None,
                "evaluation_result": None,
                "error": None,
                "human_approved": False,
            }

            # Run the graph and stream events
            # We use stream_mode="updates" to get state changes from each node
            async for event in lab_agent.astream(
                cast(Any, initial_state),
                config={"configurable": {"thread_id": session_id}},
            ):
                # event is a dict of node_name -> state_update
                for node_name, state_update in event.items():
                    # Check for messages to stream
                    if "messages" in state_update and state_update["messages"]:
                        last_msg = state_update["messages"][-1]
                        if hasattr(last_msg, "content"):
                            await websocket.send_json(
                                {
                                    "event_type": "stream_chat",
                                    "stage": node_name,  # Map node name to StageID
                                    "payload": {"text_delta": last_msg.content},
                                }
                            )

                    # Check for results to render
                    # Mapping node results to render_output events
                    result_keys = {
                        "data_acquisition_result": StageID.DATA_ACQUISITION,
                        "exploration_result": StageID.EXPLORATION,
                        "modeling_result": StageID.MODELING,
                        "evaluation_result": StageID.EVALUATION,
                    }

                    for key, stage in result_keys.items():
                        if key in state_update and state_update[key]:
                            await websocket.send_json(
                                {
                                    "event_type": "render_output",
                                    "stage": stage,
                                    "payload": state_update[key],
                                }
                            )

                    # Send status update
                    await websocket.send_json(
                        {
                            "event_type": "status_update",
                            "stage": node_name,
                            "payload": {"status": "COMPLETE"},  # mocking success
                        }
                    )

    except WebSocketDisconnect:
        # Handle disconnect
        pass
    except Exception as e:
        # Send error event
        await websocket.send_json(
            {
                "event_type": "error",
                "stage": "UNKNOWN",  # Could track current stage
                "payload": {"message": str(e), "code": "INTERNAL_ERROR"},
            }
        )


@router.websocket("/human/live")
async def websocket_human_live(
    websocket: WebSocket,
    _user: Annotated[User, Depends(get_websocket_user)],
) -> None:
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
) -> None:
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
) -> None:
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
) -> None:
    """
    Real-time feed for The Floor (P&L and Algorithm Status).
    """
    channel_id = "floor_pnl"
    await manager.connect(websocket, channel_id)

    # Start a background task for mock data (for DEMO/Integration purposes)
    async def send_mock_data() -> None:
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
                        "last_update": datetime.now().isoformat(),
                    },
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
                            "status": "active",
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
                            "status": "active",
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
                            "status": "paused",
                        },
                    ],
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


@router.websocket("/agent/{session_id}/stream")
async def websocket_agent_stream(
    websocket: WebSocket,
    session_id: uuid.UUID,
    user: Annotated[User, Depends(get_websocket_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Real-time streaming for agent session execution.

    1. Replays historical messages from DB (for reconnection).
    2. Subscribes to Redis pub/sub channel for live updates.
    3. Closes when session completes/fails/cancels.
    """
    # Verify session exists and belongs to user
    statement = select(AgentSession).where(AgentSession.id == session_id)
    session_obj = db.exec(statement).first()

    if not session_obj:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Session not found"
        )
    if session_obj.user_id != user.id:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION, reason="Not authorized"
        )

    await websocket.accept()

    # Step 1: Replay historical messages
    hist_statement = (
        select(AgentSessionMessage)
        .where(AgentSessionMessage.session_id == session_id)
        .order_by(AgentSessionMessage.created_at)  # type: ignore[arg-type]
    )
    history = db.exec(hist_statement).all()
    for msg in history:
        await websocket.send_text(
            json.dumps(
                {
                    "id": str(msg.id),
                    "type": "output",
                    "content": msg.content,
                    "agent_name": msg.agent_name,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                    "replay": True,
                }
            )
        )

    # If session already finished, send done and close
    if session_obj.status in ("completed", "failed", "cancelled"):
        await websocket.send_text(
            json.dumps(
                {
                    "type": "status",
                    "content": f"Session {session_obj.status}",
                    "status": session_obj.status,
                    "done": True,
                }
            )
        )
        await websocket.close()
        return

    # Step 2: Subscribe to Redis pub/sub for live updates
    channel_name = f"agent:session:{session_id}:stream"
    redis_client: aioredis.Redis | None = None
    pubsub: aioredis.client.PubSub | None = None

    try:
        redis_client = await aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        assert redis_client is not None
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel_name)

        async def relay_from_redis() -> None:
            """Forward Redis pub/sub messages to WebSocket."""
            assert pubsub is not None
            async for raw_msg in pubsub.listen():
                if raw_msg["type"] != "message":
                    continue
                data = raw_msg["data"]
                await websocket.send_text(data)
                # Check for completion
                try:
                    parsed = json.loads(data)
                    if parsed.get("done"):
                        return
                except (json.JSONDecodeError, TypeError):
                    pass

        relay_task = asyncio.create_task(relay_from_redis())

        try:
            # Keep connection alive while relay runs
            while not relay_task.done():
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
        except WebSocketDisconnect:
            pass
        finally:
            relay_task.cancel()
            try:
                await relay_task
            except (asyncio.CancelledError, Exception):
                pass

    finally:
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.aclose()  # type: ignore[no-untyped-call]
        if redis_client:
            await redis_client.aclose()
