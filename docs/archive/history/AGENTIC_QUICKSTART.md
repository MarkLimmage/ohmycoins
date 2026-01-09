# Agentic Data Science Capability - Quick Start Guide

## Overview

This guide provides a quick reference for implementing autonomous agentic capabilities in the Oh My Coins Lab Service. For detailed information, refer to the comprehensive documents:

- **[AGENTIC_REQUIREMENTS.md](./AGENTIC_REQUIREMENTS.md)** - Complete requirements specification
- **[AGENTIC_ARCHITECTURE.md](./AGENTIC_ARCHITECTURE.md)** - Technical architecture design
- **[AGENTIC_IMPLEMENTATION_PLAN.md](./AGENTIC_IMPLEMENTATION_PLAN.md)** - Week-by-week implementation plan

## What is Being Built?

An autonomous multi-agent system that transforms the Lab from a manual algorithm development platform into an AI-powered "data scientist" that can:

1. **Understand Goals**: Accept natural language trading objectives (e.g., "Predict Bitcoin price movements")
2. **Plan Autonomously**: Break down goals into executable data science workflows
3. **Execute Workflows**: Retrieve data, analyze, engineer features, train models, evaluate
4. **Deliver Results**: Present evaluated models with recommendations
5. **Collaborate with Users**: Ask clarifications, present choices, accept overrides

## Architecture at a Glance

```
User Goal → Agent Orchestrator → Multi-Agent Team → Evaluated Models
                   ↓
              [LangGraph State Machine]
                   ↓
    ┌──────────────┼──────────────┬──────────────┬──────────────┐
    ↓              ↓              ↓              ↓              ↓
Data Retrieval  Data Analyst  Model Trainer  Model Evaluator  Reporter
    Agent          Agent          Agent           Agent        Agent
```

## Five Specialized Agents

### 1. Data Retrieval Agent
- **Purpose**: Fetch cryptocurrency price data from database
- **Tools**: 
  - `fetch_price_data()` - Query price_data_5min table
  - `get_available_coins()` - List available cryptocurrencies
  - `get_data_statistics()` - Get data summary statistics

### 2. Data Analyst Agent
- **Purpose**: Analyze data and engineer features
- **Tools**:
  - `calculate_technical_indicators()` - SMA, EMA, RSI, MACD, Bollinger Bands
  - `clean_data()` - Handle missing values, remove outliers
  - `perform_eda()` - Exploratory data analysis
  - `create_features()` - Feature engineering for ML

### 3. Model Training Agent
- **Purpose**: Train machine learning models
- **Tools**:
  - `train_classification_model()` - Logistic Regression, Random Forest, XGBoost
  - `train_regression_model()` - Linear, Ridge, Lasso, RF Regressor
  - `cross_validate_model()` - K-fold cross-validation

### 4. Model Evaluator Agent
- **Purpose**: Evaluate and optimize models
- **Tools**:
  - `evaluate_model()` - Calculate metrics (accuracy, F1, precision, recall, AUC-ROC)
  - `tune_hyperparameters()` - GridSearchCV, RandomizedSearchCV
  - `compare_models()` - Side-by-side model comparison
  - `calculate_feature_importance()` - Feature importance ranking

### 5. Reporting Agent
- **Purpose**: Summarize findings and make recommendations
- **Tools**:
  - `generate_summary()` - Natural language model summaries
  - `create_comparison_report()` - Model comparison reports
  - `generate_recommendations()` - Actionable recommendations

## Key Features

### 1. ReAct Loop (Reason-Act-Observe)
Iterative refinement through:
- **Reason**: Agent thinks about next step
- **Act**: Agent uses tools to take action
- **Observe**: Agent sees results and adapts
- **Loop**: Continues until goal achieved

Example:
```
Reason: "I need Bitcoin price data"
Act: fetch_price_data(['btc'], '2024-01-01', '2025-11-15')
Observe: "Retrieved 50,000 records"

Reason: "Data looks good, let me calculate technical indicators"
Act: calculate_technical_indicators(data, ['SMA_20', 'RSI', 'MACD'])
Observe: "Features created successfully"

Reason: "Now I can train models"
Act: train_classification_model(X_train, y_train, 'RandomForest')
Observe: "Model trained with 78% accuracy"

... (continues until best model found)
```

### 2. Human-in-the-Loop

**Clarification Requests**:
```
Agent: "What time period should I use for training?"
User: "Last 6 months"
Agent: "Got it, fetching data from 2025-05-15 to 2025-11-15"
```

**Choice Presentation**:
```
Agent: "I've trained two models:
  1. RandomForest - 78% accuracy, faster predictions
  2. XGBoost - 82% accuracy, more accurate but slower
  
Which would you prefer?"
User: "XGBoost for accuracy"
Agent: "Perfect, I'll use XGBoost"
```

**Override Mechanism**:
```
Agent: "I recommend using all available features"
User: "Override: Remove last_price feature due to data leakage"
Agent: "Understood, retraining without last_price"
```

### 3. Secure Code Sandbox
- **Restricted Imports**: Only data science libraries allowed
- **Resource Limits**: 5-minute max execution, 2GB memory
- **No Network Access**: Agent-generated code cannot make external calls
- **Validation**: AST parsing to detect forbidden operations

## API Endpoints

```python
# Create new agent session
POST /api/v1/lab/agent/sessions
{
    "goal": "Predict Bitcoin price movements over the next hour",
    "preferences": {
        "time_period": "last_3_months",
        "model_types": ["classification"],
        "approval_mode": "interactive"
    }
}

# Get session status
GET /api/v1/lab/agent/sessions/{session_id}

# Respond to clarification
POST /api/v1/lab/agent/sessions/{session_id}/respond
{
    "response": "Last 6 months",
    "additional_notes": "Focus on recent market conditions"
}

# Stream real-time updates (WebSocket)
WS /api/v1/lab/agent/sessions/{session_id}/stream

# Cancel session
DELETE /api/v1/lab/agent/sessions/{session_id}

# Get final results
GET /api/v1/lab/agent/sessions/{session_id}/results
```

## Database Schema

Three new tables added:

```sql
-- Agent sessions
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    goal TEXT NOT NULL,
    status VARCHAR(50),  -- 'planning', 'executing', 'completed', 'failed'
    current_step VARCHAR(100),
    plan JSONB,
    context JSONB,
    results JSONB,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Conversation history
CREATE TABLE agent_session_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions(id),
    role VARCHAR(20),  -- 'user', 'assistant', 'tool'
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP
);

-- Generated artifacts
CREATE TABLE agent_artifacts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES agent_sessions(id),
    artifact_type VARCHAR(50),  -- 'model', 'plot', 'report'
    file_path TEXT,
    metadata JSONB,
    created_at TIMESTAMP
);
```

## Technology Stack

### Core Framework
- **LangChain** - Agent framework and tool calling
- **LangGraph** - State machine for workflow orchestration
- **OpenAI/Anthropic** - Large language model provider

### Data Science
- **pandas** - Data manipulation
- **scikit-learn** - Machine learning algorithms
- **xgboost** - Gradient boosting
- **matplotlib/seaborn** - Visualization
- **ta** - Technical indicators

### Infrastructure
- **Redis** - Agent state management
- **PostgreSQL** - Session and artifact storage (existing)
- **FastAPI** - API framework (existing)

## Implementation Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Foundation Setup | Weeks 1-2 | LangChain/LangGraph, Redis, database schema |
| Data Agents | Weeks 3-4 | Data Retrieval + Data Analyst agents |
| Modeling Agents | Weeks 5-6 | Model Training + Model Evaluator agents |
| Orchestration | Weeks 7-8 | LangGraph state machine, ReAct loop |
| Human-in-the-Loop | Weeks 9-10 | Clarifications, overrides, approval gates |
| Reporting | Weeks 11-12 | Reporting agent, artifact management, sandbox |
| Testing & Docs | Weeks 13-14 | Testing, security, documentation |

**Total: 14 weeks (3.5 months)**

## Quick Setup (When Implementation Begins)

### 1. Install Dependencies
```bash
cd backend
uv add langchain langchain-openai langgraph redis pandas scikit-learn xgboost matplotlib seaborn ta
```

### 2. Add Redis to Docker Compose
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
```

### 3. Configure Environment
```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Run Database Migration
```bash
cd backend
uv run alembic upgrade head
```

### 5. Start Services
```bash
docker-compose up -d
cd backend
uv run uvicorn app.main:app --reload
```

## Example Usage

### Simple Example: Predict Bitcoin Price Direction

```python
# User submits goal
response = await client.post(
    "/api/v1/lab/agent/sessions",
    json={
        "goal": "Build a model to predict if Bitcoin price will go up or down in the next hour",
        "preferences": {
            "approval_mode": "automatic"
        }
    }
)
session_id = response.json()["session_id"]

# Agent autonomously:
# 1. Fetches Bitcoin price data
# 2. Calculates technical indicators (SMA, RSI, MACD)
# 3. Engineers features (price changes, rolling stats)
# 4. Trains multiple models (LogisticRegression, RandomForest, XGBoost)
# 5. Evaluates and compares models
# 6. Tunes best model (XGBoost)
# 7. Generates final report

# Get results
results = await client.get(f"/api/v1/lab/agent/sessions/{session_id}/results")
print(results.json())
# {
#     "best_model": {
#         "name": "XGBoost",
#         "accuracy": 0.85,
#         "precision": 0.83,
#         "recall": 0.87,
#         "f1": 0.85
#     },
#     "recommendations": "The XGBoost model achieved 85% accuracy...",
#     "artifacts": {
#         "model_file": "/artifacts/model_xyz.pkl",
#         "feature_importance_plot": "/artifacts/feat_imp.png",
#         "confusion_matrix": "/artifacts/confusion.png"
#     }
# }
```

### Complex Example: Interactive Model Development

```python
# User submits goal with interactive mode
response = await client.post(
    "/api/v1/lab/agent/sessions",
    json={
        "goal": "Create a trading algorithm for Bitcoin",
        "preferences": {
            "approval_mode": "interactive"
        }
    }
)
session_id = response.json()["session_id"]

# Agent asks for clarification
status = await client.get(f"/api/v1/lab/agent/sessions/{session_id}")
print(status.json()["clarification"])
# {
#     "question": "What time period should I use for training?",
#     "options": [
#         "Last 3 months",
#         "Last 6 months", 
#         "All available data"
#     ]
# }

# User responds
await client.post(
    f"/api/v1/lab/agent/sessions/{session_id}/respond",
    json={"response": "Last 6 months"}
)

# Agent continues, presents model choices
status = await client.get(f"/api/v1/lab/agent/sessions/{session_id}")
print(status.json()["clarification"])
# {
#     "question": "I've trained two models. Which would you prefer?",
#     "options": [
#         "RandomForest - 78% accuracy, faster",
#         "XGBoost - 82% accuracy, more accurate"
#     ]
# }

# User chooses
await client.post(
    f"/api/v1/lab/agent/sessions/{session_id}/respond",
    json={"response": "XGBoost - 82% accuracy, more accurate"}
)

# Agent completes workflow with user's choice
```

## Success Metrics

### Functional
- ✅ Accepts natural language goals
- ✅ Autonomously completes data science workflows
- ✅ Trains and evaluates multiple models
- ✅ Presents results with recommendations
- ✅ Supports interactive clarifications and overrides

### Performance
- ✅ Simple tasks complete in < 5 minutes
- ✅ Complex tasks complete in < 15 minutes
- ✅ 90%+ session success rate
- ✅ Supports 10 concurrent sessions

### Quality
- ✅ 80%+ test coverage
- ✅ Zero critical security issues
- ✅ Complete documentation
- ✅ User satisfaction > 4/5

## Next Steps

1. **Review Documents**: Read full requirements and architecture documents
2. **Stakeholder Approval**: Get approval on scope and timeline
3. **Resource Allocation**: Assign developer(s) for 14-week project
4. **Budget Approval**: ~$1,500 for LLM API and infrastructure
5. **Begin Week 1**: Start with foundation setup

## Questions?

Refer to detailed documents:
- **Requirements**: [AGENTIC_REQUIREMENTS.md](./AGENTIC_REQUIREMENTS.md)
- **Architecture**: [AGENTIC_ARCHITECTURE.md](./AGENTIC_ARCHITECTURE.md)
- **Implementation**: [AGENTIC_IMPLEMENTATION_PLAN.md](./AGENTIC_IMPLEMENTATION_PLAN.md)
- **Roadmap**: [ROADMAP.md](./ROADMAP.md) - See Phase 3

## Summary

This agentic capability will transform the Oh My Coins Lab from a manual algorithm development platform into an AI-powered autonomous assistant. Users can describe their trading goals in natural language, and the multi-agent system will autonomously design, execute, and deliver complete data science workflows with minimal human intervention.

The system maintains user control through human-in-the-loop features (clarifications, choice presentation, overrides) while automating the complex and time-consuming aspects of data science and machine learning development.

**Impact**: Dramatically reduces time from idea to deployed trading algorithm while maintaining quality and giving users full transparency and control over the process.
