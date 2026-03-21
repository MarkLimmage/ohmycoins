# mypy: ignore-errors
"""
Checkpoint rewind helper for revision protocol (Phase 7.2.2 foundation).

When a user revises a completed stage, the ideal behavior is to rewind
the LangGraph state to the checkpoint at the START of that stage, creating
a new branch. This module provides the scaffolding for that behavior.

Phase 7.2.3 will refine the full rewind logic. For now, we provide:
- Stage-checkpoint lookup (find where a stage began)
- Basic branch-from-checkpoint API surface

Current limitation: LangGraph's AsyncPostgresSaver checkpoint API
supports get_state_history() for listing checkpoints, but creating
a branch from an arbitrary checkpoint requires constructing a new
config with a parent_config pointing to the desired checkpoint.
The runner currently re-executes from scratch on revision, which is
functionally correct but not optimal.
"""

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


# Mapping from DSLC stage to the workflow step(s) that BEGIN that stage
_STAGE_START_STEPS: dict[str, list[str]] = {
    "BUSINESS_UNDERSTANDING": ["initialization", "reason"],
    "DATA_ACQUISITION": ["retrieve_data"],
    "PREPARATION": ["validate_data"],
    "EXPLORATION": ["analyze_data"],
    "MODELING": ["train_model"],
    "EVALUATION": ["evaluate_model"],
    "DEPLOYMENT": ["generate_report", "finalize"],
}


async def find_stage_checkpoint(
    checkpointer: Any,
    session_id: uuid.UUID,
    target_stage: str,
) -> dict[str, Any] | None:
    """
    Find the checkpoint where a given stage began.

    Walks the checkpoint history for the session thread and returns
    the first checkpoint whose step matches the target stage's entry node.

    Returns None if no matching checkpoint is found.
    """
    start_steps = _STAGE_START_STEPS.get(target_stage, [])
    if not start_steps:
        logger.warning("No start steps mapped for stage %s", target_stage)
        return None

    config = {"configurable": {"thread_id": str(session_id)}}

    try:
        # LangGraph's get_state_history returns checkpoints in reverse order
        if hasattr(checkpointer, "aget_state_history"):
            # Async path (AsyncPostgresSaver)
            async for state in checkpointer.aget_state_history(config):
                metadata = state.metadata or {}
                step_name = metadata.get("source", "")
                if step_name in start_steps:
                    return {
                        "checkpoint_id": state.config.get("configurable", {}).get("checkpoint_id"),
                        "thread_id": str(session_id),
                        "step": step_name,
                        "stage": target_stage,
                    }
        else:
            # Sync fallback (MemorySaver)
            for state in checkpointer.get_state_history(config):
                metadata = state.metadata or {}
                step_name = metadata.get("source", "")
                if step_name in start_steps:
                    return {
                        "checkpoint_id": state.config.get("configurable", {}).get("checkpoint_id"),
                        "thread_id": str(session_id),
                        "step": step_name,
                        "stage": target_stage,
                    }
    except Exception:
        logger.warning(
            "Failed to search checkpoint history for session %s stage %s",
            session_id,
            target_stage,
            exc_info=True,
        )

    return None


def build_revision_config(
    session_id: uuid.UUID,
    checkpoint_info: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Build a LangGraph config for executing from a revision checkpoint.

    If checkpoint_info is available, creates a branched config.
    Otherwise falls back to a fresh thread config (re-execute from scratch).
    """
    if checkpoint_info and checkpoint_info.get("checkpoint_id"):
        # Branch from the found checkpoint
        return {
            "configurable": {
                "thread_id": str(session_id),
                "checkpoint_id": checkpoint_info["checkpoint_id"],
            }
        }

    # Fallback: re-use same thread (will continue from latest checkpoint)
    logger.info(
        "No checkpoint found for revision; falling back to latest state for session %s",
        session_id,
    )
    return {"configurable": {"thread_id": str(session_id)}}
