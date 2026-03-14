# 📖 User Stories: "The Lab" (Algo Development Module)

**Version:** 1.0
**Context:** This document outlines the Agile User Stories and Acceptance Criteria (AC) for building "The Lab." These stories are grouped by the stages of the Data Science Life Cycle (DSLC) and the core architectural pillars.

**Primary Persona:** * **Algo Architect (User):** A quantitative trader or data scientist who understands trading concepts and high-level ML goals but wants an AI Agent to handle the boilerplate code, data joining, and sandbox orchestration.

---

## Epic 1: Workspace & State Management (The Stateful Grid)

*The user needs a workspace that keeps them oriented within the complex ML lifecycle without overwhelming them with terminal windows.*

### 1.1 The Visual Graph

**As an** Algo Architect,
**I want** to see a visual, linear graph of the DSLC stages at the top of my workspace,
**So that** I instantly know where I am in the process and which steps are healthy, running, or stale.

* **AC 1:** The UI renders a horizontal node graph (e.g., using Vue Flow) displaying all 7 DSLC stages.
* **AC 2:** Nodes change color based on real-time WebSocket events (e.g., Gray = Pending, Blue = Active, Green = Complete, Amber = Stale).

### 1.2 The Multi-Modal Cell

**As an** Algo Architect,
**I want** each stage of the DSLC to be represented as a row containing a Chat interface, a collapsible Code block, and a visual Output area,
**So that** I can converse with the agent, verify its work, and see the results in one unified view.

* **AC 1:** The Chat cell streams text from the LangGraph agent in real-time.
* **AC 2:** The Code cell defaults to a "Collapsed" state to save screen space but can be expanded to view Python/SQL.
* **AC 3:** The Output cell renders rich JSON payloads (like Plotly charts) seamlessly.

### 1.3 The "Stale State" Warning

**As an** Algo Architect,
**I want** downstream stages to automatically flag themselves as "Stale" if I modify an earlier stage,
**So that** I don't accidentally deploy a model that was trained on outdated or mismatched data.

* **AC 1:** If the user edits the code or prompts a change in Stage 2, Stages 3 through 7 immediately turn Amber.
* **AC 2:** The agent pauses execution and prompts the user to re-run the downstream nodes.

---

## Epic 2: Business Understanding (The Blueprint)

*The user defines the goal; the agent translates it into math.*

### 2.1 Natural Language Initiation

**As an** Algo Architect,
**I want** to describe my trading goal in plain English (e.g., "Predict BTC 5% pumps over 48h using news sentiment"),
**So that** the agent can translate my vibe into a strict ML specification.

* **AC 1:** The agent parses the prompt and queries the database schema to verify the required data exists.

### 2.2 The Blueprint Card

**As an** Algo Architect,
**I want** the agent to return a structured "Model Blueprint" rather than immediately writing code,
**So that** I can approve or modify the target variables, features, and chosen algorithm before wasting compute time.

* **AC 1:** The Output cell renders a Blueprint UI card detailing: Target Variable, Feature List, and ML Task Type.
* **AC 2:** The user can add/remove features from the Blueprint via UI toggles before clicking "Approve."

---

## Epic 3: Data Acquisition & Exploration

*The agent retrieves data from the Materialized Views and visualizes its shape.*

### 3.1 Secure Data Ingestion

**As an** Algo Architect,
**I want** the agent to pull data from the Materialized Views into its sandbox without exposing my live database credentials,
**So that** my production trading floor remains secure from rogue agent queries.

* **AC 1:** The backend system automatically executes the MV extraction and mounts a flat `.parquet` file into the Dagger container.
* **AC 2:** The agent code has zero network access to the Postgres DB.

### 3.2 Visual EDA (Exploratory Data Analysis)

**As an** Algo Architect,
**I want** the agent to show me data distributions and correlation matrices instead of printing raw Pandas DataFrames,
**So that** I can quickly assess signal quality and feature validity.

* **AC 1:** The agent generates a correlation heatmap (e.g., Sentiment vs. Forward Returns) and pushes the visual artifact to the UI.
* **AC 2:** The agent provides specific text insights (e.g., "Warning: Volatility feature is highly skewed").

---

## Epic 4: Modeling & The Solid Gate

*The core engine where XGBoost and Scikit-learn do the heavy lifting in total isolation.*

### 4.1 Low-Code Hyperparameter Tuning

**As an** Algo Architect,
**I want** to adjust the model's hyperparameters using UI sliders and inputs,
**So that** I don't have to manually edit the Python dictionary in the agent's code block.

* **AC 1:** When the agent proposes an XGBoost model, the UI overlays inputs for `learning_rate`, `max_depth`, and `n_estimators`.
* **AC 2:** Adjusting these inputs automatically updates the agent's execution context.

### 4.2 Automated Leakage Prevention

**As an** Algo Architect,
**I want** the system to automatically check my dataset for look-ahead bias before training starts,
**So that** I don't waste time evaluating a model that is "cheating" by seeing the future.

* **AC 1:** The LangGraph state machine forces a validation script to run before the `MODELING` stage.
* **AC 2:** If overlapping time-windows (leakage) are detected between targets and features, the run halts and warns the user.

### 4.3 Live Training Feedback

**As an** Algo Architect,
**I want** to see the loss curve updating in real-time while the model trains inside the sandbox,
**So that** I know if the model is converging or if I should kill the run early.

* **AC 1:** The backend streams standard output from the Dagger container to update an SVG line chart in the UI.
* **AC 2:** The user has access to a persistent "Kill Switch" to terminate the Dagger container immediately.

### 4.4 (Agentic Code Optimization):

**As an** Algo Architect,
**I want** the agent to automatically attempt to rewrite its code if it hits a memory or timeout limit,
**So that** I don't have to manually debug Pandas chunking or memory management issues.
* **AC 1:** If the sandbox crashes due to hardware limits, the UI status updates to "Retrying/Optimizing".
* **AC 2:** The agent successfully modifies its code and re-runs without requiring user intervention.
* **AC 3:** If the agent fails after 2 retry attempts, a graceful error is displayed detailing the hardware limit.

---

## Epic 5: Evaluation & MLflow Tracking

*Proving the model works and creating a permanent paper trail.*

### 5.1 The Tear Sheet

**As an** Algo Architect,
**I want** to see a standardized performance report (Tear Sheet) once training is complete,
**So that** I can evaluate the model's out-of-sample accuracy and assumed profitability.

* **AC 1:** The Output cell renders a Tear Sheet containing: F1-Score, Precision/Recall, a Confusion Matrix, and Feature Importance bar charts.

### 5.2 Silent Artifact Logging

**As an** Algo Architect,
**I want** the model artifact, parameters, and metrics to be automatically logged to MLflow,
**So that** I have a versioned, reproducible history of every experiment without writing tracking code.

* **AC 1:** Upon completion of `EVALUATION`, the system pushes the `.pkl` file, the feature list, and the metrics to the local MLflow server.
* **AC 2:** The UI provides a direct hyperlink to the MLflow run for deep inspection.

---

## Epic 6: Deployment (The Bridge)

*Moving the Alpha from the Lab to the live-fire environment.*

### 6.1 Promote to Floor

**As an** Algo Architect,
**I want** a simple button to promote my evaluated model to the live trading platform,
**So that** I can connect it to an execution algorithm without manual file transfers.

* **AC 1:** In the `DEPLOYMENT` stage, a "Promote to Floor" button is enabled.
* **AC 2:** Clicking the button registers the MLflow artifact URI into the `Algorithm` database table.
* **AC 3:** The UI strictly enforces that the deployed model only provides signals (0.0 to 1.0) and does not dictate position sizing or API trade execution.