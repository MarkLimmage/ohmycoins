"""
Base Agent class for all specialized agents.

This provides common functionality for all agent types.
"""

from datetime import datetime, timezone
from typing import Any, Literal

from app.services.websocket_manager import manager

# Allowed MimeTypes as per API Contract
MimeType = Literal[
    "text/markdown",
    "application/vnd.plotly.v1+json",
    "image/png",
    "application/json+blueprint",
    "application/json+tearsheet",
]

ALLOWED_MIME_TYPES = {
    "text/markdown",
    "application/vnd.plotly.v1+json",
    "image/png",
    "application/json+blueprint",
    "application/json+tearsheet",
}


class BaseAgent:
    """
    Base class for all specialized agents in the system.

    Each agent has a specific responsibility in the data science workflow.
    """

    def __init__(self, name: str, description: str) -> None:
        """
        Initialize the base agent.

        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent's primary function.

        Args:
            state: Current workflow state

        Returns:
            Updated state after agent execution
        """
        raise NotImplementedError("Subclasses must implement execute method")

    async def emit_event(
        self,
        state: dict[str, Any],
        event_type: str,
        stage: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Emit a structured event to the frontend via WebSocket.

        This method handles sequence_id generation and timestamping
        automatically to ensure compliance with API Contracts.

        Args:
            state: Current session state (must contain session_id)
            event_type: Type of event (stream_chat, status_update, render_output, error)
            stage: Current workflow stage ID
            payload: Event payload dictionary
        """
        # 1. Enforce MimeType compliance for render_output
        if event_type == "render_output":
            mime_type = payload.get("mime_type")
            if mime_type not in ALLOWED_MIME_TYPES:
                raise ValueError(
                    f"Invalid MimeType: '{mime_type}'. "
                    f"Allowed types: {ALLOWED_MIME_TYPES}"
                )

        # 2. Get session_id
        session_id = state.get("session_id")
        if not session_id:
            # Cannot emit event without a session ID/channel
            # In production, this might log a warning or raise an error
            return

        # 3. Manage Sequence ID
        # Initialize if not present (starts at 0 in state, first event is 1)
        if "sequence_id" not in state:
            state["sequence_id"] = 0

        state["sequence_id"] += 1
        
        # 4. Append to pending_events queue
        # The Runner will drain this queue and publish to Redis
        if "pending_events" not in state or state["pending_events"] is None:
            state["pending_events"] = []

        event = {
            "event_type": event_type,
            "stage": stage,
            "sequence_id": state["sequence_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        
        state["pending_events"].append(event)

        sequence_id = state["sequence_id"]

        # 4. Generate Timestamp (ISO-8601 UTC)
        # Using Z suffix for strict ISO-8601 UTC compliance
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Construct Wrapper Schema
        event = {
            "event_type": event_type,
            "stage": stage,
            "sequence_id": sequence_id,
            "timestamp": timestamp,
            "payload": payload,
        }

        # 6. Broadcast
        await manager.broadcast_json(event, session_id)
