# Agent Services — Architecture & API Reference

> Auto-generated audit of `backend/app/services/agent/`

---

## Table of Contents

- [Dependency Overview](#dependency-overview)
- [1. Core Orchestration Layer](#1-core-orchestration-layer)
  - [1.1 SessionManager](#11-sessionmanager)
  - [1.2 AgentOrchestrator](#12-agentorchestrator)
  - [1.3 AgentRunner](#13-agentrunner)
  - [1.4 LangGraphWorkflow](#14-langgraphworkflow)
  - [1.5 LabGraph (Phase 2 Graph)](#15-labgraph-phase-2-graph)
- [2. Schema & State Definitions](#2-schema--state-definitions)
  - [2.1 schemas.py — Pydantic Models](#21-schemaspy--pydantic-models)
  - [2.2 lab_schema.py — Lab State & Events](#22-lab_schemapy--lab-state--events)
- [3. Specialized Agents](#3-specialized-agents)
  - [3.1 BaseAgent](#31-baseagent)
  - [3.2 DataRetrievalAgent](#32-dataretrievalagent)
  - [3.3 DataAnalystAgent](#33-dataanalystagent)
  - [3.4 ModelTrainingAgent](#34-modeltrainingagent)
  - [3.5 ModelEvaluatorAgent](#35-modelevaluatoragent)
  - [3.6 ReportingAgent](#36-reportingagent)
- [4. Human-in-the-Loop Nodes](#4-human-in-the-loop-nodes)
  - [4.1 clarification_node](#41-clarification_node)
  - [4.2 choice_presentation_node](#42-choice_presentation_node)
  - [4.3 approval_node](#43-approval_node)
  - [4.4 Lab Nodes (Phase 2)](#44-lab-nodes-phase-2)
- [5. Override Manager](#5-override-manager)
- [6. Supporting Services](#6-supporting-services)
  - [6.1 LLMFactory](#61-llmfactory)
  - [6.2 ArtifactManager](#62-artifactmanager)
  - [6.3 ModelPlaygroundService](#63-modelplaygroundservice)
  - [6.4 ExplainabilityService](#64-explainabilityservice)
  - [6.5 PipelineManager](#65-pipelinemanager)
  - [6.6 SandboxExecutor](#66-sandboxexecutor)
- [7. Tools](#7-tools)
  - [7.1 Data Retrieval Tools](#71-data-retrieval-tools)
  - [7.2 Data Analysis Tools](#72-data-analysis-tools)
  - [7.3 Model Training Tools](#73-model-training-tools)
  - [7.4 Model Evaluation Tools](#74-model-evaluation-tools)
  - [7.5 Reporting Tools](#75-reporting-tools)
  - [7.6 Anomaly Detection](#76-anomaly-detection)
  - [7.7 Signal Query](#77-signal-query)
  - [7.8 Dagger Tool (MLflow + Sandbox)](#78-dagger-tool-mlflow--sandbox)
  - [7.9 Sandbox Orchestrator](#79-sandbox-orchestrator)
  - [7.10 Mock Dagger](#710-mock-dagger)
  - [7.11 Hyperparameter Search (Optuna)](#711-hyperparameter-search-optuna)
- [8. Strategist](#8-strategist)
  - [8.1 StrategyGenerator](#81-strategygenerator)
  - [8.2 GovernanceEvaluator](#82-governanceevaluator)

---

## Dependency Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API / WebSocket Layer                          │
└───────────────┬─────────────────────────────────────────┬──────────────┘
                │                                         │
       ┌────────▼────────┐                      ┌─────────▼─────────┐
       │  AgentRunner     │                      │   lab_graph (app)  │
       │  (background     │                      │   Phase 2 Graph    │
       │   task mgmt)     │                      │   (LabState)       │
       └────────┬─────────┘                      └─────────┬──────────┘
                │                                          │
       ┌────────▼────────┐                        ┌────────▼────────┐
       │ AgentOrchestrator│                        │   Lab Nodes      │
       └────────┬─────────┘                        │ (lab_nodes.py)   │
                │                                  └──────────────────┘
       ┌────────▼────────────────────────┐
       │     LangGraphWorkflow           │
       │  ┌──────────────────────────┐   │
       │  │ StateGraph (AgentState)  │   │
       │  │                          │   │
       │  │  initialize              │   │
       │  │    ↓                     │   │
       │  │  reason ←────────────┐   │   │
       │  │    ↓                 │   │   │
       │  │  retrieve_data       │   │   │        ┌──────────────────┐
       │  │    ↓                 │   │   │        │    LLMFactory    │
       │  │  validate_data       │   │   │◄───────│  (BYOM support)  │
       │  │    ↓                 │   │   │        └──────────────────┘
       │  │  analyze_data        │   │   │
       │  │    ↓                 │   │   │        ┌──────────────────┐
       │  │  train_model         │   │   │◄───────│  SessionManager  │
       │  │    ↓                 │   │   │        │  (Redis + DB)    │
       │  │  evaluate_model      │   │   │        └──────────────────┘
       │  │    ↓                 │   │   │
       │  │  generate_report     │   │   │        ┌──────────────────┐
       │  │    ↓                 │   │   │◄───────│ ArtifactManager  │
       │  │  finalize            │   │   │        └──────────────────┘
       │  │    ↓                 │   │   │
       │  │  dispatch_alerts     │   │   │
       │  │    ↓                 │   │   │
       │  │  handle_error ───────┘   │   │
       │  └──────────────────────────┘   │
       └─────────────────────────────────┘
                │
     ┌──────────┼──────────────────────────────────┐
     │          │          │          │             │
┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼───────┐ ┌───▼──────┐
│DataRetr.│ │DataAna.│ │ModelTr.│ │ModelEval.│ │Reporting │
│Agent   │ │Agent   │ │Agent   │ │Agent     │ │Agent     │
└────┬───┘ └───┬────┘ └───┬────┘ └──┬───────┘ └───┬──────┘
     │         │          │         │              │
┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼───────┐ ┌───▼──────┐
│Retrieval│ │Analysis│ │Training│ │Evaluation│ │Reporting │
│ Tools  │ │ Tools  │ │ Tools  │ │  Tools   │ │ Tools    │
└────────┘ └────────┘ └────────┘ └──────────┘ └──────────┘
```

---

## 1. Core Orchestration Layer

### 1.1 SessionManager

**File:** `session_manager.py`

Manages agent session lifecycle and state persistence using PostgreSQL (sessions) and Redis (ephemeral state).

#### Class: `SessionManager`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | Initialises with `redis_client = None` |
| `async connect()` | — | `None` | Connects to Redis via `settings.REDIS_URL` |
| `async disconnect()` | — | `None` | Closes Redis connection |
| `async create_session(db, user_id, session_data)` | `db: Session`, `user_id: UUID`, `session_data: AgentSessionCreate` | `AgentSession` | Creates a new session row in DB (status=PENDING) |
| `async get_session(db, session_id)` | `db: Session`, `session_id: UUID` | `AgentSession \| None` | Fetches session by ID |
| `async update_session_status(db, session_id, status, error_message?, result_summary?)` | `db: Session`, `session_id: UUID`, `status: str`, `error_message: str \| None`, `result_summary: str \| None` | `None` | Updates session status, timestamps, error/result |
| `async update_status(...)` | *(same as above)* | `None` | Alias for backward compat |
| `async add_message(db, session_id, role, content, agent_name?, metadata?)` | `db: Session`, `session_id: UUID`, `role: str`, `content: str`, `agent_name: str \| None`, `metadata: str \| None` | `AgentSessionMessage` | Appends message to session conversation |
| `async get_session_state(session_id)` | `session_id: UUID` | `dict \| None` | Reads ephemeral state from Redis key `agent:session:{id}:state` |
| `async save_session_state(session_id, state)` | `session_id: UUID`, `state: dict` | `None` | Writes state to Redis with 24h TTL |
| `async delete_session_state(session_id)` | `session_id: UUID` | `None` | Removes state from Redis |

---

### 1.2 AgentOrchestrator

**File:** `orchestrator.py`  
**Depends on:** `SessionManager`, `LangGraphWorkflow`, `LLMFactory`

Top-level coordinator that drives agent sessions through the LangGraph workflow.

#### Class: `AgentOrchestrator`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(session_manager)` | `session_manager: SessionManager` | — | Stores session manager, creates default `LangGraphWorkflow` |
| `async start_session(db, session_id)` | `db: Session`, `session_id: UUID` | `dict` | Sets session to RUNNING, initialises Redis state |
| `async execute_step(db, session_id)` | `db: Session`, `session_id: UUID` | `dict` | Executes one workflow step (creates per-session workflow with BYOM, tracks LLM provider/model) |
| `async cancel_session(db, session_id)` | `db: Session`, `session_id: UUID` | `dict` | Sets status to CANCELLED, cleans up Redis |
| `get_session_state(db_or_session_id, session_id?)` | `db: Session \| UUID`, `session_id: UUID \| None` | `dict \| None` | Sync wrapper for `SessionManager.get_session_state` |
| `update_session_state(session_id, state)` | `session_id: UUID`, `state: dict` | `None` | Sync wrapper for `SessionManager.save_session_state` |
| `async resume_session(db, session_id)` | `db: Session`, `session_id: UUID` | `dict` | Resumes a paused session (after HiTL interaction) |
| `async run_workflow(db, session_id)` | `db: Session`, `session_id: UUID` | `dict` | Runs start + execute in one call (integration tests) |

---

### 1.3 AgentRunner

**File:** `runner.py`  
**Depends on:** `SessionManager`, `AgentOrchestrator`, `LangGraphWorkflow`, `ArtifactManager`

Decouples session execution from HTTP request cycle. Runs sessions as `asyncio.Task`s and publishes state updates to Redis pub/sub for WebSocket relay.

#### Class: `AgentRunner`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | Creates `SessionManager`, `AgentOrchestrator`, task registry |
| `start_session(session_id)` | `session_id: UUID` | `None` | Launches `_run` as background `asyncio.Task` |
| `async _run(session_id)` | `session_id: UUID` | `None` | Orchestrates full workflow: init → stream LangGraph → register artifacts → mark completed. Publishes events to `agent:session:{id}:stream` |
| `async cancel_session(session_id)` | `session_id: UUID` | `bool` | Cancels running task |
| `is_running(session_id)` | `session_id: UUID` | `bool` | Checks if task is active |
| `async shutdown()` | — | `None` | Cancels all tasks, closes Redis |
| `async _publish(redis, channel, data)` | `redis: Redis`, `channel: str`, `data: dict` | `None` | Publishes JSON event to Redis channel |

---

### 1.4 LangGraphWorkflow

**File:** `langgraph_workflow.py`  
**Depends on:** All agents, `LLMFactory`, `AlertService`

Implements the primary LangGraph `StateGraph` with ReAct-style reasoning loop, conditional routing, and error recovery.

#### TypedDict: `AgentState`

Full workflow state including fields for data retrieval, analysis, training, evaluation, reporting, ReAct loop, HiTL, and anomaly detection. Key field groups:

- **Core:** `session_id`, `user_goal`, `status`, `current_step`, `iteration`, `messages`, `result`, `error`
- **Data:** `data_retrieved`, `retrieved_data`, `analysis_results`, `insights`, `retrieval_params`, `analysis_params`
- **ML:** `model_trained`, `model_evaluated`, `trained_models`, `evaluation_results`, `training_params`, `training_summary`, `evaluation_insights`
- **ReAct:** `reasoning_trace`, `decision_history`, `retry_count`, `max_retries`, `skip_analysis`, `skip_training`, `needs_more_data`, `quality_checks`
- **HiTL:** `clarifications_needed`, `awaiting_clarification`, `choices_available`, `awaiting_choice`, `approval_needed`, `pending_approvals`, `approval_mode`, `overrides_applied`
- **Reporting:** `reporting_completed`, `reporting_results`
- **Anomaly:** `anomaly_detected`, `anomaly_summary`, `alert_triggered`, `alert_payload`

#### Class: `LangGraphWorkflow`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(session?, user_id?, credential_id?)` | `session: Session \| None`, `user_id: UUID \| None`, `credential_id: UUID \| None` | — | Builds graph, instantiates all agents, creates LLM via factory (BYOM) |
| `set_session(session)` | `session: Session` | `None` | Sets DB session on self and DataRetrievalAgent |
| `_build_graph()` | — | `StateGraph` | Constructs the full state graph with nodes and conditional edges |
| `async execute(state)` | `state: AgentState` | `AgentState` | Runs compiled graph to completion |
| `async stream_execute(state)` | `state: AgentState` | `AsyncGenerator` | Streams graph execution, yielding per-node state updates |

**Graph Nodes (private async methods):**

| Node | Method | Purpose |
|------|--------|---------|
| `initialize` | `_initialize_node` | Resets flags, initialises ReAct/reporting/anomaly fields |
| `reason` | `_reason_node` | ReAct reasoning — determines next action based on state |
| `retrieve_data` | `_retrieve_data_node` | Delegates to `DataRetrievalAgent.execute()` |
| `validate_data` | `_validate_data_node` | Checks data quality (completeness, record count) |
| `analyze_data` | `_analyze_data_node` | Delegates to `DataAnalystAgent.execute()` |
| `train_model` | `_train_model_node` | Delegates to `ModelTrainingAgent.execute()` |
| `evaluate_model` | `_evaluate_model_node` | Delegates to `ModelEvaluatorAgent.execute()` |
| `generate_report` | `_generate_report_node` | Delegates to `ReportingAgent.execute()` |
| `finalize` | `_finalize_node` | Builds comprehensive result summary |
| `dispatch_alerts` | `_dispatch_alerts_node` | Dispatches anomaly alerts via `AlertService` |
| `handle_error` | `_handle_error_node` | Retry logic with configurable max retries |

**Routing Functions (conditional edges):**

| Function | From Node | Possible Targets |
|----------|-----------|-----------------|
| `_route_after_reasoning` | `reason` | `retrieve`, `analyze`, `train`, `evaluate`, `report`, `finalize`, `error` |
| `_route_after_validation` | `validate_data` | `analyze`, `retry`, `reason`, `error` |
| `_route_after_analysis` | `analyze_data` | `train`, `report`, `finalize`, `reason`, `error` |
| `_route_after_training` | `train_model` | `evaluate`, `reason`, `error` |
| `_route_after_evaluation` | `evaluate_model` | `report`, `retrain`, `reason`, `error` |
| `_route_after_error` | `handle_error` | `retry`, `end` |

**Helper:**

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `_determine_next_action(state)` | `state: AgentState` | `str` | Rule-based reasoning to determine next action |

---

### 1.5 LabGraph (Phase 2 Graph)

**File:** `lab_graph.py`  
**Depends on:** `lab_schema.LabState`, `lab_nodes.*`

Compiles a second LangGraph `StateGraph` for the "Lab" feature following a CRISP-DM pipeline. Uses `MemorySaver` for checkpointing and interrupts before `PREPARATION` and `MODELING` stages for HiTL.

#### Module-Level

| Symbol | Type | Description |
|--------|------|-------------|
| `workflow` | `StateGraph` | The graph builder |
| `checkpointer` | `MemorySaver` | In-memory state checkpointer |
| `app` | Compiled graph | The compiled, runnable `Pregel` graph |

#### Function: `check_data_sufficiency(state: LabState) -> str`
Conditional edge: returns `"ERROR"` if `state["error"]` is truthy, else routes to `PREPARATION`.

**Graph Flow:**
```
START → BUSINESS_UNDERSTANDING → DATA_ACQUISITION
          → [conditional] → PREPARATION → EXPLORATION
          → MODELING → EVALUATION → DEPLOYMENT → END
          → ERROR → END
```

---

## 2. Schema & State Definitions

### 2.1 schemas.py — Pydantic Models

**File:** `schemas.py`

| Class | Fields | Purpose |
|-------|--------|---------|
| `ModelBlueprint` | `target`, `features`, `model_type`, `task_type`, `hyperparameters`, `rationale`, `estimated_training_time?` | Blueprint card for user approval before training |
| `TrainingMetric` | `metric_name`, `metric_value`, `epoch?`, `split` | Structured training metric event |
| `FeatureImportance` | `feature_name`, `importance` | Feature importance from a trained model |
| `PromoteArtifactRequest` | `algorithm_name`, `description`, `position_limit`, `daily_loss_limit`, `execution_frequency` | Request to promote artifact to Floor algorithm |
| `PredictionRequest` | `feature_values`, `include_explanation` | Request to run prediction on saved model |
| `PredictionResponse` | `prediction`, `prediction_label?`, `probabilities?`, `model_type`, `task_type`, `feature_columns_used`, `shap_values?`, `shap_base_value?` | Response from model prediction |
| `ModelInfo` | `artifact_id`, `model_type`, `task_type`, `feature_columns`, `training_metrics?`, `created_at?` | Model metadata for playground UI |
| `ExplanationResponse` | `supported`, `reason?`, `feature_importance?`, `plot_artifact_id?`, `plot_path?`, `model_type`, `shap_base_value?`, `cached` | Response from model explanation |

---

### 2.2 lab_schema.py — Lab State & Events

**File:** `lab_schema.py`

#### Enums

| Enum | Values |
|------|--------|
| `StageID` | `BUSINESS_UNDERSTANDING`, `DATA_ACQUISITION`, `PREPARATION`, `EXPLORATION`, `MODELING`, `EVALUATION`, `DEPLOYMENT` |
| `NodeStatus` | `PENDING`, `ACTIVE`, `COMPLETE`, `STALE`, `RETRYING_OPTIMIZATION` |
| `MimeType` | `TEXT_MARKDOWN`, `PLOTLY_JSON`, `IMAGE_PNG`, `JSON_BLUEPRINT`, `JSON_TEARSHEET` |

#### TypedDicts

| TypedDict | Key Fields |
|-----------|-----------|
| `RenderOutputPayload` | `mime_type`, `content`, `code_snippet`, `hyperparameters` |
| `LabState` | `session_id`, `messages` (with `add_messages` reducer), `current_stage`, `status`, `user_goal`, `dataset_name?`, `features`, `data_acquisition_result?`, `exploration_result?`, `modeling_result?`, `evaluation_result?`, `error?`, `retry_count`, `human_approved` |

#### Pydantic Event Models

| Class | `event_type` | Payload Class |
|-------|-------------|---------------|
| `BaseEvent` | `stream_chat \| status_update \| render_output \| error` | `Any` |
| `StreamChatEvent` | `stream_chat` | `StreamChatPayload(text_delta)` |
| `StatusUpdateEvent` | `status_update` | `StatusUpdatePayload(status, message?)` |
| `RenderOutputEvent` | `render_output` | `RenderOutputPayload` |
| `ErrorEvent` | `error` | `ErrorPayload(message, code, details?)` |

---

## 3. Specialized Agents

All agents reside in `agents/` and inherit from `BaseAgent`.

### 3.1 BaseAgent

**File:** `agents/base.py`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(name, description)` | `name: str`, `description: str` | — | Sets `self.name`, `self.description` |
| `async execute(state)` | `state: dict[str, Any]` | `dict[str, Any]` | Abstract — raises `NotImplementedError` |

---

### 3.2 DataRetrievalAgent

**File:** `agents/data_retrieval.py`  
**Depends on:** `BaseAgent`, tools: `fetch_price_data`, `fetch_sentiment_data`, `fetch_on_chain_metrics`, `fetch_catalyst_events`, `get_available_coins`, `get_data_statistics`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(session?)` | `session: Session \| None` | — | Stores optional DB session |
| `set_session(session)` | `session: Session` | `None` | Sets DB session post-init |
| `async execute(state)` | `state: dict` | `dict` | Parses `user_goal` and `retrieval_params`, fetches price/sentiment/on-chain/catalyst data based on goal keywords. Sets `data_retrieved`, `retrieved_data`, `retrieval_metadata` |

---

### 3.3 DataAnalystAgent

**File:** `agents/data_analyst.py`  
**Depends on:** `BaseAgent`, tools: `calculate_technical_indicators`, `analyze_sentiment_trends`, `analyze_on_chain_signals`, `detect_catalyst_impact`, `detect_price_anomalies`, `perform_eda`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | — |
| `async execute(state)` | `state: dict` | `dict` | Runs EDA, technical indicators, sentiment analysis, on-chain signals, catalyst impact, anomaly detection based on available data and user goal. Sets `analysis_completed`, `analysis_results`, `insights`, `anomaly_detected`, `anomaly_summary` |
| `_generate_insights(analysis_results, user_goal)` | `analysis_results: dict`, `user_goal: str` | `list[str]` | Derives actionable insights from RSI, sentiment, on-chain trends, catalyst impact |

---

### 3.4 ModelTrainingAgent

**File:** `agents/model_training.py`  
**Depends on:** `BaseAgent`, tools: `train_classification_model`, `train_regression_model`, `cross_validate_model`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | — |
| `async execute(state)` | `state: dict` | `dict` | Determines task type (classification/regression), prepares data, trains model, runs optional CV. Sets `model_trained`, `trained_models`, `training_summary` |
| `_determine_task_type(user_goal, training_params)` | `user_goal: str`, `training_params: dict` | `str` | Infers `classification` or `regression` from keywords |
| `_prepare_training_data(analysis_results, state)` | `analysis_results: dict`, `state: dict` | `DataFrame \| None` | Extracts training data from analysis or raw price data |
| `_infer_target_column(task_type)` | `task_type: str` | `str` | Returns `price_direction` or `future_price` |
| `_get_cv_model_type(model_type, task_type)` | `model_type: str`, `task_type: str` | `str` | Maps to sklearn-compatible model type string |
| `_generate_training_summary(model_result, cv_results, task_type)` | `model_result: dict`, `cv_results: dict \| None`, `task_type: str` | `str` | Human-readable summary |

---

### 3.5 ModelEvaluatorAgent

**File:** `agents/model_evaluator.py`  
**Depends on:** `BaseAgent`, tools: `evaluate_model`, `tune_hyperparameters`, `compare_models`, `calculate_feature_importance`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | — |
| `async execute(state)` | `state: dict` | `dict` | Evaluates primary model, calculates feature importance, optionally tunes hyperparameters and compares multiple models. Sets `model_evaluated`, `evaluation_results`, `evaluation_insights` |
| `_get_test_data(state, evaluation_params)` | `state: dict`, `evaluation_params: dict` | `DataFrame \| None` | Extracts test split (last 20%) |
| `_prepare_training_data(state)` | `state: dict` | `DataFrame \| None` | Gets data for HP tuning |
| `_infer_target_column(task_type)` | `task_type: str` | `str` | `price_direction` or `future_price` |
| `_get_tuning_model_type(model_type, task_type)` | `model_type: str`, `task_type: str` | `str` | Maps to sklearn name |
| `_generate_evaluation_insights(evaluation_results, task_type)` | `evaluation_results: dict`, `task_type: str` | `list[str]` | Generates human-readable evaluation insights |

---

### 3.6 ReportingAgent

**File:** `agents/reporting.py`  
**Depends on:** `BaseAgent`, reporting tools: `generate_summary`, `create_comparison_report`, `generate_recommendations`, `create_visualizations`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(artifacts_dir?)` | `artifacts_dir: str` | — | Creates artifact directory |
| `async execute(state)` | `state: dict` | `dict` | Generates summary, comparison report, recommendations, visualisations, complete report markdown. Detects HIGH-severity anomalies for alert bridge. Sets `reporting_results`, `reporting_completed`, `alert_triggered`, `alert_payload` |
| `_create_complete_report(summary, comparison_report, recommendations, visualizations)` | `summary: str`, `comparison_report: str`, `recommendations: list[str]`, `visualizations: dict` | `str` | Assembles full markdown report |

---

## 4. Human-in-the-Loop Nodes

### 4.1 clarification_node

**File:** `nodes/clarification.py`

```python
def clarification_node(state: dict[str, Any]) -> dict[str, Any]
```

Detects ambiguous user goals and generates clarification questions using an LLM (with template fallback). Sets `clarifications_needed`, `awaiting_clarification`.

**Helpers:**

| Function | Args | Returns |
|----------|------|---------|
| `_is_goal_ambiguous(goal)` | `goal: str` | `bool` |
| `_generate_template_questions(goal)` | `goal: str` | `list[str]` |
| `_check_data_quality(retrieved_data)` | `retrieved_data: dict` | `list[str]` |

---

### 4.2 choice_presentation_node

**File:** `nodes/choice_presentation.py`

```python
def choice_presentation_node(state: dict[str, Any]) -> dict[str, Any]
```

Presents trained model choices to the user with pros/cons analysis. Sets `choices_available`, `awaiting_choice`, `recommendation`.

**Helpers:**

| Function | Args | Returns |
|----------|------|---------|
| `_generate_model_choices(trained_models, evaluation_results)` | `dict`, `dict` | `list[dict]` |
| `_estimate_model_complexity(model_name)` | `str` | `str` (`low`/`medium`/`high`) |
| `_generate_pros_cons(model_name, metrics)` | `str`, `dict` | `tuple[list, list]` |
| `_generate_recommendation(choices)` | `list[dict]` | `dict` |

---

### 4.3 approval_node

**File:** `nodes/approval.py`

```python
def approval_node(state: dict[str, Any]) -> dict[str, Any]
```

Configurable approval gates. Deployment **always** requires approval. Sets `approval_needed`, `pending_approvals`.

**Helpers:**

| Function | Args | Returns |
|----------|------|---------|
| `_determine_approval_type(current_step)` | `str` | `str \| None` (`before_data_fetch`, `before_training`, `before_deployment`) |
| `_requires_approval(approval_type, approval_gates, approval_mode)` | `str`, `list`, `str` | `bool` |
| `_create_approval_request(approval_type, state)` | `str`, `dict` | `dict` |
| `_get_planned_data_sources(state)` | `dict` | `list[str]` |
| `_count_data_records(state)` | `dict` | `int` |
| `_get_planned_models(state)` | `dict` | `list[str]` |
| `_get_model_accuracy(state)` | `dict` | `float` |

---

### 4.4 Lab Nodes (Phase 2)

**File:** `nodes/lab_nodes.py`  
**Depends on:** `lab_schema.*`, `websocket_manager`

Async node functions for the Lab (Phase 2) graph. Each emits `status_update`, `render_output`, and `error` WebSocket events.

| Function | Stage | Description |
|----------|-------|-------------|
| `node_business_understanding(state)` | `BUSINESS_UNDERSTANDING` | Extracts user intent from last message |
| `node_data_acquisition(state)` | `DATA_ACQUISITION` | Loads data from materialized view (mock execution) |
| `node_preparation(state)` | `PREPARATION` | Verifies features |
| `node_exploration(state)` | `EXPLORATION` | Generates Plotly visualisation (mock) |
| `node_modeling(state)` | `MODELING` | Trains XGBoost model (mock), outputs blueprint JSON |
| `node_evaluation(state)` | `EVALUATION` | Evaluates model, outputs tearsheet JSON |
| `node_deployment(state)` | `DEPLOYMENT` | Marks deployed |
| `node_error(state)` | *(current)* | Emits error, halts workflow |

**Helpers:**

| Function | Args | Returns |
|----------|------|---------|
| `_format_execution_output(result, code, mime_type)` | `dict`, `str`, `str` | `RenderOutputPayload` |
| `_emit_status_update(session_id, stage, status, message?)` | `str`, `StageID`, `NodeStatus`, `str?` | — |
| `_emit_render_output(session_id, stage, payload)` | `str`, `StageID`, `RenderOutputPayload` | — |
| `_emit_error(session_id, stage, message, code?)` | `str`, `StageID`, `str`, `int?` | — |
| `_mock_execute_code(code, stage)` | `str`, `StageID` | `dict` |

---

## 5. Override Manager

**File:** `override.py`

#### Class: `OverrideManager`

Allows users to override agent decisions at key workflow points.

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | Defines `valid_override_types` |
| `apply_override(state, override_type, override_data)` | `state: dict`, `override_type: str`, `override_data: dict` | `dict` | Validates and applies override, records in `overrides_applied` and `reasoning_trace` |
| `_validate_override(override_type, override_data, state)` | `str`, `dict`, `dict` | `str \| None` | Returns error message or `None` |
| `_apply_model_selection_override(state, override_data)` | `dict`, `dict` | `dict` | Selects a specific trained model |
| `_apply_hyperparameters_override(state, override_data)` | `dict`, `dict` | `dict` | Updates HP, resets `model_trained` |
| `_apply_preprocessing_override(state, override_data)` | `dict`, `dict` | `dict` | Updates preprocessing, resets `analysis_completed` |
| `_apply_workflow_step_override(state, override_data)` | `dict`, `dict` | `dict` | Restarts from given step, resets downstream flags |
| `get_available_override_points(state)` | `state: dict` | `dict[str, bool]` | Returns which overrides are available |

**Valid override types:** `model_selection`, `hyperparameters`, `data_preprocessing`, `workflow_step`

**Module-level:**
- `override_manager` — singleton instance
- `apply_user_override(state, override_type, override_data)` — convenience function

---

## 6. Supporting Services

### 6.1 LLMFactory

**File:** `llm_factory.py`  
**Depends on:** `UserLLMCredentials` model, `encryption_service`

Factory for creating LLM instances. Supports BYOM (Bring Your Own Model) — users can configure their own API keys.

#### Class: `LLMFactory`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `create_llm(session, user_id, credential_id?, prefer_default?)` | `session: Session`, `user_id: UUID`, `credential_id: UUID \| None`, `prefer_default: bool` | LangChain LLM | Main factory method. Priority: credential_id → user default → system default |
| `_create_llm_from_credential(credential)` | `credential: UserLLMCredentials` | LLM | Decrypts API key and delegates |
| `create_llm_from_api_key(provider, api_key, model_name?, **kwargs)` | `provider: str`, `api_key: str`, `model_name: str \| None` | LLM | Direct creation from provider/key |
| `_create_system_default_llm()` | — | LLM | Uses environment config (`settings.LLM_PROVIDER`) |
| `_create_openai_llm(api_key, model_name?, **kwargs)` | `api_key: str`, `model_name: str \| None` | `ChatOpenAI` | — |
| `_create_google_llm(api_key, model_name?, **kwargs)` | `api_key: str`, `model_name: str \| None` | `ChatGoogleGenerativeAI` | — |
| `_create_anthropic_llm(api_key, model_name?, **kwargs)` | `api_key: str`, `model_name: str \| None` | `ChatAnthropic` | — |
| `get_supported_providers()` | — | `list[str]` | `["openai", "google", "anthropic"]` |
| `get_provider_default_models()` | — | `dict[str, str]` | Default model per provider |

**Module-level:** `create_llm(session, user_id, credential_id?, prefer_default?)` — convenience wrapper.

---

### 6.2 ArtifactManager

**File:** `artifacts.py`  
**Depends on:** `AgentArtifact` model

Manages storage, retrieval, and cleanup of agent-generated artifacts on disk and in the database.

#### Class: `ArtifactManager`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(base_dir?)` | `base_dir: str` | — | Creates base directory (default `/tmp/agent_artifacts`) |
| `save_artifact(session_id, artifact_type, name, file_path, description?, metadata?, db_session?)` | `session_id: UUID`, `artifact_type: str`, `name: str`, `file_path: str \| Path`, `description: str \| None`, `metadata: dict \| None`, `db_session: Session \| None` | `AgentArtifact` | Copies file, creates DB record |
| `get_artifact(artifact_id, db_session)` | `artifact_id: UUID`, `db_session: Session` | `AgentArtifact \| None` | Retrieves by ID |
| `list_artifacts(session_id, artifact_type?, db_session?)` | `session_id: UUID`, `artifact_type: str \| None`, `db_session: Session \| None` | `list[AgentArtifact]` | Lists artifacts for a session |
| `delete_artifact(artifact_id, db_session)` | `artifact_id: UUID`, `db_session: Session` | `bool` | Deletes file + DB record |
| `cleanup_session_artifacts(session_id, db_session)` | `session_id: UUID`, `db_session: Session` | `int` | Deletes all artifacts for a session |
| `cleanup_old_artifacts(days?, db_session?)` | `days: int`, `db_session: Session \| None` | `int` | Deletes artifacts older than N days |
| `get_storage_stats(db_session?)` | `db_session: Session \| None` | `dict` | Returns counts/sizes by type and session |
| `export_session_artifacts(session_id, export_dir, db_session)` | `session_id: UUID`, `export_dir: str \| Path`, `db_session: Session` | `Path` | Exports artifacts + metadata.json |
| `_get_mime_type(file_path)` | `file_path: Path` | `str` | Extension-based MIME mapping |

---

### 6.3 ModelPlaygroundService

**File:** `playground.py`  
**Depends on:** `ArtifactManager`, `ExplainabilityService`

Loads saved models and runs predictions, optionally with SHAP explanations.

#### Class: `ModelPlaygroundService`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(base_dir?)` | `base_dir: str` | — | Creates `ArtifactManager` |
| `load_model(artifact_id, db)` | `artifact_id: UUID`, `db: Session` | `tuple[model, scaler, metadata]` | Loads joblib model + optional scaler + JSON metadata |
| `predict(model, scaler, feature_values, metadata)` | `model: Any`, `scaler: Any`, `feature_values: dict[str, float]`, `metadata: dict` | `dict` | Runs prediction, includes probabilities for classifiers |
| `predict_with_explanation(model, scaler, feature_values, metadata)` | *(same)* | `dict` | Prediction + SHAP values |
| `get_model_info(artifact_id, db)` | `artifact_id: UUID`, `db: Session` | `dict` | Returns model metadata for UI |

---

### 6.4 ExplainabilityService

**File:** `explainability.py`  
**Depends on:** `ModelPlaygroundService`, `ArtifactManager`, SHAP library

Computes and caches SHAP explanations for trained models.

#### Class: `ExplainabilityService`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(base_dir?)` | `base_dir: str` | — | — |
| `is_supported(model)` | `model: Any` | `bool` | Checks if model type is explainable (tree/linear, not SVM) |
| `get_explainer_type(model)` | `model: Any` | `str \| None` | Returns `"tree"` or `"linear"` |
| `compute_global_shap(artifact_id, db, max_samples?)` | `artifact_id: Any`, `db: Any`, `max_samples: int` | `dict` | Computes global feature importance with caching |
| `compute_prediction_shap(model, scaler, feature_values, metadata)` | `model: Any`, `scaler: Any`, `feature_values: dict`, `metadata: dict` | `dict \| None` | Computes per-prediction SHAP values |
| `_normalize_shap_values(shap_values)` | `shap_values: Any` | `np.ndarray` | Handles list-of-arrays and 3D arrays |
| `_generate_background_data(metadata, n_samples?)` | `metadata: dict`, `n_samples: int` | `np.ndarray` | Generates synthetic background data |
| `_generate_summary_plot(shap_values, feature_names, save_path)` | `np.ndarray`, `list[str]`, `str` | — | Creates horizontal bar chart of mean |SHAP| |

**Supported models:** `TREE_MODELS` = RF, GBM, DT, XGB; `LINEAR_MODELS` = LR, Ridge, Lasso; `UNSUPPORTED_MODELS` = SVC, SVR

---

### 6.5 PipelineManager

**File:** `pipeline.py`

Exports data from PostgreSQL materialized views to Parquet for Dagger sandbox execution.

#### Class: `PipelineManager`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(session_id)` | `session_id: str` | — | Creates session directory under `/tmp/omc_lab_sessions/` |
| `export_mv_to_parquet(mv_name, limit?)` | `mv_name: str`, `limit: int` | `str` | Queries MV, returns parquet file path |

---

### 6.6 SandboxExecutor

**File:** `execution.py`  
**Depends on:** `DaggerExecutor` (from `app.services.dagger_wrapper`)

Executes Python code inside a Dagger container.

#### Class: `SandboxExecutor`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__()` | — | — | Creates `DaggerExecutor` |
| `async execute_code(code, data_path, output_dir?)` | `code: str`, `data_path: str \| None`, `output_dir: str` | `dict` | Returns `{stdout, stderr, artifact_paths, status, message}` |

---

## 7. Tools

All tools are exposed via `tools/__init__.py`.

### 7.1 Data Retrieval Tools

**File:** `tools/data_retrieval_tools.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `async fetch_price_data(session, coin_type, start_date, end_date?)` | `Session`, `str`, `datetime`, `datetime?` | `list[dict]` | Queries `PriceData5Min` table |
| `async fetch_sentiment_data(session, start_date, end_date?, platform?, currencies?)` | `Session`, `datetime`, `datetime?`, `str?`, `list[str]?` | `dict` | Returns `{news_sentiment, social_sentiment}` from `NewsSentiment` + `SocialSentiment` |
| `async fetch_on_chain_metrics(session, asset, start_date, end_date?, metric_names?)` | `Session`, `str`, `datetime`, `datetime?`, `list[str]?` | `list[dict]` | Queries `OnChainMetrics` |
| `async fetch_catalyst_events(session, start_date, end_date?, event_types?, currencies?)` | `Session`, `datetime`, `datetime?`, `list[str]?`, `list[str]?` | `list[dict]` | Queries `CatalystEvents` |
| `async get_available_coins(session)` | `Session` | `list[str]` | Distinct coin types from price table |
| `async get_data_statistics(session, coin_type?)` | `Session`, `str?` | `dict` | Data coverage statistics |

---

### 7.2 Data Analysis Tools

**File:** `tools/data_analysis_tools.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `calculate_technical_indicators(price_data, indicators?)` | `list[dict]`, `list[str]?` | `DataFrame` | Calculates TA indicators (SMA, EMA, RSI, MACD, BB, etc.) using `ta` library |
| `analyze_sentiment_trends(sentiment_data, time_window?)` | `dict`, `str` | `dict` | Aggregates news + social sentiment scores, determines trend (bullish/bearish/neutral) |
| `analyze_on_chain_signals(on_chain_data, lookback_period?)` | `list[dict]`, `int` | `dict` | Groups by metric, calculates trends and % changes |
| `detect_catalyst_impact(catalyst_events, price_data)` | `list[dict]`, `list[dict]` | `dict` | Measures price change ±1h around each catalyst event |
| `clean_data(data, remove_outliers?, fill_missing?)` | `DataFrame \| list[dict]`, `bool`, `bool` | `DataFrame` | Forward/backward fill + IQR outlier removal |
| `perform_eda(data)` | `DataFrame \| list[dict]` | `dict` | Shape, dtypes, missing values, summary statistics |

---

### 7.3 Model Training Tools

**File:** `tools/model_training_tools.py`

| Function | Key Args | Returns | Description |
|----------|----------|---------|-------------|
| `train_classification_model(training_data, target_column, feature_columns?, model_type?, hyperparameters?, test_size?, scale_features?, validation_strategy?)` | `DataFrame`, `str`, etc. | `dict` with `model`, `scaler`, `feature_columns`, `metrics`, `train_size`, `test_size` | Supports: `random_forest`, `logistic_regression`, `decision_tree`, `gradient_boosting`, `svm`, `xgboost`. Validation: `random`, `time_series`, `expanding_window` |
| `train_regression_model(training_data, target_column, feature_columns?, model_type?, hyperparameters?, test_size?, scale_features?, validation_strategy?)` | *(same)* | `dict` *(same structure)* | Supports: `random_forest`, `linear_regression`, `ridge`, `lasso`, `decision_tree`, `gradient_boosting`, `svr`, `xgboost` |
| `cross_validate_model(training_data, target_column, feature_columns?, model_type?, cv_folds?, scoring?, scale_features?)` | `DataFrame`, `str`, etc. | `dict` with `scores`, `mean_score`, `std_score`, `cv_folds` | Models: `random_forest_classifier`, `random_forest_regressor`, `logistic_regression`, `linear_regression` |

---

### 7.4 Model Evaluation Tools

**File:** `tools/model_evaluation_tools.py`

| Function | Key Args | Returns | Description |
|----------|----------|---------|-------------|
| `evaluate_model(model, test_data, target_column, feature_columns, scaler?, task_type?)` | trained model, `DataFrame`, `str`, `list[str]`, etc. | `dict` with `metrics`, `predictions`, `confusion_matrix?`, `classification_report?` | Classification metrics: accuracy, precision, recall, F1, ROC-AUC. Regression: MSE, RMSE, MAE, R² |
| `tune_hyperparameters(training_data, target_column, feature_columns?, model_type?, param_grid?, search_type?, cv_folds?, n_iter?, scoring?)` | `DataFrame`, `str`, etc. | `dict` with `best_params`, `best_score`, `best_model`, `cv_results` | Grid or random search. Supports `random_forest_classifier`, `random_forest_regressor` |
| `compare_models(models, test_data, target_column, feature_columns, task_type?, primary_metric?)` | `dict[str, dict]`, `DataFrame`, etc. | `dict` with `comparisons`, `best_model`, `rankings` | Evaluates and ranks multiple models |
| `calculate_feature_importance(model, feature_columns, top_n?)` | trained model, `list[str]`, `int` | `dict` with `feature_importances`, `top_features`, `feature_importance_list` | Requires `feature_importances_` attribute |

---

### 7.5 Reporting Tools

**File:** `tools/reporting_tools.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `generate_summary(user_goal, evaluation_results, model_results, analysis_results)` | `str`, `dict`, `dict`, `dict` | `str` (markdown) | Natural language workflow summary |
| `create_comparison_report(evaluation_results, model_results)` | `dict`, `dict` | `str` (markdown) | Model comparison table with metrics |
| `generate_recommendations(user_goal, evaluation_results, model_results, analysis_results)` | `str`, `dict`, `dict`, `dict` | `list[str]` | Actionable recommendations (data quality, model performance, anomalies, next steps) |
| `create_visualizations(evaluation_results, model_results, analysis_results, output_dir)` | `dict`, `dict`, `dict`, `Path` | `list[dict]` | Generates matplotlib/seaborn plots, returns `[{file_path, title}]` |

---

### 7.6 Anomaly Detection

**File:** `tools/anomaly_detection.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `detect_price_anomalies(price_data, contamination?)` | `list[dict]`, `float` | `dict` | Uses `IsolationForest` per coin. Returns `{model, coins_analyzed, total_anomalies, anomalies, severity_distribution, summary}`. Severity levels: LOW (score ≥ -0.7), MEDIUM (-0.9 to -0.7), HIGH (< -0.9) |

---

### 7.7 Signal Query

**File:** `tools/signal_query.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `query_market_signals(coin, hours?)` | `coin: str`, `hours: int` | `dict` | Queries `NewsEnrichment` for sentiment summary: `{coin, total_signals, bullish_count, bearish_count, sentiment_score, avg_confidence, recent_signals}` |

---

### 7.8 Dagger Tool (MLflow + Sandbox)

**File:** `tools/dagger_tool.py`  
**Depends on:** `SandboxExecutor`, `PipelineManager`, MLflow

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `async run_code_in_dagger(session_id, code, mv_name, run_name?)` | `session_id: str`, `code: str`, `mv_name: str`, `run_name: str` | `dict` | Exports MV → parquet, executes code in Dagger sandbox, logs to MLflow (params, metrics, artifacts). Returns `{stdout, stderr, artifact_paths, status}` |

---

### 7.9 Sandbox Orchestrator

**File:** `tools/sandbox.py`  
**Depends on:** `SandboxExecutor`, `PipelineManager`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `async execute_sandbox_code(session_id, code, mv_name?)` | `session_id: str`, `code: str`, `mv_name: str \| None` | `dict` | Lightweight wrapper: optionally exports MV, then executes code |

---

### 7.10 Mock Dagger

**File:** `tools/mock_dagger.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `mock_execute_code(code, execution_type?)` | `code: str`, `execution_type: str` | `dict` | Simulates Dagger output. Types: `data_loading`, `exploration` (Plotly), `modeling` (blueprint), `evaluation` (tearsheet), `general` |

---

### 7.11 Hyperparameter Search (Optuna)

**File:** `tools/hyperparameter_search.py`

| Function | Args | Returns | Description |
|----------|------|---------|-------------|
| `hyperparameter_search(training_data, target_column, model_type, task_type, n_trials?, cv_folds?)` | `DataFrame`, `str`, `str`, `str`, `int`, `int` | `dict` with `best_params`, `best_score`, `n_trials`, `model_type`, `task_type`, `scoring` | Uses Optuna TPE sampler + MedianPruner. Supports `random_forest`, `gradient_boosting`, `xgboost` × classification/regression |

---

## 8. Strategist

### 8.1 StrategyGenerator

**File:** `strategist/generator.py`  
**Depends on:** `LLMFactory`, `BacktestService`

Generates trading strategy parameters from natural language prompts using LLM, then backtests them.

#### Pydantic Model: `StrategyParams`

| Field | Type |
|-------|------|
| `strategy_name` | `str` |
| `fast_window` | `int` |
| `slow_window` | `int` |

#### Class: `StrategyGenerator`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(session, user_id)` | `session: Session`, `user_id: UUID` | — | Creates `BacktestService` and LLM via factory |
| `async generate_and_backtest(prompt, coin_type, start_date, end_date, initial_capital?)` | `prompt: str`, `coin_type: str`, `start_date: datetime`, `end_date: datetime`, `initial_capital: Decimal` | `BacktestResult` | Uses LLM to parse prompt → MA crossover params, validates, runs backtest |

---

### 8.2 GovernanceEvaluator

**File:** `strategist/governance.py`

Evaluates trading strategies against safety "Golden Rules".

#### Pydantic Model: `GovernanceConfig`

| Field | Default | Description |
|-------|---------|-------------|
| `min_sharpe_ratio` | `1.2` | Minimum acceptable Sharpe ratio |
| `max_drawdown_percent` | `0.25` | Maximum acceptable drawdown (25%) |
| `min_win_rate` | `0.40` | Minimum win rate (40%) |
| `min_trades` | `10` | Minimum trades for statistical significance |

#### Pydantic Model: `GovernanceDecision`

| Field | Type |
|-------|------|
| `approved` | `bool` |
| `rejection_reasons` | `list[str]` |
| `score` | `float` |

#### Class: `GovernanceEvaluator`

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `__init__(config?)` | `config: GovernanceConfig \| None` | — | Uses defaults if not provided |
| `evaluate(result)` | `result: BacktestResult` | `GovernanceDecision` | Checks Sharpe, drawdown, win rate, trade count |
