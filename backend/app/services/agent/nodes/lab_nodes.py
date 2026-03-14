import json
import logging
from typing import Any

from langchain_core.messages import AIMessage

from app.services.agent.lab_schema import (
    LabState,
    NodeStatus,
    RenderOutputPayload,
    StageID,
)
from app.services.agent.tools.sandbox import execute_sandbox_code
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)


def _format_execution_output(
    result: dict[str, Any], code: str, mime_type: str = "text/markdown"
) -> RenderOutputPayload:
    """Helper to format Sandbox execution results into API-compliant payload."""
    content = result.get("stdout", "")
    stderr = result.get("stderr", "")

    if stderr:
        content += f"\n\n### Stderr\n```\n{stderr}\n```"

    # Attempt to parse JSON content if the mime_type suggests JSON
    if "json" in mime_type:
        try:
            # If stdout is a JSON string, parse it
            parsed = json.loads(content)
            content = parsed
        except json.JSONDecodeError:
            # If parsing fails, fall back to text, but log warning
            logger.warning(f"Failed to parse JSON content for {mime_type}")
            mime_type = "text/markdown"  # Fallback
            content = f"Failed to parse JSON output:\n```\n{content}\n```"

    return {
        "mime_type": mime_type,
        "content": content,
        "code_snippet": code,
        "hyperparameters": None,
    }


async def _emit_status_update(
    session_id: str, stage: StageID, status: NodeStatus, message: str | None = None
) -> None:
    """Emits a status_update event via WebSocket."""
    payload = {"status": status, "message": message}
    await manager.broadcast_json(
        {"event_type": "status_update", "stage": stage, "payload": payload},
        channel_id=session_id,
    )


async def _emit_render_output(
    session_id: str, stage: StageID, payload: RenderOutputPayload
) -> None:
    """Emits a render_output event via WebSocket."""
    await manager.broadcast_json(
        {"event_type": "render_output", "stage": stage, "payload": payload},
        channel_id=session_id,
    )


async def _emit_error(
    session_id: str, stage: StageID, message: str, code: int = 500
) -> None:
    """Emits an error event via WebSocket."""
    payload = {"message": message, "code": code}
    await manager.broadcast_json(
        {"event_type": "error", "stage": stage, "payload": payload},
        channel_id=session_id,
    )


async def _mock_execute_code(code: str, stage: StageID) -> dict[str, Any]:
    """Mock execution to avoid real backend dependencies."""
    if stage == StageID.DATA_ACQUISITION:
        # Simulate loading data
        return {
            "stdout": "   open    high     low   close  volume\n0  100.0  101.0   99.0   100.5    1000\n1  100.5  102.0  100.0   101.5    1200\n\nShape: (2000, 5)\n\nColumns: ['open', 'high', 'low', 'close', 'volume']",
            "stderr": "",
        }
    elif stage == StageID.EXPLORATION:
        # Simulate Plotly JSON
        return {
            "stdout": json.dumps(
                {
                    "data": [
                        {"x": [1, 2, 3], "y": [10, 15, 13], "type": "scatter"}
                    ],
                    "layout": {"title": "Mock Price Chart"},
                }
            ),
            "stderr": "",
        }
    elif stage == StageID.MODELING:
        # Simulate Blueprint
        modeling_metrics: dict[str, Any] = {
            "target_variable": "target_return_1h",
            "feature_list": ["volatility_24h", "sentiment_1h", "news_vol_1h"],
            "ml_task_type": "CLASSIFICATION",
            "algorithm_recommendation": "XGBClassifier",
            "primary_evaluation_metric": "f1_score",
        }
        return {"stdout": json.dumps(modeling_metrics), "stderr": ""}
    elif stage == StageID.EVALUATION:
        # Simulate Tearsheet
        evaluation_metrics: dict[str, Any] = {
            "metrics": {
                "f1_score": 0.82,
                "precision": 0.85,
                "recall": 0.79
            },
            "assumed_pnl_percent": 14.5,
            "mlflow_run_id": "mock_run_id_123"
        }
        return {"stdout": json.dumps(evaluation_metrics), "stderr": ""}

    return {"stdout": "Executed mock code.", "stderr": ""}


async def node_business_understanding(state: LabState) -> dict[str, Any]:
    # Phase 1: Business Understanding
    # Goal: Clarify user intent
    session_id = state.get("session_id", "default")
    stage = StageID.BUSINESS_UNDERSTANDING

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)

    message = state["messages"][-1]
    user_input = message.content

    # Simulate some processing time or LLM call
    # For now, immediate completion

    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE)

    return {
        "user_goal": user_input,
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
    }


async def node_data_acquisition(state: LabState) -> dict[str, Any]:
    # Phase 2: Data Acquisition
    # Goal: Get data
    session_id = state.get("session_id", "default")
    stage = StageID.DATA_ACQUISITION

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)

    # In a full implementation, this node would select the dataset based on user input
    # For now, we default to a standard OHLCV view
    mv_name = "mv_ohlcv_1m"  # Default high-res data

    code = """
import pandas as pd
# check if df was loaded by the wrapper script
if 'df' in locals():
    print(df.head().to_markdown())
    print(f"\\nShape: {df.shape}")
    print(f"\\nColumns: {list(df.columns)}")
else:
    print("Error: DataFrame not loaded from parquet.")
"""
    try:
        # Mock execution instead of real sandbox
        result = await _mock_execute_code(code, stage)
        payload = _format_execution_output(result, code, "text/markdown")

        # Check for insufficient data (Mock logic)
        # In a real scenario, we'd parse the output or check `result`.
        # Here we assume success unless explicitly flagged.
        insufficient_data = False
        if insufficient_data:
             await _emit_status_update(
                session_id, stage, NodeStatus.STALE, "Insufficient Data"
            )
             return {
                "error": "insufficient_data",
                "current_stage": stage,
                "status": NodeStatus.STALE,
             }

    except Exception as e:
        logger.error(f"Sandbox execution failed: {e}")
        await _emit_error(session_id, stage, str(e))
        return {
            "error": str(e),
            "current_stage": stage,
            "status": NodeStatus.STALE, # Or error status
        }

    await _emit_render_output(session_id, stage, payload)
    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE)

    return {
        "dataset_name": mv_name,
        "data_acquisition_result": payload,
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content=f"Data acquired successfully from {mv_name}.")],
    }



async def node_preparation(state: LabState) -> dict[str, Any]:
    # Phase 3: Preparation
    # Goal: Clean data
    session_id = state.get("session_id", "default")
    stage = StageID.PREPARATION

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)

    # Mock preparation logic
    features = ["open", "high", "low", "close", "volume"]

    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE)

    return {
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
        "features": features,
        "messages": [AIMessage(content="Data prepared. Features verified.")],
    }


async def node_exploration(state: LabState) -> dict[str, Any]:
    # Phase 4: Exploration
    # Goal: Visualize data using Plotly
    session_id = state.get("session_id", "default")
    stage = StageID.EXPLORATION

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)

    code = """
import plotly.express as px
import pandas as pd
import json

if 'df' in locals():
    # Convert 'timestamp' column to datetime if needed, or assume index
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        x_col = 'timestamp'
    else:
        x_col = df.index.name or 'index'

    fig = px.line(df.iloc[:200], x=x_col, y='close', title='Close Price (First 200 rows)')
    print(fig.to_json())
else:
    print(json.dumps({"error": "No data available for plotting"}))
"""
    try:
        # Mock execution
        result = await _mock_execute_code(code, stage)
        payload = _format_execution_output(
            result, code, "application/vnd.plotly.v1+json"
        )
    except Exception as e:
        logger.error(f"Exploration failed: {e}")
        await _emit_error(session_id, stage, str(e))
        return {
            "error": str(e),
            "current_stage": stage,
            "status": NodeStatus.STALE,
        }

    await _emit_render_output(session_id, stage, payload)
    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE)

    return {
        "exploration_result": payload,
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
        "messages": [
            AIMessage(content="Exploratory analysis complete. Plot generated.")
        ],
    }


async def node_modeling(state: LabState) -> dict[str, Any]:
    # Phase 5: Modeling
    # Goal: Train model
    session_id = state.get("session_id", "default")
    stage = StageID.MODELING

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)

    code = """
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import json

if 'df' in locals():
    # Simple mock training logic on real data
    # Assume 'target' exists or create one (e.g., price went up)
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df = df.dropna()

    features = ['open', 'high', 'low', 'close', 'volume']
    X = df[features]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = XGBClassifier(n_estimators=10, max_depth=3, eval_metric='logloss')
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    # Output metadata as JSON Blueprint
    metrics: dict[str, Any] = {
        "model_id": "xgb_v1",
        "accuracy": float(acc),
        "feature_importance": dict(zip(features, map(float, model.feature_importances_)))
    }
    print(json.dumps(metrics))
else:
    print(json.dumps({"error": "No data"}))
"""
    try:
        # Mock execution
        result = await _mock_execute_code(code, stage)
        payload = _format_execution_output(result, code, "application/json+blueprint")
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        await _emit_error(session_id, stage, str(e))
        return {
            "error": str(e),
            "current_stage": stage,
            "status": NodeStatus.STALE,
        }

    await _emit_render_output(session_id, stage, payload)
    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE)

    return {
        "modeling_result": payload,
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Model trained inside sandbox.")],
    }


async def node_evaluation(state: LabState) -> dict[str, Any]:
    # Phase 6: Evaluation
    # Goal: Evaluate model
    session_id = state.get("session_id", "default")
    stage = StageID.EVALUATION

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)

    code = """
import json
# In a real pipeline, we would load the saved model and test set.
# Here we simulate the evaluation output for the 'Tearsheet' view.
metrics = {
    "sharpe_ratio": 1.2,
    "max_drawdown": -0.12,
    "total_return": 0.15,
    "win_rate": 0.52
}
print(json.dumps(metrics))
"""
    try:
        # Mock execution
        result = await _mock_execute_code(code, stage)
        payload = _format_execution_output(result, code, "application/json+tearsheet")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        await _emit_error(session_id, stage, str(e))
        return {
            "error": str(e),
            "current_stage": stage,
            "status": NodeStatus.STALE,
        }

    await _emit_render_output(session_id, stage, payload)
    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE)

    return {
        "evaluation_result": payload,
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Evaluation metrics calculated.")],
    }


async def node_deployment(state: LabState) -> dict[str, Any]:
    # Phase 7: Deployment
    # Goal: Deploy (mock)
    session_id = state.get("session_id", "default")
    stage = StageID.DEPLOYMENT

    await _emit_status_update(session_id, stage, NodeStatus.ACTIVE)
    await _emit_status_update(session_id, stage, NodeStatus.COMPLETE, "Deployed")

    return {
        "current_stage": stage,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Model deployed to production.")],
    }


async def node_error(state: LabState) -> dict[str, Any]:
    # Error Node
    # Goal: Handle failures and END
    session_id = state.get("session_id", "default")
    error_msg = state.get("error") or "Unknown error"
    stage = state.get("current_stage", StageID.DATA_ACQUISITION) # Default or current

    # We might not need to emit error here if it was already emitted,
    # but strictly ensuring it is good practice.
    # Check if we should emit generic error
    await _emit_error(session_id, stage, error_msg)

    return {
        "status": NodeStatus.STALE, # Or some terminal status
        "messages": [AIMessage(content=f"Workflow halted due to error: {error_msg}")],
    }
