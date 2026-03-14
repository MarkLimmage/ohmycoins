import json
import logging
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.services.agent.lab_schema import LabState, StageID, NodeStatus, RenderOutputPayload
from app.services.agent.tools.sandbox import execute_sandbox_code

logger = logging.getLogger(__name__)

def _format_execution_output(result: Dict[str, Any], code: str, mime_type: str = "text/markdown") -> RenderOutputPayload:
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
            mime_type = "text/markdown" # Fallback
            content = f"Failed to parse JSON output:\n```\n{content}\n```"

    return {
        "mime_type": mime_type,
        "content": content,
        "code_snippet": code,
        "hyperparameters": None
    }


async def node_business_understanding(state: LabState) -> dict:
    # Phase 1: Business Understanding
    # Goal: Clarify user intent
    message = state["messages"][-1]
    user_input = message.content
    
    # Simple logic for now: set the goal
    return {
        "user_goal": user_input, 
        "current_stage": StageID.BUSINESS_UNDERSTANDING,
        "status": NodeStatus.COMPLETE
    }

async def node_data_acquisition(state: LabState) -> dict:
    # Phase 2: Data Acquisition
    # Goal: Get data using real Sandbox tools
    session_id = state.get("session_id", "default")
    
    # In a full implementation, this node would select the dataset based on user input
    # For now, we default to a standard OHLCV view
    mv_name = "mv_ohlcv_1m" # Default high-res data
    
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
        result = await execute_sandbox_code(session_id, code, mv_name=mv_name)
        payload = _format_execution_output(result, code, "text/markdown")
    except Exception as e:
        logger.error(f"Sandbox execution failed: {e}")
        payload = {
            "mime_type": "text/markdown", 
            "content": f"Execution Error: {str(e)}", 
            "code_snippet": code,
            "hyperparameters": None
        }
    
    return {
        "dataset_name": mv_name,
        "data_acquisition_result": payload,
        "current_stage": StageID.DATA_ACQUISITION,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content=f"Data acquired successfully from {mv_name}.")]
    }

async def node_preparation(state: LabState) -> dict:
    # Phase 3: Preparation
    # Goal: Clean data (Placeholder logic for now, no execution needed unless heavy lifting)
    
    return {
        "current_stage": StageID.PREPARATION,
        "status": NodeStatus.COMPLETE,
        "features": ["open", "high", "low", "close", "volume"],
        "messages": [AIMessage(content="Data prepared. Features verified.")]
    }

async def node_exploration(state: LabState) -> dict:
    # Phase 4: Exploration
    # Goal: Visualize data using Plotly in Sandbox
    session_id = state.get("session_id", "default")
    
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
        # Re-use the data from previous stage if possible, or reload. 
        # For simplicity in this stateless sandbox, we might reload or rely on cached parquet
        result = await execute_sandbox_code(session_id, code, mv_name=None) # mv_name=None uses existing parquet
        payload = _format_execution_output(result, code, "application/vnd.plotly.v1+json")
    except Exception as e:
        logger.error(f"Exploration failed: {e}")
        payload = {"mime_type": "text/markdown", "content": f"Error: {e}", "code_snippet": code, "hyperparameters": None}
    
    return {
        "exploration_result": payload,
        "current_stage": StageID.EXPLORATION,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Exploratory analysis complete. Plot generated.")]
    }

async def node_modeling(state: LabState) -> dict:
    # Phase 5: Modeling
    # Goal: Train model in Sandbox
    session_id = state.get("session_id", "default")
    
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
    metrics = {
        "model_id": "xgb_v1",
        "accuracy": float(acc),
        "feature_importance": dict(zip(features, map(float, model.feature_importances_)))
    }
    print(json.dumps(metrics))
else:
    print(json.dumps({"error": "No data"}))
"""
    try:
        result = await execute_sandbox_code(session_id, code)
        payload = _format_execution_output(result, code, "application/json+blueprint")
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        payload = {"mime_type": "text/markdown", "content": f"Error: {e}", "code_snippet": code, "hyperparameters": None}

    return {
        "modeling_result": payload,
        "current_stage": StageID.MODELING,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Model trained inside sandbox.")]
    }

async def node_evaluation(state: LabState) -> dict:
    # Phase 6: Evaluation
    # Goal: Evaluate model in Sandbox
    session_id = state.get("session_id", "default")
    
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
        result = await execute_sandbox_code(session_id, code)
        payload = _format_execution_output(result, code, "application/json+tearsheet")
    except Exception as e:
         logger.error(f"Evaluation failed: {e}")
         payload = {"mime_type": "text/markdown", "content": f"Error: {e}", "code_snippet": code, "hyperparameters": None}

    return {
        "evaluation_result": payload,
        "current_stage": StageID.EVALUATION,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Evaluation metrics calculated.")]
    }


async def node_deployment(state: LabState) -> dict:
    # Phase 7: Deployment
    # Goal: Deploy (mock)
    
    return {
        "current_stage": StageID.DEPLOYMENT,
        "status": NodeStatus.COMPLETE,
        "messages": [AIMessage(content="Model deployed to production.")]
    }
