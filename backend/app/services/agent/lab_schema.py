from enum import Enum
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel


class StageID(str, Enum):
    BUSINESS_UNDERSTANDING = "BUSINESS_UNDERSTANDING"
    DATA_ACQUISITION = "DATA_ACQUISITION"
    PREPARATION = "PREPARATION"
    EXPLORATION = "EXPLORATION"
    MODELING = "MODELING"
    EVALUATION = "EVALUATION"
    DEPLOYMENT = "DEPLOYMENT"


# Ordered list of DSLC stages for stale-cascade calculation
DSLC_STAGE_ORDER: list[StageID] = list(StageID)


class NodeStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETE = "COMPLETE"
    STALE = "STALE"
    RETRYING_OPTIMIZATION = "RETRYING_OPTIMIZATION"


class MimeType(str, Enum):
    TEXT_MARKDOWN = "text/markdown"
    PLOTLY_JSON = "application/vnd.plotly.v1+json"
    IMAGE_PNG = "image/png"
    JSON_BLUEPRINT = "application/json+blueprint"
    JSON_TEARSHEET = "application/json+tearsheet"


class LabState(TypedDict):
    """
    State dictionary for the Phase 2 LangGraph workflow.
    Adheres to the strict schema requirements.
    """

    session_id: str
    messages: Annotated[
        list[Any], add_messages
    ]  # standard LangChain messages with reducer
    current_stage: StageID
    status: NodeStatus

    # Data context
    user_goal: str
    dataset_name: str | None
    features: list[str]

    # Artifacts (Output results from stages)
    data_acquisition_result: dict[str, Any] | None
    exploration_result: dict[str, Any] | None
    modeling_result: dict[str, Any] | None
    evaluation_result: dict[str, Any] | None

    # Execution Flags
    error: str | None
    retry_count: int
    human_approved: bool


# Event Schemas for WebSocket communication (Pydantic for validation)
class BaseEvent(BaseModel):
    event_type: Literal[
        "stream_chat", "status_update", "render_output", "error",
        "action_request", "user_message", "plan_established", "revision_start",
    ]
    stage: StageID
    sequence_id: int
    timestamp: str  # ISO-8601 UTC
    payload: Any


class StreamChatPayload(BaseModel):
    text_delta: str


class StreamChatEvent(BaseEvent):
    event_type: Literal["stream_chat"] = "stream_chat"
    payload: StreamChatPayload


class StatusUpdatePayload(BaseModel):
    status: NodeStatus
    message: str | None = None


class StatusUpdateEvent(BaseEvent):
    event_type: Literal["status_update"] = "status_update"
    payload: StatusUpdatePayload


class RenderOutputPayload(BaseModel):
    mime_type: str
    content: Any
    code_snippet: str | None = None
    hyperparameters: dict[str, Any] | None = None


class RenderOutputEvent(BaseEvent):
    event_type: Literal["render_output"] = "render_output"
    payload: RenderOutputPayload


class ActionRequestPayload(BaseModel):
    action_id: str
    description: str
    options: list[str]


class ActionRequestEvent(BaseEvent):
    event_type: Literal["action_request"] = "action_request"
    payload: ActionRequestPayload



class ErrorPayload(BaseModel):
    message: str
    code: str
    details: Any | None = None


class ErrorEvent(BaseEvent):
    event_type: Literal["error"] = "error"
    payload: ErrorPayload


class RevisionStartPayload(BaseModel):
    revised_stage: str
    stale_stages: list[str]
    revision_epoch: int = 1


class RevisionStartEvent(BaseEvent):
    event_type: Literal["revision_start"] = "revision_start"
    payload: RevisionStartPayload


def stages_after(stage_id: StageID) -> list[StageID]:
    """Return all DSLC stages ordered AFTER the given stage."""
    try:
        idx = DSLC_STAGE_ORDER.index(stage_id)
    except ValueError:
        return []
    return DSLC_STAGE_ORDER[idx + 1:]
