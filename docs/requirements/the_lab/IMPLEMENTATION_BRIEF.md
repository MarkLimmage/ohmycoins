# 🛠️ Implementation Brief: "The Lab" (Algo Development Module)

**Version:** 1.0
**Context:** This document provides the architectural instructions and data contracts required to build "The Lab." Developers and AI Agents must follow these technical patterns strictly to ensure security, state integrity, and real-time frontend synchronization.

---

## 1. System Architecture Overview

The Lab operates on a decoupled architecture comprising four main layers:

1. **The Orchestrator:** A FastAPI backend wrapping a LangGraph state machine.
2. **The Sandbox:** Ephemeral Dagger containers for executing agent-generated Python.
3. **The Interface:** A Vue.js frontend utilizing WebSockets and Vue Flow for state mapping.
4. **The Tracker:** A local MLflow instance for artifact and metric versioning.

---

## 2. Backend Implementation (FastAPI + LangGraph)

### 2.1 LangGraph State Machine Definition

The orchestration logic must be built using `langgraph`.

* **Graph Nodes:** Define exact nodes for `Business_Understanding`, `Data_Acquisition`, `Preparation`, `Exploration`, `Modeling`, `Evaluation`, and `Deployment`.
* **Graph Edges:** Define conditional edges between nodes. Implement an explicit `interrupt_before` condition prior to the `Modeling` and `Evaluation` nodes to force the "Human-in-the-Loop" approval gate.
* **The "Stale" Mutator:** Implement a state-reducer function. If a payload arrives modifying Node $N$, the reducer must iterate through the `stale_flags` dictionary and set all keys for Nodes > $N$ to `True`.
* **The Self-Healing Edge:** Implement a conditional edge exiting the `Modeling` and `Preparation` nodes. Catch execution exceptions. If the error contains `Exit code 137` (OOM) or a `TimeoutError`, route the graph to a `Remediation` node. This node must append a system prompt to the chat history: "Your code exceeded the 2GB RAM / 300s limit. Optimize your Pandas operations (e.g., use chunking, drop unused columns) and generate a new script."

### 2.2 WebSocket Gateway (`/ws/lab/{session_id}`)

The entire user-to-agent communication layer must bypass standard REST endpoints in favor of a bi-directional WebSocket connection.

* **Connection Manager:** Implement a connection manager in FastAPI to handle active Lab sessions.
* **Async Streaming:** The LangGraph agent must use async streaming (`astream_events`). Standard LLM text tokens must be routed to the `stream_chat` event type, while tool executions must trigger `status_update` events.

### 2.3 The Pre-Training Leakage Validator

Before the graph transitions into `Modeling`, implement a strict Python validation function in the backend (outside the sandbox).

* **Logic:** Load the temporal index of the feature columns and the target variable. Assert that `max(feature_timestamp) < min(target_timestamp)` for every respective row. If `AssertionError` is raised, halt the graph and emit a warning payload to the frontend.

---

## 3. The Execution Engine (Dagger SDK)

The `execute_sandbox_code` tool must be implemented using the `dagger-io` Python SDK.

### 3.1 Container Instantiation
To ensure sub-second startup latency and strict air-gapped security, the sandbox must use the pre-compiled local image rather than dynamically installing heavy ML libraries on every run.

* **Client Connection:** Wrap the execution in an `async with dagger.Connection()` block.
* **Image Definition:** Chain the `.from_("omc-agent-base:latest")` method to load the pre-baked environment. *(Note: Depending on your local Dagger engine configuration, you may need to explicitly load this from the host Docker daemon).*
* **Dependency Setup:** **Do not** chain any `.with_exec(["pip", "install", ...])` commands. All approved libraries (`scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `ta-lib`, `shap`) are already compiled inside the base image. Dynamic package installation by the agent is strictly prohibited.

### 3.2 The Data Mount Pipeline

To ensure air-gapped security, the sandbox must never connect to Postgres.

1. **Extraction:** When the agent requests data, the FastAPI backend must query the `mv_training_set_v1` materialized view via SQLAlchemy.
2. **Serialization:** Use Pandas to save the query result to a local `.parquet` file in a session-specific temporary directory on the host.
3. **Mounting:** Use Dagger's `.with_directory()` method to mount this temporary host directory into the container at `/data`.

### 3.3 Execution and Artifact Retrieval

* Inject the agent's Python code using `.with_new_file("/src/run.py", contents=code)`.
* Execute via `.with_exec(["python", "/src/run.py"])`.
* **Limits:** Apply a 300-second timeout to the `with_exec` call.
* **Retrieval:** Await `.stdout()` for terminal logs. If the script generates models or plots, use `.file("/workspace/out/artifact.ext").export(...)` to pull them back to the host before the container terminates.
* **Exception Handling:** Wrap the `.with_exec()` call in a `try/except` block catching Dagger's `ExecError`. Parse the stderr/exit code specifically to identify resource exhaustion vs. standard Python syntax errors.
---

## 4. Frontend Implementation (Vue.js)

### 4.1 Vue Flow Integration (The State Map)

* Mount a `VueFlow` component fixed at the top of the Lab view.
* Bind the node data to a reactive state object that updates whenever a `status_update` WebSocket payload is received.
* **Styling Contract:** Apply CSS classes dynamically: `node-healthy` (Green) for completed stages, `node-stale` (Amber) for stages requiring re-run, and `node-active` (Blue/Pulsing) for the currently executing node.

### 4.2 The Multi-Modal Cell Component

Create a reusable Vue component (`LabStageRow.vue`) representing a single DSLC stage.

* **Chat Panel:** Bind to the `chat_history` array. Render markdown natively.
* **Code Panel:** Implement a syntax-highlighting code viewer (e.g., using Monaco Editor or PrismJS). Wrap it in an accordion/disclosure widget defaulting to `collapsed=true`.
* **Hyperparameter Overlay:** If the JSON payload contains a `hyperparameters` object, `v-if` render a set of HTML range sliders bound to those values. Emitting a change to a slider must send a re-evaluation request back over the WebSocket.

### 4.3 Result-First Rendering (Output Panel)

* **Plotly:** If the WebSocket payload contains `mime_type: application/vnd.plotly.v1+json`, render it using the `plotly.js` Vue wrapper.
* **Images:** If the payload contains `mime_type: image/png`, render it as an `<img src="data:image/png;base64,...">`.

---

## 5. Integration: MLflow & The Floor

### 5.1 Artifact Logging

* Upon the successful completion of the `Evaluation` stage, the FastAPI backend must utilize the `mlflow` Python client.
* Call `mlflow.start_run()`.
* Log the hyperparameter dictionary using `mlflow.log_params()`.
* Log the F1-Score, RMSE, or other metrics using `mlflow.log_metrics()`.
* Log the Dagger-exported `.pkl` model using `mlflow.sklearn.log_model()` or `mlflow.xgboost.log_model()`.

### 5.2 The Deployment Bridge

When the user clicks "Promote to Floor" in the UI:

1. The frontend sends a REST `POST` to `/api/v1/algorithms/promote`.
2. The backend queries MLflow to retrieve the `run_id` and the artifact URI.
3. The backend inserts a new row into the `Algorithm` database table containing: `name`, `mlflow_run_id`, `signal_type` (from the Blueprint), and `status = 'INACTIVE'`.
4. The backend returns a 201 Created, handing over responsibility to the Live Trading Floor UI.

---

## 6. Critical Data Contracts (JSON Payloads)

To prevent parsing errors between the agent, backend, and frontend, all WebSocket messages from the backend to the frontend must adhere to this structure:

```json
{
  "event_type": "status_update | stream_chat | render_output | error",
  "stage": "MODELING",
  "payload": {
    // For stream_chat
    "text_delta": "...", 
    
    // For status_update
    "status": "STALE",
    
    // For render_output
    "mime_type": "text/markdown | application/vnd.plotly.v1+json | image/png",
    "content": "...",
    "hyperparameters": {"learning_rate": 0.05} // Optional
  }
}

```

---

### 🚀 Next Step

The engineering team now has the structural map they need.

**Would you like me to draft the final `Roadmap_strategy.md` document next?** This will break this massive implementation into logical, executable sprints so the agentic dev team knows exactly which components to build first without creating dependency bottlenecks.