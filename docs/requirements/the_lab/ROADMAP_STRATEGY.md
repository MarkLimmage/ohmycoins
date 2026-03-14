# 🗺️ Roadmap & Execution Strategy: "The Lab"

**Version:** 1.0
**Context:** This document outlines the strategic implementation phases for "The Lab" (Algo Development Module). Because this system involves stateful AI orchestration, isolated container execution, and real-time WebSockets, **strict adherence to the phase order is mandatory**.

---

## 🧭 Strategy Overview: The "Inside-Out" Approach

The team must build from the core execution engine outward to the user interface.

1. **First:** The Sandbox (Where code runs).
2. **Second:** The Orchestrator (The brain that writes the code).
3. **Third:** The Frontend (The glass through which the user watches the brain).
4. **Fourth:** The Bridge (Connecting the results to the rest of the platform).

---

## 🏁 Phase 0: Infrastructure & Scaffolding

*Establish the local backing services before any application logic is written.*

* **0.1 MLflow Service Setup:** Configure a local MLflow tracking server using the existing Postgres instance as the backend store and a local directory for artifact storage.
* **0.2 Dagger Daemon Verification:** Ensure the Dagger engine is accessible to the FastAPI environment. Define the base `python:3.11-slim` container specification with the strict dependency list (`scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`).
* **0.3 Directory Scaffolding:** Create the session-specific temporary directory structure on the host for Parquet data exports and Dagger artifact retrieval.
* **0.4 Base Image Construction:** Create a `Dockerfile.agent` in the repository root containing the `python:3.11-slim` base and the `RUN pip install` commands for the expanded library list (including `ta-lib` and `shap`). Build and tag this image locally as `omc-agent-base:latest`. This must be completed before Phase 1 begins.
* **Dependencies:** None. This phase blocks all subsequent development.

---

## 🏗️ Phase 1: The "Solid Gate" (Execution & Data Pipeline)

*Build the isolated execution environment and the data ingestion bridge. The LangGraph agent cannot exist until the tools it relies on are built.*

* **1.1 The MV-to-Parquet Pipeline:** Implement the Python logic to query `mv_training_set_v1`, serialize the output to a `.parquet` file in the session's temporary directory, and return the file path.
* **1.2 The Dagger Execution Tool:** Build the Python wrapper that accepts a code string, mounts the `.parquet` file to `/data`, executes the code within the Dagger sandbox, and captures `stdout`/`stderr`.
* **1.3 Artifact Extraction:** Extend the execution tool to retrieve generated `.pkl` models or `.json` Plotly charts from the container's `/workspace/out` directory before container termination.
* **1.4 The Leakage Validator:** Build the standalone Python function that checks for time-series overlap between target variables and features to prevent look-ahead bias.
* **Dependencies:** Blocked by Phase 0. Blocks Phase 2.

---

## 🧠 Phase 2: The Orchestrator (LangGraph & WebSockets)

*Construct the AI state machine and the communication gateway.*

* **2.1 The `DSLCState` Schema:** Define the Pydantic models representing the session state, the chat history, the artifacts dictionary, and the `stale_flags` dictionary.
* **2.2 The Node Graph:** Implement the 7 LangGraph nodes (`Business_Understanding` through `Deployment`). Wire them together with conditional edges, ensuring the `Human_in_the_Loop` interrupts are placed before `Modeling` and `Evaluation`.
* **2.3 The "Stale" Reducer:** Implement the mutator logic that cascades "Stale" flags to downstream nodes if an upstream node is modified.
* **2.4 Tool Binding:** Bind the tools built in Phase 1 (Data Extraction, Code Execution) to the LangGraph agent.
* **2.5 The WebSocket Gateway:** Create the FastAPI WebSocket endpoint. Implement the routing logic that translates LangGraph async streams into standardized JSON payloads (`status_update`, `stream_chat`, `render_output`) for the frontend.
* **Dependencies:** Blocked by Phase 1. Blocks Phase 3.
* **2.6 Self-Healing Logic:** Implement the `Remediation` node and conditional edges for resource optimization retries.
---

## 🖥️ Phase 3: The Interactive Grid (Vue.js Frontend)

*Build the user interface that translates the complex backend state into a cohesive notebook experience.*

* **3.1 The WebSocket Client & State Store:** Implement the Vue composable/store to manage the WebSocket connection and maintain the localized `DSLCState`.
* **3.2 The Vue Flow Header:** Integrate Vue Flow at the top of the interface. Bind node colors/status directly to the `status_update` events from the WebSocket.
* **3.3 The `LabStageRow` Component:** Build the reusable row component containing the Chat dialogue, the collapsible Code accordion, and the Output panel.
* **3.4 Visual Rendering Engine:** Implement the logic in the Output panel to parse and natively render Plotly JSON objects and Base64 images without relying on raw console text.
* **Dependencies:** Blocked by Phase 2. Blocks Phase 4.

---

## 🌉 Phase 4: Tracking & Deployment (The Lab-to-Floor Bridge)

*Finalize the lifecycle by creating the permanent paper trail and the deployment API.*

* **4.1 MLflow Tool Implementation:** Build the backend tool that the agent calls post-evaluation to log hyperparameters, metrics, and the Dagger-exported `.pkl` artifact to the MLflow server.
* **4.2 The Tear Sheet UI:** Update the `Evaluation` stage in the frontend to render the standardized performance card (F1-score, Confusion Matrix) using data returned from the MLflow run.
* **4.3 The "Promote" API:** Build the FastAPI REST endpoint that takes an MLflow `run_id`, verifies its existence, and writes a new, inactive record into the `Algorithm` database table.
* **4.4 Deployment UI Trigger:** Add the "Promote to Floor" button in the final DSLC stage row, wired to the Promote API.
* **Dependencies:** Blocked by Phase 3.

---

## 🛡️ Phase 5: Hardening & UX Polish (The Final 10%)

*Implement the strict constraints and low-code overlays that make the platform safe and user-friendly.*

* **5.1 Air-Gap & Limits Enforcement:** Enforce the 300-second timeout and 2GB RAM limits on the Dagger containers. Ensure internet access is disabled for the `Preparation`, `Exploration`, and `Modeling` sandbox runs.
* **5.2 Hyperparameter UI Overlays:** Implement the logic that detects a `hyperparameters` dictionary in the agent's Blueprint payload and renders HTML range sliders in the Vue frontend. Wire these sliders to send re-evaluation requests via WebSocket.
* **5.3 Graceful Degradation:** Ensure WebSocket disconnects trigger a clear UI warning and implement auto-reconnect logic that fetches the latest graph state upon reconnection.
* **Dependencies:** Blocked by Phase 4.

---

### 📋 Agentic Dev Team Instructions:

1. Do not initiate work on a subsequent phase until the current phase's acceptance criteria (from `User_stories.md`) are demonstrably met and tests are passing.
2. If a roadblock requires a change to the underlying architecture, halt execution and update the `Requirements.md` and `Implementation_brief.md` documents before writing compensatory code.