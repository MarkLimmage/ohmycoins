# Agentic Data Science System - Architecture Design

## Overview

This document describes the technical architecture for the multi-agent data science system being added to the Oh My Coins Lab Service. The system enables autonomous algorithm development through a collaborative team of specialized AI agents.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                          │
│                     (Existing Lab Service)                           │
└────────────────┬────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│                   Agent API Routes (/api/v1/lab/agent/*)            │
│  - POST   /sessions           (Create new agent session)            │
│  - GET    /sessions/{id}      (Get session status)                  │
│  - POST   /sessions/{id}/respond (Respond to clarifications)        │
│  - DELETE /sessions/{id}      (Cancel session)                      │
│  - WS     /sessions/{id}/stream (Stream real-time updates)          │
└────────────────┬────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│                       Agent Orchestrator                             │
│  ┌───────────────────────────────────────────────────────┐          │
│  │  LangGraph State Machine                              │          │
│  │  - Manages agent workflow                             │          │
│  │  - Routes between agents                              │          │
│  │  - Handles ReAct loop                                 │          │
│  └───────────────────────────────────────────────────────┘          │
│                                                                      │
│  ┌───────────────────────────────────────────────────────┐          │
│  │  Session Manager                                       │          │
│  │  - Creates/updates agent sessions                     │          │
│  │  - Stores state in Redis                              │          │
│  │  - Manages conversation history                       │          │
│  └───────────────────────────────────────────────────────┘          │
└────────────────┬────────────────────────────────────────────────────┘
                 │
      ┌──────────┼───────────┬──────────────┬──────────────┐
      │          │           │              │              │
┌─────▼───┐ ┌───▼────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
│  Data   │ │  Data  │ │  Model   │ │   Model    │ │ Reporting│
│Retrieval│ │Analyst │ │ Training │ │ Evaluator  │ │  Agent   │
│  Agent  │ │ Agent  │ │  Agent   │ │   Agent    │ │          │
└─────┬───┘ └───┬────┘ └────┬─────┘ └─────┬──────┘ └────┬─────┘
      │         │           │              │              │
┌─────▼─────────▼───────────▼──────────────▼──────────────▼──────┐
│                        Tool Registry                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  Data Tools  │ │Analysis Tools│ │Modeling Tools│           │
│  │              │ │              │ │              │           │
│  │• fetch_data  │ │• calc_tech   │ │• train_model │           │
│  │• get_coins   │ │  _indicators │ │• cross_val   │           │
│  │• get_stats   │ │• clean_data  │ │• evaluate    │           │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘           │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          │  ┌─────────────▼────────────────▼──────────────┐
          │  │      Code Execution Sandbox                  │
          │  │  - RestrictedPython environment              │
          │  │  - Resource limits (CPU, memory, time)       │
          │  │  - Allowed imports only                      │
          │  │  - No network/filesystem access              │
          │  └──────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────────────┐
│                     Data & Storage Layer                            │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │   PostgreSQL     │  │    Redis     │  │  Artifact Store  │    │
│  │                  │  │              │  │                  │    │
│  │• agent_sessions  │  │• Agent state │  │• Trained models  │    │
│  │• session_msgs    │  │• Temp data   │  │• Plots/charts    │    │
│  │• agent_artifacts │  │• Task queue  │  │• Reports         │    │
│  │• price_data_5min │  │              │  │                  │    │
│  └──────────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Agent Orchestrator

**File**: `backend/app/services/agent/orchestrator.py`

**Responsibilities**:
- Receive user goals and preferences
- Initialize agent session
- Create execution plan
- Route tasks to appropriate agents
- Manage ReAct loop
- Handle clarification requests
- Coordinate agent collaboration

**Key Classes**:

```python
class AgentOrchestrator:
    """
    Main orchestrator that coordinates all agents and manages workflow execution.
    """
    
    def __init__(
        self,
        session_manager: SessionManager,
        agents: dict[str, BaseAgent],
        tools: ToolRegistry
    ):
        self.session_manager = session_manager
        self.agents = agents
        self.tools = tools
        self.graph = self._build_graph()
    
    async def start_session(
        self,
        user_id: UUID,
        goal: str,
        preferences: dict
    ) -> AgentSession:
        """Start a new agent session"""
        pass
    
    async def execute_workflow(self, session_id: UUID):
        """Execute the agent workflow using LangGraph"""
        pass
    
    async def handle_user_response(
        self,
        session_id: UUID,
        response: str
    ):
        """Process user response to clarification"""
        pass
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine for agent workflow"""
        pass
```

### 2. Session Manager

**File**: `backend/app/services/agent/session_manager.py`

**Responsibilities**:
- Create and manage agent sessions
- Store session state in Redis
- Maintain conversation history
- Track progress through workflow
- Save final results to database

**Key Classes**:

```python
class SessionManager:
    """
    Manages agent session lifecycle and state persistence.
    """
    
    def __init__(self, redis_client: Redis, db_session: Session):
        self.redis = redis_client
        self.db = db_session
    
    async def create_session(
        self,
        user_id: UUID,
        goal: str,
        preferences: dict
    ) -> AgentSession:
        """Create new agent session"""
        pass
    
    async def get_session(self, session_id: UUID) -> AgentSession:
        """Retrieve session from Redis or database"""
        pass
    
    async def update_session(
        self,
        session_id: UUID,
        updates: dict
    ):
        """Update session state"""
        pass
    
    async def save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: dict = None
    ):
        """Save message to conversation history"""
        pass
    
    async def save_artifact(
        self,
        session_id: UUID,
        artifact_type: str,
        file_path: str,
        metadata: dict = None
    ):
        """Save generated artifact"""
        pass
    
    async def finalize_session(
        self,
        session_id: UUID,
        results: dict
    ):
        """Mark session as complete and save results"""
        pass
```

### 3. Specialized Agents

Each agent is a specialized LangChain agent with specific tools and system prompt.

**Base Agent Class**:

```python
class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(
        self,
        llm: BaseChatModel,
        tools: list[BaseTool],
        system_prompt: str
    ):
        self.llm = llm
        self.tools = tools
        self.system_prompt = system_prompt
        self.agent = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """Create LangChain agent with tools"""
        pass
    
    async def execute(
        self,
        task: str,
        context: dict
    ) -> AgentResult:
        """Execute agent task"""
        pass
```

**Agent Implementations**:

1. **DataRetrievalAgent** (`backend/app/services/agent/agents/data_retrieval.py`)
   - Tools: fetch_price_data, get_available_coins, get_data_statistics
   - System Prompt: "You are a data retrieval specialist..."

2. **DataAnalystAgent** (`backend/app/services/agent/agents/data_analyst.py`)
   - Tools: calculate_technical_indicators, clean_data, create_features, perform_eda
   - System Prompt: "You are a data analyst expert..."

3. **ModelTrainingAgent** (`backend/app/services/agent/agents/model_trainer.py`)
   - Tools: train_classification_model, train_regression_model, cross_validate_model
   - System Prompt: "You are a machine learning engineer..."

4. **ModelEvaluatorAgent** (`backend/app/services/agent/agents/model_evaluator.py`)
   - Tools: evaluate_model, tune_hyperparameters, compare_models, feature_importance
   - System Prompt: "You are a model evaluation specialist..."

5. **ReportingAgent** (`backend/app/services/agent/agents/reporter.py`)
   - Tools: generate_summary, create_comparison_report, generate_recommendations
   - System Prompt: "You are a technical writer who explains ML results..."

### 4. Tool Registry

**File**: `backend/app/services/agent/tools/__init__.py`

**Purpose**: Central registry of all tools available to agents

```python
class ToolRegistry:
    """Registry of all tools available to agents"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.tools = self._register_tools()
    
    def _register_tools(self) -> dict[str, BaseTool]:
        """Register all tools"""
        return {
            # Data tools
            "fetch_price_data": fetch_price_data_tool,
            "get_available_coins": get_available_coins_tool,
            "get_data_statistics": get_data_statistics_tool,
            
            # Analysis tools
            "calculate_technical_indicators": calc_indicators_tool,
            "clean_data": clean_data_tool,
            "create_features": create_features_tool,
            "perform_eda": perform_eda_tool,
            
            # Modeling tools
            "train_classification_model": train_classification_tool,
            "train_regression_model": train_regression_tool,
            "cross_validate_model": cross_validate_tool,
            "evaluate_model": evaluate_model_tool,
            "tune_hyperparameters": tune_hyperparameters_tool,
            "compare_models": compare_models_tool,
            
            # Reporting tools
            "generate_summary": generate_summary_tool,
            "create_comparison_report": create_report_tool,
            "generate_recommendations": generate_recommendations_tool,
        }
    
    def get_tools_for_agent(self, agent_type: str) -> list[BaseTool]:
        """Get tools for specific agent type"""
        pass
```

### 5. Tool Implementations

**Data Tools** (`backend/app/services/agent/tools/data_tools.py`):

```python
from langchain.tools import tool
from datetime import datetime
import pandas as pd

@tool
async def fetch_price_data(
    coin_types: list[str],
    start_date: str,
    end_date: str,
    db_session: Session
) -> dict:
    """
    Fetch historical cryptocurrency price data from the database.
    
    Args:
        coin_types: List of coin symbols (e.g., ['btc', 'eth'])
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        db_session: Database session
    
    Returns:
        Dictionary with 'data' key containing price data as JSON,
        'row_count' and 'date_range'
    """
    # Implementation
    pass

@tool
async def get_available_coins(db_session: Session) -> dict:
    """
    Get list of all cryptocurrencies with available price data.
    
    Returns:
        Dictionary with 'coins' list and 'count'
    """
    pass

@tool
async def get_data_statistics(
    coin_type: str,
    db_session: Session
) -> dict:
    """
    Get statistical summary for a coin's price data.
    
    Returns:
        Dictionary with statistics (mean, std, min, max, count, date_range)
    """
    pass
```

**Analysis Tools** (`backend/app/services/agent/tools/analysis_tools.py`):

```python
@tool
def calculate_technical_indicators(
    data: str,  # JSON string of price data
    indicators: list[str]
) -> dict:
    """
    Calculate technical indicators from price data.
    
    Supported indicators:
    - SMA_N: Simple Moving Average (N periods)
    - EMA_N: Exponential Moving Average
    - RSI_N: Relative Strength Index
    - MACD: Moving Average Convergence Divergence
    - BBANDS: Bollinger Bands
    
    Args:
        data: Price data as JSON string
        indicators: List of indicator names
    
    Returns:
        Dictionary with enhanced data including indicators
    """
    pass

@tool
def clean_data(data: str) -> dict:
    """
    Clean data: handle missing values, remove outliers, fix data types.
    
    Returns:
        Dictionary with cleaned data and statistics on changes made
    """
    pass

@tool
def create_features(
    data: str,
    target_variable: str,
    lookback_period: int = 5
) -> dict:
    """
    Engineer features for model training.
    
    Creates:
    - Lagged features
    - Rolling statistics
    - Price changes and returns
    - Target variable
    
    Returns:
        Dictionary with feature matrix and target vector
    """
    pass
```

**Modeling Tools** (`backend/app/services/agent/tools/modeling_tools.py`):

```python
@tool
def train_classification_model(
    X_train: str,  # JSON
    y_train: str,  # JSON
    model_type: str,
    hyperparameters: dict = None
) -> dict:
    """
    Train a classification model.
    
    Supported models:
    - LogisticRegression
    - RandomForest
    - GradientBoosting
    - XGBoost
    
    Returns:
        Dictionary with model_id, training_time, and initial metrics
    """
    pass

@tool
def evaluate_model(
    model_id: str,
    X_test: str,
    y_test: str
) -> dict:
    """
    Evaluate a trained model on test data.
    
    Returns:
        Dictionary with metrics (accuracy, precision, recall, f1, auc_roc)
    """
    pass

@tool
def tune_hyperparameters(
    model_id: str,
    X_train: str,
    y_train: str,
    param_grid: dict,
    cv: int = 5
) -> dict:
    """
    Perform hyperparameter tuning using GridSearchCV.
    
    Returns:
        Dictionary with tuned_model_id and best_parameters
    """
    pass

@tool
def compare_models(model_ids: list[str], X_test: str, y_test: str) -> dict:
    """
    Compare multiple models side by side.
    
    Returns:
        Dictionary with comparison table and best_model_id
    """
    pass
```

### 6. LangGraph State Machine

**File**: `backend/app/services/agent/graph.py`

The LangGraph state machine defines the workflow:

```python
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    """State maintained throughout agent workflow"""
    session_id: str
    user_id: str
    goal: str
    preferences: dict
    current_step: str
    plan: list[dict]
    context: dict
    data: dict
    models: dict
    results: dict
    requires_clarification: bool
    clarification: dict | None
    error: str | None

def create_agent_graph() -> StateGraph:
    """Create the agent workflow state machine"""
    
    workflow = StateGraph(AgentState)
    
    # Define nodes (states)
    workflow.add_node("planning", planning_node)
    workflow.add_node("data_retrieval", data_retrieval_node)
    workflow.add_node("data_analysis", data_analysis_node)
    workflow.add_node("feature_engineering", feature_engineering_node)
    workflow.add_node("model_training", model_training_node)
    workflow.add_node("model_evaluation", model_evaluation_node)
    workflow.add_node("hyperparameter_tuning", hyperparameter_tuning_node)
    workflow.add_node("reporting", reporting_node)
    workflow.add_node("awaiting_user", awaiting_user_node)
    
    # Define edges (transitions)
    workflow.add_edge("planning", "data_retrieval")
    workflow.add_conditional_edges(
        "data_retrieval",
        should_clarify,
        {
            True: "awaiting_user",
            False: "data_analysis"
        }
    )
    workflow.add_edge("data_analysis", "feature_engineering")
    workflow.add_edge("feature_engineering", "model_training")
    workflow.add_edge("model_training", "model_evaluation")
    workflow.add_conditional_edges(
        "model_evaluation",
        should_tune_or_report,
        {
            "tune": "hyperparameter_tuning",
            "report": "reporting"
        }
    )
    workflow.add_edge("hyperparameter_tuning", "reporting")
    workflow.add_edge("awaiting_user", "data_analysis")  # Continue after clarification
    workflow.add_edge("reporting", END)
    
    # Set entry point
    workflow.set_entry_point("planning")
    
    return workflow.compile()

async def planning_node(state: AgentState) -> AgentState:
    """Generate execution plan"""
    # Use Planner agent to create plan
    pass

async def data_retrieval_node(state: AgentState) -> AgentState:
    """Retrieve data from database"""
    # Use DataRetrieval agent
    pass

# ... other node implementations
```

### 7. Code Execution Sandbox

**File**: `backend/app/services/agent/sandbox.py`

**Purpose**: Safely execute agent-generated code

```python
import ast
import resource
import signal
from contextlib import contextmanager

class CodeSandbox:
    """Secure sandbox for executing agent-generated code"""
    
    ALLOWED_IMPORTS = {
        'pandas', 'numpy', 'sklearn', 'xgboost',
        'matplotlib', 'seaborn', 'ta'
    }
    
    MAX_EXECUTION_TIME = 300  # 5 minutes
    MAX_MEMORY_MB = 2048
    
    def __init__(self):
        self.globals_dict = self._create_safe_globals()
    
    def _create_safe_globals(self) -> dict:
        """Create safe globals with allowed imports"""
        safe_globals = {
            '__builtins__': {
                'range': range,
                'len': len,
                'print': print,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                # ... safe builtins only
            }
        }
        
        # Import allowed libraries
        import pandas as pd
        import numpy as np
        import sklearn
        
        safe_globals['pd'] = pd
        safe_globals['np'] = np
        safe_globals['sklearn'] = sklearn
        
        return safe_globals
    
    def validate_code(self, code: str) -> bool:
        """Validate code before execution"""
        try:
            tree = ast.parse(code)
            # Check for forbidden operations
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    # Validate imports
                    pass
                if isinstance(node, ast.Call):
                    # Check for forbidden function calls
                    pass
            return True
        except SyntaxError:
            return False
    
    @contextmanager
    def resource_limits(self):
        """Set resource limits for execution"""
        # Set CPU time limit
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.MAX_EXECUTION_TIME)
        
        # Set memory limit
        resource.setrlimit(
            resource.RLIMIT_AS,
            (self.MAX_MEMORY_MB * 1024 * 1024, resource.RLIM_INFINITY)
        )
        
        try:
            yield
        finally:
            signal.alarm(0)  # Disable alarm
    
    def execute(self, code: str) -> tuple[Any, str]:
        """Execute code in sandbox"""
        if not self.validate_code(code):
            raise ValueError("Invalid code")
        
        with self.resource_limits():
            try:
                exec(code, self.globals_dict)
                # Get result from globals if any
                result = self.globals_dict.get('result', None)
                return result, ""
            except Exception as e:
                return None, str(e)
    
    @staticmethod
    def _timeout_handler(signum, frame):
        raise TimeoutError("Execution exceeded time limit")
```

### 8. API Routes

**File**: `backend/app/api/routes/agent.py`

```python
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from app.api.deps import get_current_user, get_db
from app.services.agent.orchestrator import AgentOrchestrator
from app.models import User

router = APIRouter()

@router.post("/sessions")
async def create_agent_session(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    goal: str,
    preferences: dict = None
):
    """Create a new agent session"""
    orchestrator = get_orchestrator(db)
    session = await orchestrator.start_session(
        user_id=current_user.id,
        goal=goal,
        preferences=preferences or {}
    )
    return session

@router.get("/sessions/{session_id}")
async def get_agent_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent session status"""
    orchestrator = get_orchestrator(db)
    session = await orchestrator.get_session(session_id)
    
    # Verify user owns this session
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return session

@router.post("/sessions/{session_id}/respond")
async def respond_to_clarification(
    session_id: UUID,
    response: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Respond to agent clarification request"""
    orchestrator = get_orchestrator(db)
    await orchestrator.handle_user_response(session_id, response)
    return {"status": "acknowledged"}

@router.websocket("/sessions/{session_id}/stream")
async def stream_agent_updates(
    websocket: WebSocket,
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Stream real-time agent updates via WebSocket"""
    await websocket.accept()
    
    # Subscribe to session updates from Redis
    # Stream messages to client
    
    try:
        while True:
            # Send updates
            pass
    except Exception as e:
        await websocket.close()

@router.delete("/sessions/{session_id}")
async def cancel_agent_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an agent session"""
    orchestrator = get_orchestrator(db)
    await orchestrator.cancel_session(session_id)
    return {"status": "cancelled"}

@router.get("/sessions/{session_id}/results")
async def get_agent_results(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get final results from completed agent session"""
    orchestrator = get_orchestrator(db)
    results = await orchestrator.get_results(session_id)
    return results
```

## Data Flow

### 1. Session Creation Flow

```
User → POST /api/v1/lab/agent/sessions
  ↓
AgentOrchestrator.start_session()
  ↓
SessionManager.create_session()
  ↓
- Insert record in PostgreSQL (agent_sessions table)
- Initialize state in Redis
- Return session_id to user
```

### 2. Agent Execution Flow

```
AgentOrchestrator.execute_workflow()
  ↓
LangGraph.run(initial_state)
  ↓
[Planning Node]
  - PlannerAgent generates execution plan
  - Update state with plan
  ↓
[Data Retrieval Node]
  - DataRetrievalAgent fetches data
  - Tools: fetch_price_data, get_available_coins
  - Update state with data
  ↓
[Data Analysis Node]
  - DataAnalystAgent analyzes data
  - Tools: calculate_indicators, clean_data, perform_eda
  - Update state with insights
  ↓
[Feature Engineering Node]
  - DataAnalystAgent creates features
  - Tools: create_features
  - Update state with features
  ↓
[Model Training Node]
  - ModelTrainingAgent trains models
  - Tools: train_classification_model, cross_validate
  - Update state with models
  ↓
[Model Evaluation Node]
  - ModelEvaluatorAgent evaluates models
  - Tools: evaluate_model, compare_models
  - Decision: tune best model or proceed to reporting?
  ↓
[Hyperparameter Tuning Node] (if needed)
  - ModelEvaluatorAgent tunes model
  - Tools: tune_hyperparameters
  - Update state with tuned model
  ↓
[Reporting Node]
  - ReportingAgent generates report
  - Tools: generate_summary, create_report
  - Finalize session with results
  ↓
Session Complete
```

### 3. Clarification Flow

```
Agent needs clarification
  ↓
Set state: requires_clarification = True
Set state: clarification = {...}
  ↓
Transition to [Awaiting User Node]
  ↓
Update session status in database
  ↓
User polls GET /sessions/{id}
  ↓
User sees clarification request
  ↓
User responds POST /sessions/{id}/respond
  ↓
Update state with user response
  ↓
Resume workflow from appropriate node
```

## Technology Stack

### Core Framework
- **LangChain**: Agent framework, tool calling
- **LangGraph**: State machine for workflow orchestration
- **OpenAI/Anthropic**: LLM provider

### Data Science
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **scikit-learn**: Machine learning algorithms
- **xgboost**: Gradient boosting
- **matplotlib/seaborn**: Visualization
- **ta**: Technical indicators

### Infrastructure
- **FastAPI**: API framework (existing)
- **PostgreSQL**: Session and artifact storage (existing)
- **Redis**: Agent state and temporary data
- **Celery**: Async task execution (optional)

## Configuration

**Environment Variables** (`.env`):

```bash
# LLM Configuration
LLM_PROVIDER=openai  # or anthropic, azure
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
MAX_TOKENS_PER_REQUEST=4000
ENABLE_STREAMING=true

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Agent Configuration
AGENT_MAX_RETRIES=3
AGENT_TIMEOUT_SECONDS=600
MAX_CONCURRENT_SESSIONS=10

# Sandbox Configuration
SANDBOX_MAX_EXECUTION_TIME=300
SANDBOX_MAX_MEMORY_MB=2048

# Artifact Storage
ARTIFACT_STORAGE_PATH=/app/artifacts
ARTIFACT_MAX_SIZE_MB=100
```

## Security Considerations

### 1. Code Execution
- Sandboxed environment with restricted imports
- Resource limits (CPU, memory, time)
- No network or filesystem access
- Input validation before execution

### 2. API Security
- JWT authentication required
- User can only access own sessions
- Rate limiting per user
- Input validation and sanitization

### 3. LLM Security
- Prompt injection protection
- Output validation
- Token usage limits
- Cost tracking and alerts

### 4. Data Security
- User data isolation
- Encrypted credentials (existing)
- Audit logging of agent actions
- No PII in logs

## Monitoring and Observability

### Metrics to Track
- Agent session creation rate
- Average session duration
- Success/failure rates
- Token usage per session
- Tool execution times
- Error rates by agent type

### Logging
- All agent actions logged
- Tool calls and results
- Clarification requests/responses
- Errors with stack traces
- Performance metrics

### Alerts
- Session failure rate > 10%
- Average session duration > 15 minutes
- Token usage exceeding budget
- Sandbox execution errors
- Database/Redis connectivity issues

## Deployment

### Development
```bash
# Start all services including Redis
docker-compose up -d

# Install agent dependencies
cd backend
uv pip install langchain langchain-openai langgraph pandas scikit-learn xgboost

# Run migrations
uv run alembic upgrade head

# Start backend with agent service
uv run uvicorn app.main:app --reload
```

### Production
- Deploy Redis cluster for high availability
- Use managed LLM API (OpenAI, Anthropic)
- Scale FastAPI workers horizontally
- Use S3 for artifact storage
- Enable CloudWatch monitoring
- Set up alerting via PagerDuty

## Future Enhancements

1. **Advanced Models**: Support for deep learning (PyTorch, TensorFlow)
2. **AutoML**: Automated feature engineering and model selection
3. **Multi-User Collaboration**: Shared agent sessions
4. **Agent Learning**: Learn from past sessions to improve
5. **Custom Agents**: Users can define their own agents
6. **Integration with The Floor**: Auto-deploy best models to trading
7. **Visualization Dashboard**: Real-time agent workflow visualization
8. **Voice Interface**: Natural language voice commands

## Conclusion

This architecture provides a solid foundation for the agentic data science system. The multi-agent design with LangGraph orchestration enables flexible workflows, the tool framework allows easy extension, and the human-in-the-loop features ensure user control while benefiting from AI automation.

The system is designed to integrate seamlessly with the existing Oh My Coins architecture while maintaining security, scalability, and maintainability.
