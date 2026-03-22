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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis.asyncio as aioredis
from sqlmodel import Session as DBSession
from sqlmodel import func, select

from app.core.config import settings
from app.core.db import engine
from app.models import AgentSessionMessage, AgentSessionStatus

from .artifacts import ArtifactManager
from .orchestrator import AgentOrchestrator
from .session_manager import SessionManager


def _build_checkpoint_connstr() -> str:
    """Build a psycopg-compatible connection string for the LangGraph checkpointer."""
    s = settings
    return f"postgresql://{s.POSTGRES_USER}:{s.POSTGRES_PASSWORD}@{s.POSTGRES_SERVER}:{s.POSTGRES_PORT}/{s.POSTGRES_DB}"

logger = logging.getLogger(__name__)


def _channel_for(session_id: uuid.UUID) -> str:
    return f"agent:session:{session_id}:stream"


def _get_stage_from_step(step_name: str) -> str:
    """Map workflow step to API StageID."""
    mapping = {
        "initialization": "BUSINESS_UNDERSTANDING",
        "reason": "BUSINESS_UNDERSTANDING",
        "retrieve_data": "DATA_ACQUISITION",
        "validate_data": "PREPARATION",
        "analyze_data": "EXPLORATION",
        "train_model": "MODELING",
        "evaluate_model": "EVALUATION",
        "generate_report": "DEPLOYMENT",
        "finalize": "DEPLOYMENT",
        "dispatch_alerts": "DEPLOYMENT",
        "handle_error": "EVALUATION",
    }
    return mapping.get(step_name, "BUSINESS_UNDERSTANDING")


def _get_task_id_from_step(step_name: str) -> str:
    """Map workflow step to task_id used in plan."""
    mapping = {
        "initialization": "scope_confirmation",
        "scope_confirmation": "scope_confirmation",
        "scope_confirmation_node": "scope_confirmation",
        "reason": "scope_confirmation",
        "retrieve_data": "fetch_price_data",
        "validate_data": "validate_quality",
        "analyze_data": "compute_indicators",
        "train_model": "train_models",
        "evaluate_model": "evaluate_metrics",
        "generate_report": "generate_report",
        "finalize": "generate_report",
    }
    return mapping.get(step_name, step_name)


class AgentRunner:
    """Manages background execution of agent sessions."""

    def __init__(self) -> None:
        self.session_manager = SessionManager()
        self._tasks: dict[uuid.UUID, asyncio.Task] = {}
        self._redis: aioredis.Redis | None = None
        self._checkpointer: Any = None
        self._orchestrator: AgentOrchestrator | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def _get_checkpointer(self) -> Any:
        """Lazily create and initialize a persistent PostgreSQL checkpointer."""
        if self._checkpointer is None:
            try:
                import psycopg
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

                conn_str = _build_checkpoint_connstr()
                conn = await psycopg.AsyncConnection.connect(
                    conn_str, autocommit=True, prepare_threshold=0
                )
                self._checkpointer = AsyncPostgresSaver(conn)
                await self._checkpointer.setup()
                logger.info("Initialized AsyncPostgresSaver checkpointer")
            except Exception:
                logger.warning(
                    "Failed to create PostgresSaver, falling back to MemorySaver",
                    exc_info=True,
                )
                from langgraph.checkpoint.memory import MemorySaver
                self._checkpointer = MemorySaver()
        return self._checkpointer

    @property
    def orchestrator(self) -> AgentOrchestrator:
        """Lazy-init orchestrator (sync property; checkpointer set later if needed)."""
        if self._orchestrator is None:
            self._orchestrator = AgentOrchestrator(self.session_manager)
        return self._orchestrator
    async def start_session(self, session_id: uuid.UUID) -> None:
        """Start a new agent session in the background."""
        logger.info(f"Starting session {session_id}")
        task = asyncio.create_task(self.run_session(session_id))
        self._tasks[session_id] = task

        def _cleanup(t: asyncio.Task) -> None:
            self._tasks.pop(session_id, None)
            if not t.cancelled() and t.exception():
                logger.error(f"Task for session {session_id} failed", exc_info=t.exception())

        task.add_done_callback(_cleanup)

    async def run_session(self, session_id: uuid.UUID) -> None:
        """Execute the agent workflow in its own DB session, publishing events."""
        redis = await self._get_redis()
        channel = _channel_for(session_id)

        with DBSession(engine) as db:
            try:
                # Initialize sequence_id from existing message count
                # Use max(sequence_id) instead of count() for correct sequence tracking (F6)
                max_stmt = (
                    select(func.max(AgentSessionMessage.sequence_id))
                    .select_from(AgentSessionMessage)
                    .where(AgentSessionMessage.session_id == session_id)
                )
                sequence_id = db.exec(max_stmt).one() or 0

                # Initialise the session via orchestrator (sets RUNNING, adds system msg)
                # Only call start_session if this is a fresh run (sequence_id=0 or None)
                if sequence_id == 0:
                    await self.orchestrator.start_session(db, session_id)
                    # This added a message, so sequence_id is now at least 1 (or more)

                # Emit "Session started/resumed" event and persist to DB (F6)
                status_msg = await self.session_manager.add_message(
                    db,
                    session_id,
                    role="assistant",
                    content="Session started" if sequence_id == 0 else "Session resumed",
                    event_type="status_update",
                    stage="BUSINESS_UNDERSTANDING",
                    metadata=json.dumps({"status": AgentSessionStatus.RUNNING})
                )

                current_sequence_id = status_msg.sequence_id or 1

                await self._publish(
                    redis,
                    channel,
                    {
                        "event_type": "status_update",
                        "stage": "BUSINESS_UNDERSTANDING",
                        "sequence_id": current_sequence_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "payload": {
                            "status": AgentSessionStatus.RUNNING,
                            "message": status_msg.content,
                            "task_id": "scope_confirmation",
                        },
                    },
                )

                # Stream through the LangGraph workflow
                session = await self.session_manager.get_session(db, session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")

                from .langgraph_workflow import LangGraphWorkflow

                # Initialize workflow with database session and user context
                # Use persistent checkpointer for cross-container/restart resilience
                checkpointer = await self._get_checkpointer()
                workflow = LangGraphWorkflow(
                    session=db,
                    user_id=session.user_id,
                    credential_id=session.llm_credential_id,
                    checkpointer=checkpointer,
                )

                initial_state = None
                # If fresh run or force restart
                if sequence_id == 0:
                    initial_state = {
                        "session_id": str(session_id),
                        "sequence_id": current_sequence_id,
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
                        "pending_events": [],
                    }

                # Track which event identities we've already processed to avoid duplicates.
                # LangGraph's astream yields full state per node; nodes that don't
                # clear pending_events cause the runner to re-process old events.
                # Use (event_type, content_hash) as dedup key since nodes don't assign sequence_ids.
                processed_event_keys: set[str] = set()
                # Track node-emitted action requests to prevent runner overwrite (F2 enforcement)
                last_node_action: dict[str, Any] | None = None
                # Track current stage for COMPLETE signaling (D5)
                current_tracked_stage: str | None = None
                # Track stages already marked COMPLETE to prevent duplicate emissions
                # when LangGraph replays nodes after approval/resume cycles.
                completed_stages: set[str] = set()

                async for state_update in workflow.stream_execute(initial_state, session_id=str(session_id)):
                    # Increment sequence_id for each state update
                    sequence_id += 1

                    # Each state_update is a dict keyed by node name
                    for node_name, node_state in state_update.items():
                        # Skip LangGraph internal keys (e.g. __interrupt__)
                        if not isinstance(node_state, dict):
                            continue
                        pending_events = node_state.get("pending_events", [])

                        # Process Explicit Events (New Agent System)
                        if pending_events:
                            for event in pending_events:
                                # Deduplicate: build a stable identity key
                                # Nodes don't assign sequence_ids (they're set after DB persist),
                                # so we use event_type + payload hash instead.
                                evt_type = event.get("event_type", "")
                                evt_payload = json.dumps(event.get("payload", {}), sort_keys=True)
                                dedup_key = f"{evt_type}:{evt_payload}"
                                if dedup_key in processed_event_keys:
                                    continue
                                processed_event_keys.add(dedup_key)

                                # D5: COMPLETE signaling on stage transition
                                event_stage = event.get("stage")

                                # Guard: ignore events from stages that are behind
                                # current_tracked_stage (happens when LangGraph replays
                                # earlier nodes after approval/resume cycles).
                                if (
                                    event_stage
                                    and current_tracked_stage
                                    and event_stage != current_tracked_stage
                                    and event_stage in completed_stages
                                ):
                                    continue

                                if (
                                    event_stage
                                    and current_tracked_stage
                                    and event_stage != current_tracked_stage
                                    and current_tracked_stage not in completed_stages
                                    and event.get("event_type") != "revision_start"
                                ):
                                    completed_stages.add(current_tracked_stage)
                                    complete_event = {
                                        "event_type": "status_update",
                                        "stage": current_tracked_stage,
                                        "payload": {
                                            "status": "COMPLETE",
                                            "message": f"Stage {current_tracked_stage} completed",
                                            "task_id": "stage_complete",
                                        },
                                    }
                                    saved_complete = await self.session_manager.add_message(
                                        db,
                                        session_id,
                                        role="assistant",
                                        content=f"COMPLETE: Stage {current_tracked_stage} completed",
                                        agent_name=node_name,
                                        metadata=json.dumps(complete_event),
                                        event_type="status_update",
                                        stage=current_tracked_stage,
                                    )
                                    complete_event["sequence_id"] = saved_complete.sequence_id
                                    complete_event["timestamp"] = saved_complete.created_at.isoformat()
                                    await self._publish(redis, channel, complete_event)
                                    sequence_id = saved_complete.sequence_id

                                if event_stage:
                                    current_tracked_stage = event_stage

                                # F2: Track action_request emission
                                if event.get("event_type") == "action_request":
                                    last_node_action = event

                                # Persist full event to DB for reliable rehydration
                                content_str = ""
                                if event.get("event_type") == "render_output":
                                    content_str = (
                                        f"Render Output: {event.get('payload', {}).get('mime_type')}"
                                    )
                                elif event.get("event_type") == "status_update":
                                    msg = event.get("payload", {}).get("message", "")
                                    status = event.get("payload", {}).get("status")
                                    content_str = f"{status}: {msg}"
                                else:
                                    content_str = str(event.get("payload"))

                                # F6: Persist first to get correct monotonic sequence_id
                                saved_msg = await self.session_manager.add_message(
                                    db,
                                    session_id,
                                    role="assistant",
                                    content=content_str,
                                    agent_name=node_name,
                                    # Update metadata with potentially outdated sequence_id, will be fixed on read?
                                    # Ideally we should update metadata after save, but circular dependency.
                                    # The critical part is event["sequence_id"] for publish
                                    metadata=json.dumps(event),
                                    event_type=event.get("event_type", "message"),
                                    stage=event.get("stage")
                                )

                                # Update sequence_id and timestamp from DB truth
                                event["sequence_id"] = saved_msg.sequence_id
                                # Use DB timestamp for consistency
                                event["timestamp"] = saved_msg.created_at.isoformat()
                                # Update local tracker
                                sequence_id = saved_msg.sequence_id

                                # Publish to Redis with CORRECT sequence_id
                                await self._publish(redis, channel, event)


                        # Fallback for Legacy Nodes (initialization, reason)
                        elif node_state.get("current_step"):
                            sequence_id += 1
                            stage = _get_stage_from_step(
                                node_state.get("current_step", "initialization")
                            )

                            # D5: COMPLETE signaling for legacy fallback path
                            if (
                                current_tracked_stage
                                and stage != current_tracked_stage
                            ):
                                legacy_complete = {
                                    "event_type": "status_update",
                                    "stage": current_tracked_stage,
                                    "payload": {
                                        "status": "COMPLETE",
                                        "message": f"Stage {current_tracked_stage} completed",
                                        "task_id": "stage_complete",
                                    },
                                }
                                saved_lc = await self.session_manager.add_message(
                                    db,
                                    session_id,
                                    role="assistant",
                                    content=f"COMPLETE: Stage {current_tracked_stage} completed",
                                    agent_name=node_name,
                                    metadata=json.dumps(legacy_complete),
                                    event_type="status_update",
                                    stage=current_tracked_stage,
                                )
                                legacy_complete["sequence_id"] = saved_lc.sequence_id
                                legacy_complete["timestamp"] = saved_lc.created_at.isoformat()
                                await self._publish(redis, channel, legacy_complete)
                                sequence_id = saved_lc.sequence_id

                            current_tracked_stage = stage
                            msg = f"Step: {node_state.get('current_step')}"

                            fallback_event = {
                                "event_type": "status_update",
                                "stage": stage,
                                "sequence_id": sequence_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "payload": {
                                    "status": AgentSessionStatus.RUNNING,
                                    "message": msg,
                                    "task_id": _get_task_id_from_step(node_state.get("current_step")),
                                },
                            }

                            await self._publish(redis, channel, fallback_event)
                            await self.session_manager.add_message(
                                db,
                                session_id,
                                role="assistant",
                                content=msg,
                                agent_name=node_name,
                                metadata=json.dumps(fallback_event),
                            )
                        # Handle HITL / Action Requests (Legacy Support)
                        if node_state.get("awaiting_choice") and node_state.get("choices_available"):
                            sequence_id += 1
                            stage = _get_stage_from_step(
                                node_state.get("current_step", "initialization")
                            )
                            choices = node_state.get("choices_available", [])
                            # Extract descriptions/labels based on assumed structure
                            options = [str(c) for c in choices]

                            action_event = {
                                "event_type": "action_request",
                                "stage": stage,
                                "sequence_id": sequence_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "payload": {
                                    "action_id": "user_choice_required",
                                    "description": node_state.get(
                                        "choice_description", "User input required"
                                    ),
                                    "options": options,
                                },
                            }

                            await self._publish(redis, channel, action_event)
                            await self.session_manager.add_message(
                                db,
                                session_id,
                                role="assistant",
                                content=f"Action Required: {action_event['payload'].get('description', '')}",
                                agent_name=node_name,
                                metadata=json.dumps(action_event),
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

                # Check for interrupts after stream ends
                config = {"configurable": {"thread_id": str(session_id)}}
                state_snapshot = await workflow.graph.aget_state(config)

                if state_snapshot.next:
                    # Handle Interrupt
                    next_node = state_snapshot.next[0]
                    # Log interrupt
                    logger.info(f"Session {session_id} interrupted at {next_node}")

                    # F2 & F5: Logic to handle node-emitted action requests
                    if last_node_action:
                        # Use node's emitted action details for Redis state
                        payload = last_node_action.get("payload", {})
                        action_id = last_node_action.get("action_id") or payload.get("action_id") or f"approve_{next_node}"
                        description = payload.get("description", "Action required")
                        options = payload.get("options", ["APPROVE", "REJECT"])
                        stage = last_node_action.get("stage", _get_stage_from_step(next_node))

                        logger.info(f"Using existing node action_request: {action_id}")
                    else:
                        # Fallback: Generic action_request
                        action_id = f"approve_{next_node}"
                        description = f"Workflow paused before step: {next_node}. Please review and approve to continue."
                        options = ["APPROVE", "REJECT"]

                        if next_node == "train_model":
                            description = "Model training is ready. Please review data analysis and feature selection."
                        elif next_node == "finalize":
                            description = "Workflow complete. Please review reports and model artifacts before finalization."

                        stage = _get_stage_from_step(next_node)

                        # Emit action_request
                        sequence_id += 1
                        action_event = {
                            "event_type": "action_request",
                            "stage": stage,
                            "sequence_id": sequence_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {
                                "action_id": action_id,
                                "description": description,
                                "options": options,
                            },
                        }
                        await self._publish(redis, channel, action_event)

                        # Persist action_request to DB for rehydration
                        await self.session_manager.add_message(
                            db,
                            session_id,
                            role="assistant",
                            content=f"Action Required: {description}",
                            agent_name=next_node,
                            metadata=json.dumps(action_event),
                        )

                    # Emit status_update with AWAITING_APPROVAL
                    sequence_id += 1
                    status_event = {
                        "event_type": "status_update",
                        "stage": stage,
                        "sequence_id": sequence_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "payload": {
                            "status": AgentSessionStatus.AWAITING_APPROVAL,
                            "message": f"Waiting for approval to proceed to {next_node}",
                            "task_id": _get_task_id_from_step(next_node),
                        },
                    }
                    await self._publish(redis, channel, status_event)

                    # Persist status_update to DB
                    await self.session_manager.add_message(
                        db,
                        session_id,
                        role="assistant",
                        content=f"AWAITING_APPROVAL: Waiting for approval to proceed to {next_node}",
                        agent_name=next_node,
                        metadata=json.dumps(status_event),
                    )

                    # Update DB session status
                    await self.session_manager.update_session_status(
                        db,
                        session_id,
                        AgentSessionStatus.AWAITING_APPROVAL,
                        result_summary=f"Waiting for approval at {next_node}",
                    )

                    # Save approval state to Redis so approve endpoint can find it
                    await self.session_manager.save_session_state(
                        session_id,
                        {
                            "session_id": str(session_id),
                            "user_goal": session.user_goal,
                            "status": AgentSessionStatus.AWAITING_APPROVAL,
                            "current_step": next_node,
                            "iteration": 0,
                            "approval_needed": True,
                            "pending_approvals": [{
                                "approval_type": action_id,
                                "description": description,
                                "options": options,
                            }],
                        },
                    )
                else:
                    # D5: Emit COMPLETE for the final stage before marking session done
                    if current_tracked_stage:
                        final_complete = {
                            "event_type": "status_update",
                            "stage": current_tracked_stage,
                            "payload": {
                                "status": "COMPLETE",
                                "message": f"Stage {current_tracked_stage} completed",
                                "task_id": "stage_complete",
                            },
                        }
                        saved_final = await self.session_manager.add_message(
                            db,
                            session_id,
                            role="assistant",
                            content=f"COMPLETE: Stage {current_tracked_stage} completed",
                            agent_name="runner",
                            metadata=json.dumps(final_complete),
                            event_type="status_update",
                            stage=current_tracked_stage,
                        )
                        final_complete["sequence_id"] = saved_final.sequence_id
                        final_complete["timestamp"] = saved_final.created_at.isoformat()
                        await self._publish(redis, channel, final_complete)

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
        # Close persistent checkpointer connection
        if self._checkpointer is not None and hasattr(self._checkpointer, "conn"):
            try:
                await self._checkpointer.conn.close()
            except Exception:
                pass
        self._checkpointer = None

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
