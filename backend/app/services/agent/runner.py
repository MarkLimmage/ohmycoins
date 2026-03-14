# mypy: ignore-errors
"""
AgentRunner: Background session execution with Redis pub/sub streaming.

Decouples session execution from the HTTP request cycle. Sessions run as
asyncio tasks; state updates are published to Redis channels for WebSocket
consumers to relay in real-time.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

import redis.asyncio as aioredis
from sqlmodel import Session as DBSession

from app.core.config import settings
from app.core.db import engine
from app.models import AgentSessionStatus

from .artifacts import ArtifactManager
from .orchestrator import AgentOrchestrator
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


def _channel_for(session_id: uuid.UUID) -> str:
    return f"agent:session:{session_id}:stream"


class AgentRunner:
    """Manages background execution of agent sessions."""

    def __init__(self) -> None:
        self.session_manager = SessionManager()
        self.orchestrator = AgentOrchestrator(self.session_manager)
        self._tasks: dict[uuid.UUID, asyncio.Task] = {}
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def start_session(self, session_id: uuid.UUID) -> None:
        """Launch a background task for the given session."""
        if session_id in self._tasks and not self._tasks[session_id].done():
            logger.warning("Session %s is already running", session_id)
            return

        task = asyncio.create_task(self._run(session_id))
        self._tasks[session_id] = task
        task.add_done_callback(lambda t: self._on_done(session_id, t))

    async def _run(self, session_id: uuid.UUID) -> None:
        """Execute the agent workflow in its own DB session, publishing events."""
        redis = await self._get_redis()
        channel = _channel_for(session_id)

        with DBSession(engine) as db:
            try:
                # Initialise the session via orchestrator (sets RUNNING, adds system msg)
                await self.orchestrator.start_session(db, session_id)

                await self._publish(
                    redis,
                    channel,
                    {
                        "type": "status",
                        "content": "Session started",
                        "status": AgentSessionStatus.RUNNING,
                    },
                )

                # Stream through the LangGraph workflow
                session = await self.session_manager.get_session(db, session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")

                from .langgraph_workflow import AgentState, LangGraphWorkflow

                # Initialize workflow with database session and user context
                workflow = LangGraphWorkflow(
                    session=db,
                    user_id=session.user_id,
                    credential_id=session.llm_credential_id,
                )
                initial_state: AgentState = {
                    "session_id": str(session_id),
                    "user_goal": session.user_goal,
                    "status": AgentSessionStatus.RUNNING,
                    "current_step": "initialization",
                    "iteration": 0,
                    "messages": [],
                    "data_retrieved": {},
                    "analysis_results": {},
                    "models_trained": [],
                    "evaluation_results": {},
                    "report": None,
                    "error": None,
                    "max_iterations": 10,
                    "awaiting_clarification": False,
                    "clarifications_needed": [],
                    "awaiting_choice": False,
                    "choices_available": [],
                    "recommendation": None,
                    "approval_needed": False,
                    "pending_approvals": [],
                    "approval_mode": "manual",
                    "overrides_applied": [],
                }

                async for state_update in workflow.stream_execute(initial_state):
                    # Each state_update is a dict keyed by node name
                    for node_name, node_state in state_update.items():
                        content = ""
                        msg_type = "output"
                        agent_name = node_name
                        metadata_json = None

                        if isinstance(node_state, dict):
                            # Sprint 2.45: Check for structured event types first
                            if node_state.get("trained_models"):
                                msg_type = "metric"
                                trained = node_state.get("trained_models", {})
                                content = json.dumps(
                                    {
                                        "metric_type": "training_metrics",
                                        "data": {
                                            k: str(v)[:500]
                                            for k, v in trained.items()
                                            if v
                                        },
                                    },
                                    default=str,
                                )
                            elif node_state.get("evaluation_results"):
                                msg_type = "metric"
                                eval_results = node_state.get("evaluation_results", {})
                                content = json.dumps(
                                    {
                                        "metric_type": "evaluation_metrics",
                                        "data": {
                                            k: str(v)[:500]
                                            for k, v in eval_results.items()
                                            if v
                                        },
                                    },
                                    default=str,
                                )
                            elif node_state.get("awaiting_choice") and node_state.get(
                                "choices_available"
                            ):
                                msg_type = "blueprint"
                                content = json.dumps(
                                    {
                                        "choices": node_state.get(
                                            "choices_available", []
                                        ),
                                    },
                                    default=str,
                                )
                            elif node_state.get("result"):
                                msg_type = "output"
                                content = node_state["result"]
                            else:
                                # Original content extraction logic
                                content = (
                                    node_state.get("report")
                                    or node_state.get("error")
                                    or json.dumps(
                                        {
                                            k: str(v)[:200]
                                            for k, v in node_state.items()
                                            if v
                                        },
                                        default=str,
                                    )
                                )
                                if node_state.get("error"):
                                    msg_type = "result"
                                    metadata_json = content
                                elif node_state.get("current_step"):
                                    msg_type = "thought"
                                    metadata_json = content
                                    content = f"Step: {node_state['current_step']}"
                        else:
                            content = str(node_state)

                        # Persist message to DB
                        await self.session_manager.add_message(
                            db,
                            session_id,
                            role="assistant",
                            content=content,
                            agent_name=agent_name,
                            metadata=metadata_json,
                        )

                        # Publish to Redis for live WS consumers
                        pub_metadata = None
                        if metadata_json:
                            try:
                                pub_metadata = json.loads(metadata_json)
                            except Exception:
                                pub_metadata = {"raw": metadata_json}

                        await self._publish(
                            redis,
                            channel,
                            {
                                "type": msg_type,
                                "content": content,
                                "agent_name": agent_name,
                                "timestamp": None,  # will be set by consumer
                                "metadata": pub_metadata,
                            },
                        )

                # Register any artifacts written to disk during the workflow
                artifact_dir = Path(f"/data/agent_artifacts/{session_id}")
                if artifact_dir.exists():
                    artifact_mgr = ArtifactManager(base_dir="/data/agent_artifacts")
                    for file_path in artifact_dir.iterdir():
                        if file_path.is_file():
                            ext = file_path.suffix.lower()
                            if ext in (".joblib", ".pkl"):
                                artifact_type = "model"
                            elif ext == ".json":
                                artifact_type = "data"
                            else:
                                artifact_type = "other"

                            existing = artifact_mgr.list_artifacts(
                                session_id, db_session=db
                            )
                            already_registered = any(
                                a.file_path and Path(a.file_path).name == file_path.name
                                for a in existing
                            )
                            if not already_registered:
                                artifact_mgr.save_artifact(
                                    session_id=session_id,
                                    artifact_type=artifact_type,
                                    name=file_path.name,
                                    file_path=file_path,
                                    description=f"Auto-registered {artifact_type} artifact",
                                    db_session=db,
                                )

                # Mark completed
                await self.session_manager.update_session_status(
                    db,
                    session_id,
                    AgentSessionStatus.COMPLETED,
                    result_summary="Session completed successfully",
                )
                await self._publish(
                    redis,
                    channel,
                    {
                        "type": "status",
                        "content": "Session completed",
                        "status": AgentSessionStatus.COMPLETED,
                        "done": True,
                    },
                )

            except asyncio.CancelledError:
                await self.session_manager.update_session_status(
                    db,
                    session_id,
                    AgentSessionStatus.CANCELLED,
                )
                await self._publish(
                    redis,
                    channel,
                    {
                        "type": "status",
                        "content": "Session cancelled",
                        "status": AgentSessionStatus.CANCELLED,
                        "done": True,
                    },
                )
                raise

            except Exception as exc:
                logger.exception("Agent session %s failed", session_id)
                await self.session_manager.update_session_status(
                    db,
                    session_id,
                    AgentSessionStatus.FAILED,
                    error_message=str(exc),
                )
                await self._publish(
                    redis,
                    channel,
                    {
                        "type": "status",
                        "content": f"Session failed: {exc}",
                        "status": AgentSessionStatus.FAILED,
                        "done": True,
                    },
                )

    def _on_done(self, session_id: uuid.UUID, task: asyncio.Task) -> None:
        self._tasks.pop(session_id, None)
        if task.cancelled():
            logger.info("Session %s task cancelled", session_id)
        elif task.exception():
            logger.error("Session %s task exception: %s", session_id, task.exception())

    async def cancel_session(self, session_id: uuid.UUID) -> bool:
        """Cancel a running session."""
        task = self._tasks.get(session_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def is_running(self, session_id: uuid.UUID) -> bool:
        task = self._tasks.get(session_id)
        return task is not None and not task.done()

    async def shutdown(self) -> None:
        """Cancel all running tasks and close Redis."""
        for _sid, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
        # Wait for all tasks to finish
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    @staticmethod
    async def _publish(
        redis: aioredis.Redis, channel: str, data: dict[str, Any]
    ) -> None:
        try:
            await redis.publish(channel, json.dumps(data, default=str))
        except Exception:
            logger.warning("Failed to publish to %s", channel, exc_info=True)


# Module-level singleton
_runner: AgentRunner | None = None


def get_runner() -> AgentRunner:
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner


async def shutdown_runner() -> None:
    global _runner
    if _runner is not None:
        await _runner.shutdown()
        _runner = None
