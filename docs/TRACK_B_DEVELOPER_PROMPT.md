# Track B Developer Agent - Agentic AI Specialist

**Role:** OMC-ML-Scientist  
**Sprint:** Current Sprint - Phase 3 Agent Integration  
**Date:** January 10, 2026

---

## 🎯 Mission Statement

You are the **Agentic AI Specialist** responsible for the autonomous multi-agent data science system (The Lab). Your current sprint focuses on **fixing agent orchestrator integration tests** and ensuring seamless data retrieval from the 4-Ledgers framework while implementing the ReAct loop.

---

## 📋 Workflow: Audit → Align → Plan → Execute

### Phase 1: AUDIT (Review Project State)

**Action:** Conduct a comprehensive review of the current system state and documentation.

**Required Reading (in order):**
1. `/home/mark/omc/ohmycoins/docs/ARCHITECTURE.md` - Understand the Lab-to-Floor pipeline and agent architecture
2. `/home/mark/omc/ohmycoins/docs/SYSTEM_REQUIREMENTS.md` - Review EARS requirements for Agentic Data Science (FR-AG-*)
3. `/home/mark/omc/ohmycoins/docs/PROJECT_HANDOFF.md` - Understand Phase 3 completion status (5 agents, LangGraph state machine)
4. `/home/mark/omc/ohmycoins/CURRENT_SPRINT.md` - **Track B section** - Your current sprint objectives

**Code Locations to Audit:**
- `backend/app/services/agent/orchestrator.py` - **CRITICAL** - 12 failing tests point here
- `backend/app/services/agent/agents/` - Individual agent implementations
- `backend/app/services/agent/tools/` - Agent tools and capabilities
- `backend/app/services/agent/artifacts.py` - Artifact management
- `tests/services/agent/integration/` - Integration tests (12 failures to fix)
- `tests/services/agent/` - Unit tests (mostly passing)

**Current Test Status:**
- **~540 passing** tests in agent module (unit tests are solid)
- **12 failing** integration tests (orchestrator method mismatches)
- **50+ warnings** for deprecated datetime usage (technical debt)

**Questions to Answer During Audit:**
1. What methods does `orchestrator.py` actually expose vs. what tests expect?
2. Is `get_session_state()` signature correct? (Takes 2 args but tests pass 3)
3. Are agent integration tests using real LLM calls or mocks?
4. What is the current state of the LangGraph state machine implementation?
5. How does the orchestrator coordinate the 5 agents (Planner, Retrieval, Analyst, Trainer, Evaluator)?

---

### Phase 2: ALIGN (Verify Understanding)

**Action:** Confirm your understanding of the critical issues and sprint objectives.

**Critical Issue #1: Orchestrator Integration Test Failures (HIGH)**
```
Location: tests/services/agent/integration/test_end_to_end.py
Tests Failing: 8 tests
Common Error: AttributeError - orchestrator missing expected methods or wrong signatures

Failed Tests:
1. test_simple_workflow_completion
2. test_workflow_with_price_data
3. test_workflow_with_error_recovery
4. test_workflow_with_clarification
5. test_workflow_with_model_selection
6. test_complete_workflow_with_reporting
7. test_workflow_session_lifecycle
8. test_workflow_with_artifact_generation
```

**Root Cause Analysis Required:**
- Are tests calling methods that don't exist on orchestrator?
- Are method signatures mismatched (e.g., async vs sync)?
- Are tests outdated after orchestrator refactoring?
- Is the LangGraph state machine properly integrated?

**Critical Issue #2: Performance Test Failures (MEDIUM)**
```
Location: tests/services/agent/integration/test_performance.py
Tests Failing: 4 tests

Specific Issues:
- test_session_state_retrieval_performance: get_session_state() takes 2 args but 3 given
- Other 3 tests: AttributeError on orchestrator object
```

**Critical Issue #3: Missing OPENAI_API_KEY (MEDIUM)**
```
Location: .env:59
Problem: OPENAI_API_KEY= (empty)
Impact: Agent tests may fail when attempting real LLM calls
```

**Decision Required:** Should tests use real LLM or mocks?
- **Real LLM:** Requires API key, slower, costs money, validates actual behavior
- **Mocks:** Fast, free, but may miss integration issues

**Technical Debt Issue: Deprecated Datetime (LOW)**
```
Files: 
- backend/app/services/agent/artifacts.py
- backend/app/services/agent/agents/reporting.py
- backend/app/services/agent/tools/reporting_tools.py

Issue: 50+ warnings for datetime.utcnow()
Fix: Replace with datetime.now(datetime.UTC)
```

**Sprint Priorities (Must Complete):**
1. ✅ Fix orchestrator integration tests (8 failures)
2. ✅ Fix performance tests (4 failures)
3. ✅ Configure LLM provider (API key or mock strategy)
4. ✅ Implement Data Retrieval Agent with 4-Ledger access
5. 🔄 Update deprecated datetime calls (stretch goal)
6. 🔄 Enhance Analyst Agent with technical indicators (stretch goal)

**Definition of Done:**
- All 12 integration tests pass
- Orchestrator properly coordinates agent workflows
- Data Retrieval Agent can query all 4 ledgers
- Tests use consistent mocking strategy (or API key configured)
- Documentation updated with any API changes

**Dependencies:**
- **BLOCKED BY:** Track A must fix CatalystEvents schema before full integration testing
- **WAITING FOR:** OPENAI_API_KEY configuration (Track C responsibility, but you can add it)

---

### Phase 3: PLAN (Create Execution Strategy)

**Action:** Develop a detailed, step-by-step plan for sprint execution.

**Recommended Execution Order:**

**Step 1: Audit Orchestrator Implementation (45 minutes)**
1. Open `backend/app/services/agent/orchestrator.py`
2. Document all public methods and their signatures:
   ```python
   class AgentOrchestrator:
       def __init__(self, ...): ...
       async def execute_workflow(self, ...): ...
       async def get_session_state(self, session_id: str): ...  # Verify signature!
       # List all other methods
   ```
3. Open `tests/services/agent/integration/test_end_to_end.py`
4. For each failing test, identify:
   - What method it's calling
   - What parameters it's passing
   - What it expects in return
5. Create a gap analysis document (can be comments in code)

**Step 2: Fix get_session_state() Signature (15 minutes)**
```
Error: get_session_state() takes 2 positional arguments but 3 were given
Location: tests/services/agent/integration/test_performance.py:line_number

Expected signature (2 args):
async def get_session_state(self, session_id: str)

Test is calling (3 args):
await orchestrator.get_session_state(session_id, some_extra_param)

Action: Either fix signature to accept extra param or update test call
```

**Step 3: Align Integration Tests with Orchestrator (2-3 hours)**
For each of the 8 failing end-to-end tests:
1. Read test expectations
2. Verify orchestrator has the method being called
3. Options:
   - **Option A:** Add missing methods to orchestrator
   - **Option B:** Update test to use correct methods
   - **Option C:** Fix method signature mismatches
4. Decision criteria: Choose based on actual requirements in `SYSTEM_REQUIREMENTS.md`

Example pattern:
```python
# Test expects
result = await orchestrator.run_workflow(goal="Predict BTC price")

# But orchestrator has
result = await orchestrator.execute_workflow(user_goal="Predict BTC price")

# Decision: Update test OR add run_workflow() as alias
```

**Step 4: Configure LLM Provider Strategy (30 minutes)**
1. **Check if API key needed:**
   ```bash
   grep -r "openai" tests/services/agent/integration/
   ```
2. **Option A: Use Mocks (Recommended for CI/CD)**
   ```python
   # In conftest.py or test setup
   @pytest.fixture
   def mock_llm():
       with patch('langchain_openai.ChatOpenAI') as mock:
           mock.return_value.invoke.return_value = MockResponse(...)
           yield mock
   ```
3. **Option B: Use Real API (For validation)**
   - Add to `.env`: `OPENAI_API_KEY=sk-...`
   - Ensure tests can access it
   - Add `@pytest.mark.requires_api` marker

**Step 5: Implement Data Retrieval Agent (3-4 hours)**
1. Create or enhance `backend/app/services/agent/agents/data_retrieval.py`
2. Add tools to query 4-Ledger tables:
   ```python
   class DataRetrievalAgent:
       def get_price_data(self, coin: str, start: datetime, end: datetime)
       def get_catalyst_events(self, event_type: str, days_back: int)
       def get_news_sentiment(self, coin: str, days_back: int)
       def get_on_chain_metrics(self, protocol: str)
   ```
3. Integrate with LangChain tool system
4. Connect to PostgreSQL using session from `backend/app/core/db.py`
5. Add unit tests in `tests/services/agent/agents/test_data_retrieval.py`
6. Add integration test verifying queries work against test database

**Step 6: Run Focused Test Suites (30 minutes)**
```bash
# Test orchestrator integration
pytest tests/services/agent/integration/test_end_to_end.py -v

# Test performance
pytest tests/services/agent/integration/test_performance.py -v

# Test data retrieval
pytest tests/services/agent/agents/test_data_retrieval.py -v

# Full agent suite
pytest tests/services/agent/ -v
```

**Step 7: Fix Deprecated Datetime (30 minutes - Optional)**
1. Search and replace pattern:
   ```bash
   # Find all occurrences
   grep -r "datetime.utcnow()" backend/app/services/agent/
   
   # Replace with
   datetime.now(datetime.UTC)
   ```
2. Ensure imports include: `from datetime import datetime, UTC`
3. Run tests to verify no behavioral changes

**Step 8: Integration with Track A Data (1 hour)**
1. **Wait for Track A** to fix CatalystEvents schema
2. Once fixed, test Data Retrieval Agent against real data:
   ```python
   # Test can query all 4 ledgers
   agent = DataRetrievalAgent()
   assert agent.get_price_data("BTC", ...) is not None
   assert agent.get_catalyst_events("listing", 7) is not None
   assert agent.get_news_sentiment("BTC", 7) is not None
   assert agent.get_on_chain_metrics("ethereum") is not None
   ```

---

### Phase 4: EXECUTE (Implement the Plan)

**Action:** Execute the plan methodically, testing after each step.

**Execution Guidelines:**
1. **Understand before changing** - Read orchestrator code thoroughly first
2. **Test incrementally** - Fix one test at a time, verify it passes
3. **Maintain backward compatibility** - Don't break existing passing tests
4. **Document LangGraph flow** - If you modify state machine, update comments
5. **Communication** - Track A schema fix blocks full integration - coordinate

**Git Commit Message Template:**
```
[Track B] <component>: <short description>

- <detail 1>
- <detail 2>

Fixes: <test file>::<test name>
Tests: <affected test files>
```

**Example Commit:**
```
[Track B] orchestrator: Fix get_session_state signature mismatch

- Changed method to accept optional 'include_history' parameter
- Updated integration tests to use correct signature
- Maintains backward compatibility with existing calls

Fixes: test_performance.py::test_session_state_retrieval_performance
Tests: tests/services/agent/integration/test_performance.py
```

**Testing Commands:**
```bash
# Activate virtual environment
cd /home/mark/omc/ohmycoins/backend
source .venv/bin/activate

# Test specific integration suite
pytest tests/services/agent/integration/ -v

# Test with markers (if configured)
pytest tests/services/agent/ -m "not slow" -v

# Test single file
pytest tests/services/agent/integration/test_end_to_end.py::test_simple_workflow_completion -v

# Run with coverage
pytest tests/services/agent/ --cov=app.services.agent --cov-report=html
```

**Debugging Tips:**
```python
# Add breakpoint in orchestrator
import pdb; pdb.set_trace()

# Or use pytest debugging
pytest tests/services/agent/integration/test_end_to_end.py --pdb

# Print orchestrator state
print(f"Orchestrator methods: {dir(orchestrator)}")
print(f"Session state: {orchestrator.get_session_state(session_id)}")
```

**Success Criteria:**
- [ ] All 8 end-to-end integration tests passing
- [ ] All 4 performance tests passing
- [ ] Data Retrieval Agent implemented and tested
- [ ] LLM provider strategy documented (mock or real API)
- [ ] No AttributeError exceptions in agent tests
- [ ] Orchestrator methods aligned with test expectations
- [ ] Ready for Lab-to-Floor integration (promote algorithms)

---

## 🔧 Technical Context

**Your Development Boundaries:**
- **Primary:** `backend/app/services/agent/`
- **Shared:** `backend/app/models.py` (read-only - coordinate with Track A for changes)
- **Tests:** `tests/services/agent/`

**DO NOT MODIFY:**
- `backend/app/services/collectors/` (Track A's domain)
- `backend/app/services/trading/` (Track A's domain - except for algorithm promotion)
- `infrastructure/` (Track C's domain)
- Frontend code

**Integration Contracts:**
- **Track A** provides data via `backend/app/models.py` schema
- **Track C** provides `OPENAI_API_KEY` via secrets management
- Your agents must read from Track A's 4-Ledger tables
- Your algorithms must be promotable to "The Floor" (trading system)

**Agent Architecture (Your Responsibility):**
1. **Orchestrator** - Manages LangGraph state machine and agent coordination
2. **Planner Agent** - Breaks down user goals into steps
3. **Data Retrieval Agent** - Queries 4-Ledger database ← **Current focus**
4. **Data Analyst Agent** - EDA, feature engineering, technical indicators
5. **Model Trainer Agent** - Trains ML models in restricted sandbox
6. **Model Evaluator Agent** - Performance metrics and promotion logic

**LangGraph State Machine:**
- Review `backend/app/services/agent/orchestrator.py` for state nodes
- Understand ReAct loop: Reason → Act → Observe → Repeat
- Human-in-the-Loop nodes for clarification and approval

---

## 📚 Additional Resources

**Database Access Pattern:**
```python
from app.core.db import SessionLocal
from app.models import PriceData5Min, CatalystEvents, NewsSentiment, OnChainMetrics

with SessionLocal() as session:
    # Query 4-Ledgers
    prices = session.query(PriceData5Min).filter(...).all()
    events = session.query(CatalystEvents).filter(...).all()
```

**LangChain Tool Pattern:**
```python
from langchain.tools import tool

@tool
def query_price_data(coin: str, days_back: int) -> str:
    """Query price data for a specific coin."""
    # Implementation
    return result
```

**Environment Variables:**
```bash
# .env file location
/home/mark/omc/ohmycoins/.env

# Key variables for your work
OPENAI_API_KEY=  # Currently empty - needs configuration
OPENAI_MODEL=gpt-4-turbo-preview
REDIS_HOST=localhost  # Agent state storage
REDIS_PORT=6379
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300
```

**Useful Commands:**
```bash
# Redis CLI (check agent state)
docker exec -it ohmycoins-redis-1 redis-cli

# View agent session keys
KEYS agent:session:*

# Check specific session
GET agent:session:<session_id>

# Python shell with agent context
cd backend
source .venv/bin/activate
python -c "from app.services.agent.orchestrator import AgentOrchestrator; print(dir(AgentOrchestrator))"
```

---

## 🚨 Escalation Points

**Escalate if:**
1. Orchestrator refactoring reveals fundamental architecture issues
2. LangGraph state machine needs redesign (not just method fixes)
3. Integration with Track A data requires schema changes
4. Test failures indicate LLM provider issues beyond configuration

**Do NOT escalate for:**
- Method signature mismatches (fix them)
- Test assertion updates
- Deprecated datetime warnings
- Waiting for Track A schema fix (expected dependency)

---

## ✅ Final Checklist Before Sprint Completion

Before marking sprint complete, verify:

- [ ] `git status` shows all changes committed
- [ ] `pytest tests/services/agent/integration/ -v` passes with 0 failures
- [ ] Data Retrieval Agent successfully queries all 4 ledgers
- [ ] Orchestrator integration tests fully aligned
- [ ] LLM provider strategy documented in README or comments
- [ ] No merge conflicts with main branch
- [ ] Track A notified if any data schema questions arose
- [ ] Sprint tasks in `CURRENT_SPRINT.md` marked complete

---

**Remember:** Your agents are the "brain" of the system. They must reliably coordinate, reason, and learn from Track A's data. Focus on making the orchestrator robust and the integration tests comprehensive. The Lab-to-Floor pipeline depends on your agent system working flawlessly.

**Good luck! 🚀**
