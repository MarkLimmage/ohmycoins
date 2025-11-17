# LangGraph Foundation - Developer B Implementation

## Overview

This document describes the LangGraph foundation implementation by Developer B as part of the parallel development effort for Phase 3: Agentic Data Science system.

**Timeline:**
- **Week 1-2**: LangGraph foundation with basic workflow
- **Week 3-4**: Enhanced with DataRetrievalAgent tools and new DataAnalystAgent

## Architecture

### Components

1. **LangGraphWorkflow** (`backend/app/services/agent/langgraph_workflow.py`)
   - State machine implementation using LangGraph
   - Coordinates agent execution through defined workflow nodes
   - Supports both synchronous and streaming execution
   - **Week 3-4**: Enhanced with DataAnalystAgent node

2. **AgentOrchestrator** (`backend/app/services/agent/orchestrator.py`)
   - Main entry point for agent system
   - Integrates LangGraph workflow with session management
   - Handles workflow execution and state persistence
   - **Week 3-4**: Added database session management for agents

3. **AgentState** (TypedDict)
   - Defines the state structure passed between workflow nodes
   - Contains session info, user goal, status, messages, and results
   - **Week 3-4**: Added fields for retrieved_data, analysis_results, insights

### Workflow Nodes

**Week 3-4 Enhanced Workflow** consists of four nodes:

1. **initialize**: Sets up initial state and prepares for execution
2. **retrieve_data**: Executes DataRetrievalAgent (enhanced with comprehensive tools)
3. **analyze_data**: Executes DataAnalystAgent (NEW in Week 3-4)
4. **finalize**: Completes workflow and prepares results with insights

### State Flow

**Week 3-4 Enhanced Flow:**
```
START → initialize → retrieve_data → analyze_data → finalize → END
```

**Previous (Week 1-2) Flow:**
```
START → initialize → retrieve_data → finalize → END
```

## Agents and Tools (Week 3-4 Implementation)

### DataRetrievalAgent (Enhanced)

**Location**: `backend/app/services/agent/agents/data_retrieval.py`

Enhanced in Week 3-4 with comprehensive data retrieval capabilities:

**Tools** (`backend/app/services/agent/tools/data_retrieval_tools.py`):
- `fetch_price_data()`: Query price_data_5min table for historical prices
- `fetch_sentiment_data()`: Fetch news and social media sentiment (Phase 2.5)
- `fetch_on_chain_metrics()`: Fetch on-chain metrics like active addresses (Phase 2.5)
- `fetch_catalyst_events()`: Fetch SEC filings, listings, and other catalysts (Phase 2.5)
- `get_available_coins()`: List all available cryptocurrencies
- `get_data_statistics()`: Get data coverage statistics

**Capabilities:**
- Automatically fetches relevant data based on user goal
- Supports custom time ranges (default: 30 days)
- Ready for Phase 2.5 data integration (when Developer A completes collectors)
- Generates comprehensive metadata about retrieved data

### DataAnalystAgent (NEW in Week 3-4)

**Location**: `backend/app/services/agent/agents/data_analyst.py`

Performs comprehensive data analysis and generates actionable insights.

**Tools** (`backend/app/services/agent/tools/data_analysis_tools.py`):
- `calculate_technical_indicators()`: RSI, MACD, SMA, EMA, Bollinger Bands, etc.
- `analyze_sentiment_trends()`: Analyze news and social sentiment patterns
- `analyze_on_chain_signals()`: Detect trends in on-chain metrics
- `detect_catalyst_impact()`: Measure event impact on price movements
- `clean_data()`: Data cleaning and preprocessing
- `perform_eda()`: Exploratory data analysis with summary statistics

**Capabilities:**
- Automatic technical analysis on price data
- Sentiment trend detection (bullish/bearish/neutral)
- On-chain metric correlation analysis
- Catalyst event impact measurement
- Generates human-readable insights

**Example Insights Generated:**
- "RSI is overbought at 75.23, potential sell signal"
- "Overall sentiment is bullish, positive market outlook"
- "active_addresses is increasing by 25.3%"
- "Recent catalyst events had positive impact (avg 3.2% price change)"

## Configuration

### Environment Variables

The LangGraph workflow uses the following configuration from `.env`:

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai              # Options: openai, anthropic, azure, local
OPENAI_API_KEY=                  # Set your OpenAI API key here
OPENAI_MODEL=gpt-4-turbo-preview
MAX_TOKENS_PER_REQUEST=4000
ENABLE_STREAMING=True

# Agent System Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300
AGENT_CODE_EXECUTION_TIMEOUT=60
```

### Redis Configuration

Redis is used for session state management:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Usage

### Basic Workflow Execution

```python
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.session_manager import SessionManager

# Initialize components
session_manager = SessionManager()
await session_manager.connect()

orchestrator = AgentOrchestrator(session_manager)

# Execute workflow for a session
result = await orchestrator.execute_step(db, session_id)
```

### Direct LangGraph Workflow Usage

```python
from app.services.agent.langgraph_workflow import LangGraphWorkflow, AgentState

# Initialize workflow
workflow = LangGraphWorkflow()

# Prepare initial state
initial_state: AgentState = {
    "session_id": "test-session",
    "user_goal": "Analyze Bitcoin trends",
    "status": "running",
    "current_step": "start",
    "iteration": 0,
    "data_retrieved": False,
    "messages": [],
    "result": None,
    "error": None,
}

# Execute
final_state = await workflow.execute(initial_state)

# Stream execution (for real-time updates)
async for state_update in workflow.stream_execute(initial_state):
    print(f"Current step: {state_update.get('current_step')}")
```

## Integration with Existing System

### No Conflicts

The LangGraph implementation:
- ✅ Works within the `backend/app/services/agent/` directory
- ✅ Does not modify collector infrastructure (Developer A's domain)
- ✅ Uses existing database and Redis infrastructure
- ✅ Compatible with existing session management
- ✅ Uses existing agent base classes

### Dependencies

All required dependencies are already in `pyproject.toml`:

```toml
"langchain<1.0.0,>=0.1.0",
"langchain-openai<1.0.0,>=0.0.5",
"langgraph<1.0.0,>=0.0.20",
"redis<6.0.0,>=5.0.0",
```

## Testing

### Unit Tests

Tests are located in `backend/tests/services/agent/test_langgraph_workflow.py`:

- ✅ Workflow initialization
- ✅ Basic workflow execution
- ✅ State progression through nodes
- ✅ Individual node testing
- ✅ Multiple user goal scenarios

### Running Tests

```bash
# Via Docker (when network is available)
docker compose exec backend bash scripts/tests-start.sh

# Via pytest directly
pytest tests/services/agent/test_langgraph_workflow.py -v
```

### Manual Verification

```python
# Import and test basic functionality
from app.services.agent.langgraph_workflow import LangGraphWorkflow

workflow = LangGraphWorkflow()
assert workflow.graph is not None
assert workflow.data_retrieval_agent is not None
```

## Future Enhancements (Week 3-8)

### Week 3-4: Additional Agents
- Integrate DataAnalystAgent
- Add more sophisticated data retrieval tools
- Connect Phase 2.5 data sources

### Week 5-6: Modeling Agents
- Add ModelTrainingAgent
- Add ModelEvaluatorAgent
- Implement model evaluation workflow

### Week 7-8: ReAct Loop
- Implement reasoning loop
- Add tool selection logic
- Enhance orchestration with dynamic agent selection
- Add human-in-the-loop capabilities

## Current State (Week 1-2 Complete)

### ✅ Completed
- [x] LangGraph workflow foundation created
- [x] Basic state machine with three nodes
- [x] Integration with existing orchestrator
- [x] AgentState TypedDict defined
- [x] Unit tests implemented
- [x] Documentation created
- [x] Compatible with existing infrastructure

### 🔄 Placeholder Implementations
- Data retrieval uses existing price data (Phase 2.5 integration pending)
- Workflow completes with placeholder results
- No LLM reasoning yet (API key optional)

### 📋 Next Steps for Other Developers
- **Week 3**: DataRetrievalAgent enhancement (integrate Phase 2.5 data)
- **Week 4**: DataAnalystAgent implementation
- **Week 5-6**: Modeling agents implementation
- **Week 7-8**: ReAct loop and orchestration enhancements

## Parallel Development Coordination

### Developer A (Data Specialist)
- Working on Phase 2.5 data collectors
- No conflicts with agent directory
- Integration point: Week 6-7 (connect Phase 2.5 data to agents)

### Developer B (AI/ML Specialist) - This Implementation
- ✅ Week 1-2: LangGraph foundation COMPLETE
- 📋 Week 3-4: Data agents with stubbed Phase 2.5 tools
- 📋 Week 5-6: Modeling agents
- 📋 Week 7-8: Orchestration & ReAct loop

### Integration Points
- Week 4: Developer A provides Phase 2.5 collectors operational
- Week 6-7: Integration sprint to connect agents with Phase 2.5 data
- Week 12: Final integration testing

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Parallel Development Guide](../../../PARALLEL_DEVELOPMENT_GUIDE.md)
- [Next Steps](../../../NEXT_STEPS.md)
- [Architecture Overview](../../../ARCHITECTURE.md)

---

**Implementation Date**: 2025-11-17  
**Developer**: Developer B (AI/ML Specialist)  
**Status**: Week 1-2 Complete ✅
