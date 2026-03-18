#!/usr/bin/env python3
"""
Mock WebSocket server for Glass Agent development.
Emits the full v1.3 event sequence for the Scientific Grid.

Usage: python3 mock_ws_v13.py
Listens on ws://localhost:8002/ws/agent/{session_id}/stream
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

try:
    import websockets
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

PORT = 8002
seq = 0


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def evt(event_type: str, stage: str, payload: dict) -> str:
    global seq
    seq += 1
    return json.dumps({
        "event_type": event_type,
        "stage": stage,
        "sequence_id": seq,
        "timestamp": ts(),
        "payload": payload,
    })


PLAN_PAYLOAD = {
    "plan": [
        {
            "stage": "DATA_ACQUISITION",
            "tasks": [
                {"task_id": "fetch_price_data", "label": "Fetch BTC/ETH OHLCV data (30d)"},
                {"task_id": "fetch_sentiment", "label": "Fetch sentiment scores"},
                {"task_id": "fetch_on_chain", "label": "Fetch on-chain metrics"},
            ],
        },
        {
            "stage": "PREPARATION",
            "tasks": [
                {"task_id": "validate_quality", "label": "Run data quality checks"},
                {"task_id": "detect_anomalies", "label": "Detect price anomalies"},
            ],
        },
        {
            "stage": "EXPLORATION",
            "tasks": [
                {"task_id": "compute_indicators", "label": "Calculate technical indicators (RSI, MACD, BB)"},
                {"task_id": "analyze_sentiment", "label": "Analyze sentiment correlation"},
                {"task_id": "perform_eda", "label": "Exploratory data analysis"},
            ],
        },
        {
            "stage": "MODELING",
            "tasks": [
                {"task_id": "train_models", "label": "Train ML models (XGBoost, RandomForest)"},
                {"task_id": "cross_validate", "label": "5-fold cross-validation"},
            ],
        },
        {
            "stage": "EVALUATION",
            "tasks": [
                {"task_id": "eval_metrics", "label": "Compute evaluation metrics"},
                {"task_id": "compare_models", "label": "Compare model performance"},
            ],
        },
        {
            "stage": "DEPLOYMENT",
            "tasks": [
                {"task_id": "gen_report", "label": "Generate final report"},
                {"task_id": "register_artifacts", "label": "Register model artifacts"},
            ],
        },
    ]
}


async def session_handler(websocket):
    """Simulate a full v1.3 session."""
    global seq
    seq = 0

    async def send(msg):
        await websocket.send(msg)
        await asyncio.sleep(0.3)

    async def send_slow(msg):
        await websocket.send(msg)
        await asyncio.sleep(1.5)

    # ── BUSINESS_UNDERSTANDING ──
    await send(evt("status_update", "BUSINESS_UNDERSTANDING", {
        "status": "ACTIVE", "message": "Starting session...",
    }))
    await send(evt("stream_chat", "BUSINESS_UNDERSTANDING", {
        "text_delta": "Hello! I've received your research goal. Let me analyze what you're looking for and propose a plan."
    }))
    await asyncio.sleep(1)
    await send(evt("stream_chat", "BUSINESS_UNDERSTANDING", {
        "text_delta": "Based on your goal 'Analyze BTC price trends over the last 24 hours', here's my interpretation:"
    }))
    await send(evt("action_request", "BUSINESS_UNDERSTANDING", {
        "action_id": "scope_confirmation_v1",
        "description": "Here's my interpretation of your research goal. Please confirm or adjust.",
        "interpretation": {
            "assets": ["BTC"],
            "timeframe": "30d",
            "analysis_type": "trend_analysis",
            "indicators": ["RSI", "MACD", "Bollinger Bands"],
            "modeling_target": "price_direction_1h",
        },
        "questions": [
            "Should I include additional assets (ETH, SOL, etc.)?",
            "Is a 30-day lookback appropriate, or do you need a different window?",
            "Do you want price prediction, anomaly detection, or correlation analysis?",
        ],
        "options": ["CONFIRM_SCOPE", "ADJUST_SCOPE"],
    }))

    # Wait for user response (scope confirmation)
    print("[MOCK] ⏸  Waiting for scope confirmation...")
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=120)
        print(f"[MOCK] Received: {response}")
    except asyncio.TimeoutError:
        print("[MOCK] Timeout, auto-confirming scope")

    # User message echoed back
    await send(evt("user_message", "BUSINESS_UNDERSTANDING", {
        "content": "Yes, but include ETH too. Use 7-day window.",
    }))
    await send(evt("stream_chat", "BUSINESS_UNDERSTANDING", {
        "text_delta": "Got it! I'll analyze BTC and ETH over a 7-day window. Let me set up the research plan."
    }))

    # Plan established
    await send(evt("plan_established", "BUSINESS_UNDERSTANDING", PLAN_PAYLOAD))

    await send(evt("status_update", "BUSINESS_UNDERSTANDING", {
        "status": "COMPLETE", "message": "Scope confirmed, plan established.",
    }))

    # ── DATA_ACQUISITION ──
    await send(evt("status_update", "DATA_ACQUISITION", {
        "status": "ACTIVE", "message": "Starting data retrieval...",
        "task_id": "fetch_price_data",
    }))
    await send(evt("stream_chat", "DATA_ACQUISITION", {
        "text_delta": "Starting data retrieval. Querying 7 days of BTC/USDT and ETH/USDT OHLCV data from the price database..."
    }))
    await send_slow(evt("status_update", "DATA_ACQUISITION", {
        "status": "COMPLETE", "message": "Retrieved 168 hourly BTC candles and 168 ETH candles.",
        "task_id": "fetch_price_data",
    }))
    await send(evt("status_update", "DATA_ACQUISITION", {
        "status": "ACTIVE", "message": "Fetching sentiment scores...",
        "task_id": "fetch_sentiment",
    }))
    await send(evt("stream_chat", "DATA_ACQUISITION", {
        "text_delta": "Price data looks good — 168 hourly candles for each asset. Now fetching sentiment from 3 data sources..."
    }))
    await send_slow(evt("status_update", "DATA_ACQUISITION", {
        "status": "COMPLETE", "message": "Sentiment data retrieved (428 records).",
        "task_id": "fetch_sentiment",
    }))
    await send(evt("status_update", "DATA_ACQUISITION", {
        "status": "ACTIVE", "message": "Fetching on-chain metrics...",
        "task_id": "fetch_on_chain",
    }))
    await send_slow(evt("status_update", "DATA_ACQUISITION", {
        "status": "COMPLETE", "message": "On-chain metrics retrieved.",
        "task_id": "fetch_on_chain",
    }))
    await send(evt("render_output", "DATA_ACQUISITION", {
        "mime_type": "text/markdown",
        "content": "## Data Retrieval Summary\n\n| Dataset | Records | Range |\n|---|---|---|\n| BTC OHLCV | 168 | 7d hourly |\n| ETH OHLCV | 168 | 7d hourly |\n| Sentiment | 428 | 7d |\n| On-Chain | 84 | 7d |",
    }))
    await send(evt("status_update", "DATA_ACQUISITION", {
        "status": "COMPLETE", "message": "Data acquisition complete.",
    }))

    # ── PREPARATION ──
    await send(evt("status_update", "PREPARATION", {
        "status": "ACTIVE", "message": "Running data quality checks...",
        "task_id": "validate_quality",
    }))
    await send(evt("stream_chat", "PREPARATION", {
        "text_delta": "Running quality checks — testing for completeness, variance, and outliers across all datasets..."
    }))
    await send_slow(evt("status_update", "PREPARATION", {
        "status": "COMPLETE", "message": "Data quality: GOOD. No zero-variance features, 99.4% completeness.",
        "task_id": "validate_quality",
    }))
    await send(evt("status_update", "PREPARATION", {
        "status": "ACTIVE", "message": "Detecting price anomalies...",
        "task_id": "detect_anomalies",
    }))
    await send_slow(evt("status_update", "PREPARATION", {
        "status": "COMPLETE", "message": "Found 2 minor anomalies (Z-score < 3.0). Safe to proceed.",
        "task_id": "detect_anomalies",
    }))
    await send(evt("status_update", "PREPARATION", {
        "status": "COMPLETE", "message": "Preparation complete.",
    }))

    # ── EXPLORATION ──
    await send(evt("status_update", "EXPLORATION", {
        "status": "ACTIVE", "message": "Calculating technical indicators...",
        "task_id": "compute_indicators",
    }))
    await send(evt("stream_chat", "EXPLORATION", {
        "text_delta": "Computing RSI(14), MACD(12,26,9), and Bollinger Bands(20,2) for both BTC and ETH. Initial scan shows BTC RSI at 72 — overbought territory."
    }))
    await send_slow(evt("status_update", "EXPLORATION", {
        "status": "COMPLETE", "message": "Technical indicators computed. RSI: 72 (BTC), 58 (ETH).",
        "task_id": "compute_indicators",
    }))
    await send(evt("status_update", "EXPLORATION", {
        "status": "ACTIVE", "message": "Analyzing sentiment correlation...",
        "task_id": "analyze_sentiment",
    }))
    await send_slow(evt("status_update", "EXPLORATION", {
        "status": "COMPLETE", "message": "Sentiment-price correlation: BTC r=0.42, ETH r=0.31.",
        "task_id": "analyze_sentiment",
    }))
    await send(evt("status_update", "EXPLORATION", {
        "status": "ACTIVE", "message": "Running EDA...",
        "task_id": "perform_eda",
    }))
    await send_slow(evt("status_update", "EXPLORATION", {
        "status": "COMPLETE", "message": "EDA complete. Key finding: BTC/ETH correlation at 0.87.",
        "task_id": "perform_eda",
    }))
    await send(evt("stream_chat", "EXPLORATION", {
        "text_delta": "Analysis complete. Key insights:\n1. BTC RSI at 72 suggests overbought conditions\n2. Strong BTC/ETH correlation (0.87) means ETH likely follows BTC moves\n3. Positive sentiment-price correlation supports momentum trading\n\nI'll proceed to model training with these features."
    }))
    await send(evt("render_output", "EXPLORATION", {
        "mime_type": "text/markdown",
        "content": "## Analysis Summary\n\n### Technical Indicators\n- **BTC RSI(14):** 72 (overbought)\n- **ETH RSI(14):** 58 (neutral)\n- **MACD:** BTC positive cross, ETH flat\n- **Bollinger:** BTC touching upper band\n\n### Correlations\n- BTC/ETH price: 0.87\n- BTC sentiment-price: 0.42\n- ETH sentiment-price: 0.31\n\n### Insights\n1. BTC momentum strong but near reversal zone\n2. ETH lagging — potential catch-up trade\n3. Sentiment supports bullish bias short-term",
    }))
    await send(evt("render_output", "EXPLORATION", {
        "mime_type": "application/vnd.plotly.v1+json",
        "content": {
            "data": [
                {"x": list(range(168)), "y": [42000 + i * 50 + (i % 7) * 100 for i in range(168)], "type": "scatter", "name": "BTC Price", "line": {"color": "#f7931a"}},
                {"x": list(range(168)), "y": [2800 + i * 3 + (i % 5) * 10 for i in range(168)], "type": "scatter", "name": "ETH Price", "yaxis": "y2", "line": {"color": "#627eea"}},
            ],
            "layout": {
                "title": "BTC vs ETH Price (7d Hourly)",
                "yaxis": {"title": "BTC ($)"},
                "yaxis2": {"title": "ETH ($)", "overlaying": "y", "side": "right"},
                "height": 300,
            },
        },
    }))
    await send(evt("status_update", "EXPLORATION", {
        "status": "COMPLETE", "message": "Exploration complete.",
    }))

    # ── MODELING (HITL GATE) ──
    await send(evt("status_update", "MODELING", {
        "status": "ACTIVE", "message": "Preparing model training...",
    }))
    await send(evt("stream_chat", "MODELING", {
        "text_delta": "I'm ready to train models. Here's the proposed configuration — please review before I begin."
    }))
    await send(evt("render_output", "MODELING", {
        "mime_type": "application/json+blueprint",
        "content": {
            "target": "price_direction_1h",
            "features": ["volatility_24h", "rsi_14", "macd_signal", "sentiment_score", "bb_position", "volume_ratio"],
            "model_type": "XGBClassifier",
            "task_type": "CLASSIFICATION",
            "hyperparameters": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
            "rationale": "XGBoost selected for its handling of tabular financial data with mixed feature types.",
            "estimated_training_time": "~15s",
        },
    }))
    await send(evt("action_request", "MODELING", {
        "action_id": "approve_modeling_v1",
        "description": "Please review the feature set and model configuration before training begins.",
        "context": {
            "features": ["volatility_24h", "rsi_14", "macd_signal", "sentiment_score", "bb_position", "volume_ratio"],
            "algorithm": "XGBClassifier",
            "estimated_time": "~15s",
        },
        "options": ["APPROVE", "REJECT", "EDIT_BLUEPRINT"],
    }))

    print("[MOCK] ⏸  Waiting for training approval...")
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=120)
        print(f"[MOCK] Received: {response}")
    except asyncio.TimeoutError:
        print("[MOCK] Timeout, auto-approving")

    await send(evt("stream_chat", "MODELING", {
        "text_delta": "Approved! Training XGBClassifier with 6 features on 336 samples (BTC + ETH). Running 5-fold cross-validation..."
    }))
    await send(evt("status_update", "MODELING", {
        "status": "ACTIVE", "message": "Training XGBClassifier...",
        "task_id": "train_models",
    }))
    await send_slow(evt("status_update", "MODELING", {
        "status": "COMPLETE", "message": "XGBClassifier trained. CV F1: 0.84.",
        "task_id": "train_models",
    }))
    await send(evt("status_update", "MODELING", {
        "status": "ACTIVE", "message": "Cross-validating...",
        "task_id": "cross_validate",
    }))
    await send_slow(evt("status_update", "MODELING", {
        "status": "COMPLETE", "message": "5-fold CV complete. Avg accuracy: 0.85.",
        "task_id": "cross_validate",
    }))
    await send(evt("status_update", "MODELING", {
        "status": "COMPLETE", "message": "Model training complete.",
    }))

    # ── EVALUATION (MODEL SELECTION GATE) ──
    await send(evt("status_update", "EVALUATION", {
        "status": "ACTIVE", "message": "Evaluating models...",
        "task_id": "eval_metrics",
    }))
    await send(evt("stream_chat", "EVALUATION", {
        "text_delta": "Running evaluation on held-out test set. Computing accuracy, F1, precision, recall, and ROC-AUC..."
    }))
    await send_slow(evt("status_update", "EVALUATION", {
        "status": "COMPLETE", "message": "Evaluation complete.",
        "task_id": "eval_metrics",
    }))
    await send(evt("status_update", "EVALUATION", {
        "status": "ACTIVE", "message": "Comparing model variants...",
        "task_id": "compare_models",
    }))
    await send_slow(evt("status_update", "EVALUATION", {
        "status": "COMPLETE", "message": "Comparison complete.",
        "task_id": "compare_models",
    }))
    await send(evt("render_output", "EVALUATION", {
        "mime_type": "application/json+tearsheet",
        "content": {
            "metrics": {
                "accuracy": 0.85,
                "f1_score": 0.84,
                "precision": 0.82,
                "recall": 0.88,
                "roc_auc": 0.91,
            },
            "assumed_pnl_percent": 14.5,
            "mlflow_run_id": "abc123xyz890",
        },
    }))
    await send(evt("action_request", "EVALUATION", {
        "action_id": "model_selection_v1",
        "description": "I've trained and evaluated the models. Here's the comparison — which should we deploy?",
        "models": [
            {
                "name": "XGBClassifier",
                "accuracy": 0.85,
                "f1_score": 0.84,
                "training_time": 12.5,
                "pros": ["High accuracy (85%)", "Fast training (12.5s)", "Handles feature interactions well"],
                "cons": ["Prone to overfitting on small datasets"],
            },
            {
                "name": "RandomForest",
                "accuracy": 0.82,
                "f1_score": 0.81,
                "training_time": 8.2,
                "pros": ["More robust to overfitting", "Feature importance built-in"],
                "cons": ["Slightly lower accuracy (82%)", "Larger model size"],
            },
        ],
        "recommendation": {
            "model": "XGBClassifier",
            "confidence": 0.9,
            "reasoning": "Best F1 score (0.84) with fast training time. Strong ROC-AUC (0.91) indicates good class separation.",
        },
        "options": ["SELECT_MODEL", "RETRAIN_ALL", "SKIP_MODELING"],
    }))

    print("[MOCK] ⏸  Waiting for model selection...")
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=120)
        print(f"[MOCK] Received: {response}")
    except asyncio.TimeoutError:
        print("[MOCK] Timeout, auto-selecting XGBClassifier")

    await send(evt("stream_chat", "EVALUATION", {
        "text_delta": "XGBClassifier selected. Proceeding to generate the final research report."
    }))
    await send(evt("status_update", "EVALUATION", {
        "status": "COMPLETE", "message": "Model selected: XGBClassifier.",
    }))

    # ── DEPLOYMENT ──
    await send(evt("status_update", "DEPLOYMENT", {
        "status": "ACTIVE", "message": "Generating final report...",
        "task_id": "gen_report",
    }))
    await send(evt("stream_chat", "DEPLOYMENT", {
        "text_delta": "Compiling the final research report with analysis results, model metrics, and deployment recommendations..."
    }))
    await send_slow(evt("status_update", "DEPLOYMENT", {
        "status": "COMPLETE", "message": "Report generated.",
        "task_id": "gen_report",
    }))
    await send(evt("render_output", "DEPLOYMENT", {
        "mime_type": "text/markdown",
        "content": "# Research Report: BTC/ETH Trend Analysis\n\n## Executive Summary\nAnalyzed 7 days of BTC and ETH price data with sentiment and on-chain signals. XGBClassifier achieved 85% accuracy on hourly price direction prediction.\n\n## Key Findings\n1. **BTC overbought** — RSI at 72, touching upper Bollinger Band\n2. **Strong BTC/ETH correlation** (0.87) — ETH follows BTC moves\n3. **Positive sentiment** supports short-term bullish bias\n\n## Model Performance\n- Accuracy: 85% | F1: 0.84 | ROC-AUC: 0.91\n- Estimated PnL: +14.5% annualized\n\n## Recommendations\n1. Deploy model in shadow mode for 1-2 weeks\n2. Set alert at F1 < 0.75 for retraining trigger\n3. Monitor BTC RSI — reversal from overbought could invalidate trend",
    }))
    await send(evt("status_update", "DEPLOYMENT", {
        "status": "ACTIVE", "message": "Registering model artifacts...",
        "task_id": "register_artifacts",
    }))
    await send_slow(evt("status_update", "DEPLOYMENT", {
        "status": "COMPLETE", "message": "Artifacts registered in MLflow.",
        "task_id": "register_artifacts",
    }))

    # Final approval
    await send(evt("action_request", "DEPLOYMENT", {
        "action_id": "approve_finalize_v1",
        "description": "Research complete. Approve to finalize and register all artifacts.",
        "options": ["APPROVE", "REJECT"],
    }))

    print("[MOCK] ⏸  Waiting for final approval...")
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=120)
        print(f"[MOCK] Received: {response}")
    except asyncio.TimeoutError:
        print("[MOCK] Timeout, auto-approving finalize")

    await send(evt("stream_chat", "DEPLOYMENT", {
        "text_delta": "Session finalized! All artifacts registered, report generated. You can promote the model to The Floor from the artifacts panel."
    }))
    await send(evt("status_update", "DEPLOYMENT", {
        "status": "COMPLETE", "message": "Session completed.",
    }))

    print(f"[MOCK] ✅ Session complete. {seq} events emitted.")
    # Keep connection open
    try:
        await websocket.wait_closed()
    except Exception:
        pass


async def handler(websocket, path=""):
    # Accept path like /ws/agent/{session_id}/stream
    print(f"[MOCK] New connection: {path or websocket.path}")
    await session_handler(websocket)


async def main():
    print(f"[MOCK] v1.3 Scientific Grid Mock WS Server on ws://localhost:{PORT}")
    print(f"[MOCK] Connect to: ws://localhost:{PORT}/ws/agent/test-session/stream")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
