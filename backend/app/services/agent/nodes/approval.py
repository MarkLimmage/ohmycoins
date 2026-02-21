# mypy: ignore-errors
"""
Approval Gate Node for Human-in-the-Loop workflow.

This node implements configurable approval gates that require user approval
before proceeding with specific actions (e.g., data fetching, model training).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def approval_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Check if approval is needed at current step.

    Approval gates can be configured for different workflow steps:
    - before_data_fetch: Require approval before fetching data
    - before_training: Require approval before model training
    - before_deployment: Require approval before model deployment (always on)

    Args:
        state: Current workflow state

    Returns:
        Updated state with approval_needed and pending_approvals fields
    """
    logger.info("ApprovalNode: Checking approval requirements")

    current_step = state.get("current_step", "")
    approval_mode = state.get("approval_mode", "manual")
    approval_gates = state.get("approval_gates", [])

    # Determine which approval gate this is
    approval_type = _determine_approval_type(current_step)

    if not approval_type:
        logger.info("ApprovalNode: No approval needed for this step")
        state["approval_needed"] = False
        return state

    # Check if this gate requires approval
    requires_approval = _requires_approval(approval_type, approval_gates, approval_mode)

    if not requires_approval:
        logger.info(f"ApprovalNode: Auto-approval for {approval_type}")
        state["approval_needed"] = False
        _grant_auto_approval(state, approval_type)
        return state

    # Request approval
    logger.info(f"ApprovalNode: Requesting approval for {approval_type}")

    approval_request = _create_approval_request(approval_type, state)

    state["approval_needed"] = True
    state["pending_approvals"] = [approval_request]
    state["current_step"] = f"awaiting_approval_{approval_type}"

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append(
        {
            "step": "approval_requested",
            "approval_type": approval_type,
            "request": approval_request,
        }
    )

    return state


def _determine_approval_type(current_step: str) -> str | None:
    """
    Determine which type of approval is needed based on current step.

    Args:
        current_step: Current workflow step

    Returns:
        Approval type or None if no approval needed
    """
    step_to_approval = {
        "data_retrieval": "before_data_fetch",
        "model_training": "before_training",
        "deployment": "before_deployment",
    }

    for step_key, approval_type in step_to_approval.items():
        if step_key in current_step:
            return approval_type

    return None


def _requires_approval(
    approval_type: str, approval_gates: list[str], approval_mode: str
) -> bool:
    """
    Check if this approval type requires user approval.

    Args:
        approval_type: Type of approval being checked
        approval_gates: List of active approval gates
        approval_mode: "auto" or "manual"

    Returns:
        True if approval is required
    """
    # Deployment always requires approval (safety measure)
    if approval_type == "before_deployment":
        return True

    # In auto mode, no approvals except deployment
    if approval_mode == "auto":
        return False

    # In manual mode, check if this gate is active
    return approval_type in approval_gates


def _create_approval_request(
    approval_type: str, state: dict[str, Any]
) -> dict[str, Any]:
    """
    Create an approval request with context.

    Args:
        approval_type: Type of approval
        state: Current workflow state

    Returns:
        Approval request dictionary
    """
    request = {
        "approval_type": approval_type,
        "timestamp": None,  # Will be set by API
        "status": "pending",
    }

    # Add context based on approval type
    if approval_type == "before_data_fetch":
        request["message"] = "Approve data fetching from external sources?"
        request["details"] = {
            "data_sources": _get_planned_data_sources(state),
            "estimated_records": "Unknown",
        }

    elif approval_type == "before_training":
        request["message"] = "Approve model training with current data?"
        request["details"] = {
            "data_records": _count_data_records(state),
            "models_to_train": _get_planned_models(state),
            "estimated_time": "5-30 seconds per model",
        }

    elif approval_type == "before_deployment":
        request["message"] = "Approve deployment of trained model?"
        request["details"] = {
            "model": state.get("selected_choice", "unknown"),
            "accuracy": _get_model_accuracy(state),
            "warning": "This will deploy the model for live trading consideration",
        }

    return request


def _get_planned_data_sources(state: dict[str, Any]) -> list[str]:
    """Get list of data sources that will be queried."""
    retrieval_params = state.get("retrieval_params", {})
    sources = []

    if retrieval_params.get("fetch_price_data", True):
        sources.append("Price data (CoinSpot)")
    if retrieval_params.get("fetch_sentiment", False):
        sources.append("Sentiment data (news, social)")
    if retrieval_params.get("fetch_on_chain", False):
        sources.append("On-chain metrics")

    return sources if sources else ["Price data (default)"]


def _count_data_records(state: dict[str, Any]) -> int:
    """Count total data records available."""
    retrieved_data = state.get("retrieved_data", {})
    total = 0

    for _data_type, data in retrieved_data.items():
        if isinstance(data, list):
            total += len(data)

    return total


def _get_planned_models(state: dict[str, Any]) -> list[str]:
    """Get list of models that will be trained."""
    training_params = state.get("training_params", {})
    models = training_params.get("model_types", ["RandomForest", "LogisticRegression"])
    return models


def _get_model_accuracy(state: dict[str, Any]) -> str:
    """Get accuracy of selected model."""
    selected_model = state.get("selected_choice")
    evaluation_results = state.get("evaluation_results", {})

    if selected_model and selected_model in evaluation_results:
        accuracy = evaluation_results[selected_model].get("accuracy", 0.0)
        return f"{accuracy:.2%}"

    return "Unknown"


def _grant_auto_approval(state: dict[str, Any], approval_type: str) -> None:
    """
    Grant automatic approval and record it.

    Args:
        state: Workflow state
        approval_type: Type of approval being granted
    """
    if "approvals_granted" not in state:
        state["approvals_granted"] = []

    state["approvals_granted"].append(
        {
            "approval_type": approval_type,
            "mode": "auto",
            "timestamp": None,  # Will be set when logged
        }
    )


def handle_approval_granted(
    state: dict[str, Any], approval_type: str
) -> dict[str, Any]:
    """
    Process user approval.

    Args:
        state: Current workflow state
        approval_type: Type of approval granted

    Returns:
        Updated state with approval recorded
    """
    logger.info(f"ApprovalNode: Approval granted for {approval_type}")

    if "approvals_granted" not in state:
        state["approvals_granted"] = []

    state["approvals_granted"].append(
        {
            "approval_type": approval_type,
            "mode": "manual",
            "timestamp": None,  # Will be set by API
        }
    )

    state["approval_needed"] = False
    state["pending_approvals"] = []

    # Resume workflow
    state["current_step"] = _get_next_step_after_approval(approval_type)

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append(
        {"step": "approval_granted", "approval_type": approval_type}
    )

    return state


def handle_approval_rejected(
    state: dict[str, Any], approval_type: str, reason: str | None = None
) -> dict[str, Any]:
    """
    Process user rejection of approval.

    Args:
        state: Current workflow state
        approval_type: Type of approval rejected
        reason: Optional reason for rejection

    Returns:
        Updated state with workflow stopped
    """
    logger.info(f"ApprovalNode: Approval rejected for {approval_type}")

    state["approval_needed"] = False
    state["pending_approvals"] = []
    state["status"] = "stopped"
    state["current_step"] = "stopped_by_user"
    state["error"] = f"User rejected {approval_type}"

    if reason:
        state["error"] += f": {reason}"

    # Add to reasoning trace
    if "reasoning_trace" not in state or state["reasoning_trace"] is None:
        state["reasoning_trace"] = []

    state["reasoning_trace"].append(
        {"step": "approval_rejected", "approval_type": approval_type, "reason": reason}
    )

    return state


def _get_next_step_after_approval(approval_type: str) -> str:
    """Get the next workflow step after approval is granted."""
    next_steps = {
        "before_data_fetch": "data_retrieval",
        "before_training": "model_training",
        "before_deployment": "deployment",
    }

    return next_steps.get(approval_type, "planning")
