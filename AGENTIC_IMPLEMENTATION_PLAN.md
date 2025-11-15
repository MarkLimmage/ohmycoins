# Agentic Data Science System - Implementation Plan

## Overview

This document provides a detailed, week-by-week implementation plan for adding autonomous agentic capabilities to the Oh My Coins Lab Service. The plan is designed for minimal changes while maximizing impact.

## Timeline: 14 Weeks (3.5 months)

## Phase 1: Foundation Setup (Weeks 1-2)

### Week 1: Framework Integration

**Goals**:
- Install and configure LangChain/LangGraph
- Set up Redis for state management
- Create basic project structure

**Tasks**:

1. **Day 1-2: Dependencies and Configuration**
   - [ ] Update `backend/pyproject.toml` with agent dependencies
     ```toml
     dependencies = [
         # Existing...
         "langchain>=0.1.0",
         "langchain-openai>=0.0.5",
         "langgraph>=0.0.20",
         "redis>=5.0.0",
         "pandas>=2.0.0",
         "scikit-learn>=1.3.0",
         "xgboost>=2.0.0",
         "matplotlib>=3.7.0",
         "seaborn>=0.12.0",
         "ta>=0.11.0",
     ]
     ```
   - [ ] Add Redis to `docker-compose.yml`
   - [ ] Create `.env` configuration for LLM providers
   - [ ] Install dependencies: `cd backend && uv sync`

2. **Day 3-4: Project Structure**
   - [ ] Create directory structure:
     ```
     backend/app/services/agent/
     ├── __init__.py
     ├── orchestrator.py
     ├── session_manager.py
     ├── graph.py
     ├── sandbox.py
     ├── agents/
     │   ├── __init__.py
     │   ├── base.py
     │   ├── data_retrieval.py
     │   ├── data_analyst.py
     │   ├── model_trainer.py
     │   ├── model_evaluator.py
     │   └── reporter.py
     └── tools/
         ├── __init__.py
         ├── data_tools.py
         ├── analysis_tools.py
         ├── modeling_tools.py
         └── evaluation_tools.py
     ```
   - [ ] Create base classes and interfaces
   - [ ] Set up configuration management

3. **Day 5: Database Schema**
   - [ ] Create Alembic migration for agent tables:
     - `agent_sessions`
     - `agent_session_messages`
     - `agent_artifacts`
   - [ ] Add SQLModel classes to `backend/app/models.py`
   - [ ] Run migration: `uv run alembic upgrade head`
   - [ ] Test database schema creation

**Deliverables**:
- ✅ Project structure created
- ✅ Dependencies installed
- ✅ Redis running
- ✅ Database schema created
- ✅ Basic configuration in place

**Testing**:
- Verify Redis connection
- Verify LangChain imports work
- Verify database tables created

---

### Week 2: Core Infrastructure

**Goals**:
- Implement session management
- Create basic orchestrator skeleton
- Set up API routes

**Tasks**:

1. **Day 1-2: Session Manager**
   - [ ] Implement `SessionManager` class
   - [ ] CRUD operations for agent sessions
   - [ ] Redis integration for state management
   - [ ] Conversation history tracking
   - [ ] Write unit tests for session manager

2. **Day 3-4: Base Agent and Orchestrator**
   - [ ] Implement `BaseAgent` class
   - [ ] Create `AgentOrchestrator` skeleton
   - [ ] LLM client initialization (OpenAI/Anthropic)
   - [ ] Basic error handling
   - [ ] Write unit tests

3. **Day 5: API Routes**
   - [ ] Create `backend/app/api/routes/agent.py`
   - [ ] Implement endpoints:
     - `POST /api/v1/lab/agent/sessions`
     - `GET /api/v1/lab/agent/sessions/{id}`
     - `DELETE /api/v1/lab/agent/sessions/{id}`
   - [ ] Add authentication/authorization
   - [ ] Write API tests

**Deliverables**:
- ✅ SessionManager working with Redis
- ✅ AgentOrchestrator initialized
- ✅ API routes functional
- ✅ Unit tests passing

**Testing**:
- Create/retrieve/delete sessions via API
- Verify session state persists in Redis
- Test authentication and authorization

---

## Phase 2: Data Agents (Weeks 3-4)

### Week 3: Data Retrieval Agent

**Goals**:
- Implement data retrieval tools
- Create DataRetrievalAgent
- Test with real price data

**Tasks**:

1. **Day 1-2: Data Tools**
   - [ ] Implement `fetch_price_data` tool
     - Query `price_data_5min` table
     - Support date range filtering
     - Support coin type filtering
     - Return as pandas DataFrame
   - [ ] Implement `get_available_coins` tool
   - [ ] Implement `get_data_statistics` tool
   - [ ] Write tool tests with mock data

2. **Day 3-4: DataRetrievalAgent**
   - [ ] Create `DataRetrievalAgent` class
   - [ ] Define system prompt
   - [ ] Register data tools
   - [ ] Implement agent execution logic
   - [ ] Handle errors and edge cases

3. **Day 5: Integration Testing**
   - [ ] Test agent with real database
   - [ ] Test with various date ranges
   - [ ] Test with missing/invalid data
   - [ ] Performance testing (large date ranges)

**Deliverables**:
- ✅ Data tools functional
- ✅ DataRetrievalAgent working
- ✅ Integration tests passing
- ✅ Real data retrieval verified

**Testing**:
- Fetch Bitcoin data for last month
- Fetch multiple coins simultaneously
- Handle missing coins gracefully
- Verify data quality

---

### Week 4: Data Analyst Agent

**Goals**:
- Implement analysis tools
- Create DataAnalystAgent
- Test EDA and feature engineering

**Tasks**:

1. **Day 1-2: Analysis Tools**
   - [ ] Implement `calculate_technical_indicators` tool
     - SMA (Simple Moving Average)
     - EMA (Exponential Moving Average)
     - RSI (Relative Strength Index)
     - MACD
     - Bollinger Bands
   - [ ] Implement `clean_data` tool
     - Handle missing values
     - Remove outliers
     - Type validation
   - [ ] Implement `perform_eda` tool
     - Summary statistics
     - Distribution analysis
     - Correlation analysis

3. **Day 3-4: Feature Engineering**
   - [ ] Implement `create_features` tool
     - Lagged features
     - Rolling statistics
     - Price changes and returns
     - Target variable creation
   - [ ] Test feature engineering pipeline

4. **Day 5: DataAnalystAgent**
   - [ ] Create `DataAnalystAgent` class
   - [ ] Define system prompt
   - [ ] Register analysis tools
   - [ ] Integration testing
   - [ ] Document usage patterns

**Deliverables**:
- ✅ Technical indicators working
- ✅ Data cleaning functional
- ✅ Feature engineering pipeline ready
- ✅ DataAnalystAgent operational

**Testing**:
- Calculate indicators on Bitcoin data
- Clean messy data
- Generate features for model training
- Verify feature quality

---

## Phase 3: Modeling Agents (Weeks 5-6)

### Week 5: Model Training Agent

**Goals**:
- Implement model training tools
- Create ModelTrainingAgent
- Support multiple algorithms

**Tasks**:

1. **Day 1-2: Training Tools**
   - [ ] Implement `train_classification_model` tool
     - LogisticRegression
     - RandomForest
     - GradientBoosting
     - XGBoost
   - [ ] Implement `train_regression_model` tool
   - [ ] Implement `cross_validate_model` tool
   - [ ] Model serialization/deserialization

2. **Day 3-4: ModelTrainingAgent**
   - [ ] Create `ModelTrainingAgent` class
   - [ ] Define system prompt
   - [ ] Register training tools
   - [ ] Algorithm selection logic
   - [ ] Handle training errors

3. **Day 5: Integration Testing**
   - [ ] Train models on real price data
   - [ ] Test all supported algorithms
   - [ ] Verify model persistence
   - [ ] Performance benchmarking

**Deliverables**:
- ✅ Training tools functional
- ✅ Multiple algorithms supported
- ✅ ModelTrainingAgent working
- ✅ Models can be saved/loaded

**Testing**:
- Train classification models (predict price up/down)
- Train regression models (predict price value)
- Cross-validation
- Compare training times

---

### Week 6: Model Evaluator Agent

**Goals**:
- Implement evaluation tools
- Create ModelEvaluatorAgent
- Support hyperparameter tuning

**Tasks**:

1. **Day 1-2: Evaluation Tools**
   - [ ] Implement `evaluate_model` tool
     - Accuracy, Precision, Recall, F1
     - AUC-ROC, AUC-PR
     - Confusion matrix
   - [ ] Implement `compare_models` tool
   - [ ] Implement `calculate_feature_importance` tool

2. **Day 3-4: Tuning Tools**
   - [ ] Implement `tune_hyperparameters` tool
     - GridSearchCV
     - RandomizedSearchCV
   - [ ] Implement tuning strategies
   - [ ] Performance optimization

3. **Day 5: ModelEvaluatorAgent**
   - [ ] Create `ModelEvaluatorAgent` class
   - [ ] Define system prompt
   - [ ] Register evaluation tools
   - [ ] Decision logic (tune vs deploy)
   - [ ] Integration testing

**Deliverables**:
- ✅ Evaluation metrics working
- ✅ Model comparison functional
- ✅ Hyperparameter tuning ready
- ✅ ModelEvaluatorAgent operational

**Testing**:
- Evaluate models on test data
- Compare multiple models
- Tune hyperparameters
- Verify improvements

---

## Phase 4: Orchestration & ReAct (Weeks 7-8)

### Week 7: LangGraph State Machine

**Goals**:
- Implement LangGraph workflow
- Create state transitions
- Test ReAct loop

**Tasks**:

1. **Day 1-2: State Definition**
   - [ ] Define `AgentState` TypedDict
   - [ ] Define all state fields
   - [ ] Create state update functions

2. **Day 3-4: Workflow Nodes**
   - [ ] Implement `planning_node`
   - [ ] Implement `data_retrieval_node`
   - [ ] Implement `data_analysis_node`
   - [ ] Implement `feature_engineering_node`
   - [ ] Implement `model_training_node`
   - [ ] Implement `model_evaluation_node`
   - [ ] Implement `hyperparameter_tuning_node`
   - [ ] Implement `reporting_node`

3. **Day 5: Graph Construction**
   - [ ] Define node edges
   - [ ] Define conditional edges
   - [ ] Set entry/exit points
   - [ ] Compile graph
   - [ ] Test state transitions

**Deliverables**:
- ✅ LangGraph state machine defined
- ✅ All workflow nodes implemented
- ✅ State transitions working
- ✅ Graph compiles successfully

**Testing**:
- Test each node in isolation
- Test state transitions
- Test conditional edges
- Verify complete workflow path

---

### Week 8: ReAct Loop & Orchestration

**Goals**:
- Implement ReAct loop
- Connect all agents
- End-to-end workflow

**Tasks**:

1. **Day 1-2: ReAct Implementation**
   - [ ] Implement Reason step
   - [ ] Implement Act step (tool calls)
   - [ ] Implement Observe step
   - [ ] Loop control logic
   - [ ] Max iterations limit

2. **Day 3-4: Agent Coordination**
   - [ ] Connect agents to orchestrator
   - [ ] Agent-to-agent data passing
   - [ ] Error propagation
   - [ ] Recovery mechanisms

3. **Day 5: End-to-End Testing**
   - [ ] Test complete workflow
   - [ ] Test with simple goal: "Predict Bitcoin price"
   - [ ] Test with complex goal
   - [ ] Debug and fix issues

**Deliverables**:
- ✅ ReAct loop working
- ✅ Agents coordinated
- ✅ End-to-end workflow functional
- ✅ Basic use cases working

**Testing**:
- Run complete workflow with test goal
- Verify each agent is invoked
- Check data flows correctly
- Validate final results

---

## Phase 5: Human-in-the-Loop (Weeks 9-10)

### Week 9: Clarification System

**Goals**:
- Implement clarification requests
- Add user response handling
- Test interactive mode

**Tasks**:

1. **Day 1-2: Clarification Models**
   - [ ] Create `ClarificationRequest` model
   - [ ] Create `ClarificationResponse` model
   - [ ] Database schema for clarifications
   - [ ] API endpoints for responses

2. **Day 3-4: Clarification Logic**
   - [ ] Identify clarification triggers
   - [ ] Generate clarification questions
   - [ ] Provide multiple choice options
   - [ ] Handle free-form responses

3. **Day 5: Integration**
   - [ ] Add `awaiting_user` node to graph
   - [ ] Implement response handling
   - [ ] Resume workflow after response
   - [ ] Test interactive sessions

**Deliverables**:
- ✅ Clarification system working
- ✅ API endpoints functional
- ✅ Interactive mode operational
- ✅ User responses handled correctly

**Testing**:
- Trigger clarification (ambiguous input)
- Respond via API
- Verify workflow resumes
- Test with multiple clarifications

---

### Week 10: Choice Presentation & Overrides

**Goals**:
- Implement model comparison UI
- Add user override mechanism
- Support approval gates

**Tasks**:

1. **Day 1-2: Choice Presentation**
   - [ ] Format model comparison results
   - [ ] Present pros/cons clearly
   - [ ] Recommendation logic
   - [ ] API endpoint for choices

2. **Day 3-4: Override Mechanism**
   - [ ] API endpoint for overrides
   - [ ] Override types: model selection, parameters, restart
   - [ ] Update graph state with override
   - [ ] Resume from override point

3. **Day 5: Approval Gates**
   - [ ] Define gate points in workflow
   - [ ] Auto-approve vs manual modes
   - [ ] Timeout handling
   - [ ] Test all gate types

**Deliverables**:
- ✅ Choice presentation polished
- ✅ Override mechanism working
- ✅ Approval gates functional
- ✅ User control maintained

**Testing**:
- Present model choices to user
- Override model selection
- Test approval gates
- Verify control flow

---

## Phase 6: Reporting & Completion (Weeks 11-12)

### Week 11: Reporting Agent

**Goals**:
- Implement reporting tools
- Create ReportingAgent
- Generate comprehensive reports

**Tasks**:

1. **Day 1-2: Reporting Tools**
   - [ ] Implement `generate_summary` tool
   - [ ] Implement `create_comparison_report` tool
   - [ ] Implement `generate_recommendations` tool
   - [ ] Format reports as Markdown/HTML

2. **Day 3-4: ReportingAgent**
   - [ ] Create `ReportingAgent` class
   - [ ] Define system prompt
   - [ ] Register reporting tools
   - [ ] Natural language generation
   - [ ] Test report quality

3. **Day 5: Artifact Management**
   - [ ] Save models to filesystem/S3
   - [ ] Save plots and visualizations
   - [ ] Save final reports
   - [ ] Track artifacts in database

**Deliverables**:
- ✅ ReportingAgent functional
- ✅ High-quality reports generated
- ✅ Artifacts properly saved
- ✅ Results accessible via API

**Testing**:
- Generate reports for completed sessions
- Verify report quality and clarity
- Check artifact storage
- Test report retrieval

---

### Week 12: Code Sandbox

**Goals**:
- Implement secure sandbox
- Test with agent-generated code
- Add safety constraints

**Tasks**:

1. **Day 1-2: Sandbox Implementation**
   - [ ] Implement `CodeSandbox` class
   - [ ] Restricted imports
   - [ ] Resource limits (CPU, memory, time)
   - [ ] Input validation

2. **Day 3-4: Safety Features**
   - [ ] AST parsing for code validation
   - [ ] Forbidden operation detection
   - [ ] Timeout handling
   - [ ] Memory limit enforcement

3. **Day 5: Integration & Testing**
   - [ ] Integrate sandbox with agents
   - [ ] Test with generated code
   - [ ] Security testing
   - [ ] Performance testing

**Deliverables**:
- ✅ Secure sandbox operational
- ✅ Safety constraints enforced
- ✅ Code execution working
- ✅ Security validated

**Testing**:
- Execute safe code successfully
- Block dangerous operations
- Enforce time limits
- Enforce memory limits

---

## Phase 7: Testing & Documentation (Weeks 13-14)

### Week 13: Comprehensive Testing

**Goals**:
- Complete test coverage
- Integration tests
- Performance testing

**Tasks**:

1. **Day 1-2: Unit Tests**
   - [ ] Test all agents
   - [ ] Test all tools
   - [ ] Test orchestrator
   - [ ] Test session manager
   - [ ] Achieve 80%+ coverage

2. **Day 3-4: Integration Tests**
   - [ ] End-to-end workflow tests
   - [ ] Database integration tests
   - [ ] Redis integration tests
   - [ ] API integration tests

3. **Day 5: Performance & Security**
   - [ ] Load testing (concurrent sessions)
   - [ ] Performance profiling
   - [ ] Security audit
   - [ ] Fix identified issues

**Deliverables**:
- ✅ 80%+ test coverage
- ✅ All tests passing
- ✅ Performance acceptable
- ✅ Security validated

**Testing**:
- Run full test suite
- Performance benchmarks
- Security scan
- Fix all issues

---

### Week 14: Documentation & Polish

**Goals**:
- Complete documentation
- User guides
- API documentation
- Final polish

**Tasks**:

1. **Day 1-2: API Documentation**
   - [ ] OpenAPI/Swagger docs
   - [ ] Endpoint descriptions
   - [ ] Request/response examples
   - [ ] Error codes documented

2. **Day 3-4: User Documentation**
   - [ ] Getting started guide
   - [ ] Usage examples
   - [ ] Best practices
   - [ ] Troubleshooting guide

3. **Day 5: Final Polish**
   - [ ] Code cleanup
   - [ ] Logging improvements
   - [ ] Error message refinement
   - [ ] Final testing
   - [ ] Release preparation

**Deliverables**:
- ✅ Complete documentation
- ✅ User guides ready
- ✅ API docs published
- ✅ System ready for use

**Testing**:
- Follow getting started guide
- Run all examples
- Verify documentation accuracy
- User acceptance testing

---

## Risk Management

### High-Risk Items

1. **LLM API Reliability**
   - Risk: OpenAI/Anthropic API downtime
   - Mitigation: Implement retry logic, fallback to different model, cache responses

2. **Code Sandbox Security**
   - Risk: Agent-generated code escapes sandbox
   - Mitigation: Multiple layers of validation, resource limits, regular security audits

3. **Performance**
   - Risk: LLM calls too slow, workflow takes too long
   - Mitigation: Parallel tool execution, caching, streaming responses

4. **Cost**
   - Risk: LLM API costs exceed budget
   - Mitigation: Token limits per session, cost tracking, alerts

### Medium-Risk Items

1. **Integration Complexity**
   - Risk: Agents don't coordinate well
   - Mitigation: Thorough testing, clear interfaces, good error handling

2. **User Experience**
   - Risk: Clarifications too frequent or confusing
   - Mitigation: User testing, refinement, smart defaults

3. **Data Quality**
   - Risk: Poor input data leads to poor models
   - Mitigation: Data validation, quality checks, user warnings

## Success Metrics

### Functional Metrics
- [ ] Agent accepts natural language goals ✅
- [ ] Agent autonomously completes workflow ✅
- [ ] Agent generates actionable results ✅
- [ ] User can interact via clarifications ✅
- [ ] User can override decisions ✅

### Performance Metrics
- [ ] Simple tasks complete in < 5 minutes
- [ ] Complex tasks complete in < 15 minutes
- [ ] 90%+ session success rate
- [ ] 10 concurrent sessions supported

### Quality Metrics
- [ ] 80%+ test coverage
- [ ] Zero critical security issues
- [ ] Documentation complete
- [ ] User satisfaction > 4/5

## Resource Requirements

### Personnel
- 1 Full-time developer for 14 weeks
- Part-time code reviews
- Part-time testing support

### Infrastructure
- OpenAI API access (GPT-4)
- Redis instance
- PostgreSQL (existing)
- S3 for artifact storage (optional)

### Budget
- LLM API costs: ~$500/month during development
- Infrastructure: ~$50/month (Redis)
- Total: ~$1,500 for project

## Rollout Strategy

### Phase 1: Internal Testing (Week 15)
- Deploy to staging environment
- Internal team testing
- Gather feedback
- Fix critical issues

### Phase 2: Beta Release (Week 16)
- Select beta users
- Limited feature set
- Close monitoring
- Iterative improvements

### Phase 3: General Availability (Week 17+)
- Full feature release
- Documentation published
- Marketing/announcement
- Ongoing support

## Maintenance Plan

### Ongoing Tasks
- Monitor LLM API costs
- Review and improve prompts
- Add new tools as needed
- Update documentation
- Security patches
- Performance optimization

### Quarterly Reviews
- User feedback analysis
- Feature prioritization
- Cost analysis
- Security audit

## Conclusion

This implementation plan provides a structured, week-by-week roadmap for adding agentic capabilities to Oh My Coins. The plan emphasizes:

- **Incremental development**: Build and test components sequentially
- **Minimal changes**: Integrate with existing architecture
- **Quality focus**: Testing and documentation throughout
- **Risk mitigation**: Address risks proactively
- **User-centric**: Human-in-the-loop features ensure control

Following this plan will result in a production-ready agentic data science system that transforms the Lab from a manual platform into an AI-powered autonomous assistant.
