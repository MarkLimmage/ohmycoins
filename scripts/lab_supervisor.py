import asyncio
import logging
import json
import random
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# --- CONFIGURATION ---
PORT = 8002
HOST = "0.0.0.0"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupervisorMock")

app = FastAPI(title="OMC Supervisor Mock Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCK DATA GENERATORS ---

STAGES = [
    "BUSINESS_UNDERSTANDING",
    "DATA_ACQUISITION",
    "PREPARATION",
    "EXPLORATION",
    "MODELING",
    "EVALUATION",
    "DEPLOYMENT"
]

def generate_blueprint():
    return {
        "mime_type": "application/json+blueprint",
        "content": {
            "target_variable": "price_change_24h",
            "feature_list": ["volume_24h", "market_cap", "social_dominance", "developer_activity"],
            "ml_task_type": "REGRESSION",
            "algorithm_recommendation": "XGBoost",
            "primary_evaluation_metric": "RMSE",
            "hyperparameters": {
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5
            }
        },
        "code_snippet": "model = XGBRegressor(n_estimators=100, learning_rate=0.1)",
        "hyperparameters": {"n_estimators": 100}
    }

def generate_tearsheet():
    return {
        "mime_type": "application/json+tearsheet",
        "content": {
            "metrics": {
                "f1_score": round(random.uniform(0.7, 0.95), 4),
                "precision": round(random.uniform(0.7, 0.95), 4),
                "recall": round(random.uniform(0.7, 0.95), 4)
            },
            "assumed_pnl_percent": round(random.uniform(5.0, 25.0), 2),
            "mlflow_run_id": str(uuid.uuid4())
        }
    }

def generate_status_update(stage_idx):
    return {
        "event_type": "status_update",
        "stage": STAGES[stage_idx],
        "payload": {
            "status": "ACTIVE",
            "message": f"Processing stage {STAGES[stage_idx]}..."
        }
    }

async def stream_workflow(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to Mock WS")
    
    try:
        # 1. Business Understanding
        await websocket.send_json(generate_status_update(0))
        await asyncio.sleep(1)
        await websocket.send_json({
            "event_type": "stream_chat",
            "stage": STAGES[0],
            "payload": {"text_delta": "Analyzing market requirements and defining objective: Predict 24h volatility."}
        })
        await asyncio.sleep(1)

        # 2. Data Acquisition
        await websocket.send_json(generate_status_update(1))
        await asyncio.sleep(1)
        await websocket.send_json({
            "event_type": "stream_chat",
            "stage": STAGES[1],
            "payload": {"text_delta": "Fetching Glass and Catalyst ledger data..."}
        })
        await asyncio.sleep(1)

        # 3. Preparation & Blueprint
        await websocket.send_json(generate_status_update(2))
        await asyncio.sleep(1)
        blueprint = generate_blueprint()
        await websocket.send_json({
            "event_type": "render_output",
            "stage": STAGES[2],
            "payload": blueprint
        })
        await asyncio.sleep(2)

        # 4. Modeling & Tearsheet
        await websocket.send_json(generate_status_update(4))
        await asyncio.sleep(2)
        tearsheet = generate_tearsheet()
        await websocket.send_json({
            "event_type": "render_output",
            "stage": STAGES[4],
            "payload": tearsheet
        })
        
        # Complete
        await websocket.send_json({
            "event_type": "status_update",
            "stage": STAGES[6],
            "payload": {
                "status": "COMPLETE",
                "message": "Workflow finished."
            }
        })

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            await websocket.send_json({
                "event_type": "error",
                "stage": "UNKNOWN",
                "payload": {"message": str(e)}
            })
        except:
            pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await stream_workflow(websocket)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "supervisor-mock"}

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
