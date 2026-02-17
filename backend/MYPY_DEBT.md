# MyPy Technical Debt (Sprint 2.26)

This file lists the modules currently exempted from strict type checking to unblock `mypy` enforcement. Resolving these should be prioritized in upcoming tech debt sprints.

## 🧹 Debt Recovery Plan

To remove an ignore:
1. Delete `# mypy: ignore-errors` from the file header.
2. Run `docker run --rm -v $(pwd)/backend:/app backend:latest mypy --no-incremental path/to/file.py`.
3. Add missing type hints, fix null-safety issues (`Optional`), and resolve strict mode errors.

---

### 🟢 Low Complexity (Scripts & Utils)
*Easy wins: Usually missing return types (`-> None`) or simple argument annotations.*

- `backend/app/utils/seed_data.py`
- `backend/app/utils/test_fixtures.py`
- `backend/scripts/benchmark_safety.py`
- `backend/scripts/byom_performance_benchmark.py`
- `backend/scripts/hard_stop_watcher.py`
- `backend/scripts/run_live_strategy.py`
- `backend/scripts/run_ma_strategy.py`
- `backend/scripts/seed_live_strategy.py`

### 🟡 Medium Complexity (Collectors & Integrations)
*External API integrations often return untyped `JSON` (dicts) that require `TypedDict` or Pydantic models.*

- `backend/app/services/collector.py` (Legacy?)
- `backend/app/services/collectors/api_collector.py`
- `backend/app/services/collectors/base.py`
- `backend/app/services/collectors/catalyst/coinspot_announcements.py`
- `backend/app/services/collectors/catalyst/sec_api.py`
- `backend/app/services/collectors/config.py`
- `backend/app/services/collectors/factory.py`
- `backend/app/services/collectors/glass/defillama.py`
- `backend/app/services/collectors/glass/nansen.py`
- `backend/app/services/collectors/human/cryptopanic.py`
- `backend/app/services/collectors/human/newscatcher.py`
- `backend/app/services/collectors/human/reddit.py`
- `backend/app/services/collectors/metrics.py`
- `backend/app/services/collectors/orchestrator.py`
- `backend/app/services/collectors/quality_monitor.py`

### 🔴 High Complexity (Agents & Trading Logic)
*Heavy use of dynamic state (`dict[str, Any]`), strict SQLAlchemy null-safety, and complex inheritance.*

- `backend/app/services/agent/agents/model_evaluator.py`
- `backend/app/services/agent/agents/model_training.py`
- `backend/app/services/agent/agents/reporting.py`
- `backend/app/services/agent/artifacts.py`
- `backend/app/services/agent/langgraph_workflow.py` (State complexity)
- `backend/app/services/agent/llm_factory.py`
- `backend/app/services/agent/nodes/approval.py`
- `backend/app/services/agent/nodes/choice_presentation.py`
- `backend/app/services/agent/nodes/clarification.py`
- `backend/app/services/agent/orchestrator.py`
- `backend/app/services/agent/override.py`
- `backend/app/services/agent/tools/data_analysis_tools.py`
- `backend/app/services/agent/tools/data_retrieval_tools.py`
- `backend/app/services/agent/tools/model_evaluation_tools.py`
- `backend/app/services/agent/tools/model_training_tools.py`
- `backend/app/services/agent/tools/reporting_tools.py`
- `backend/app/services/backtesting/engine.py`
- `backend/app/services/compliance/reporting.py`
- `backend/app/services/encryption.py`
- `backend/app/services/execution/manager.py` (Critical Path)
- `backend/app/services/execution/vwap.py`
- `backend/app/services/scheduler.py`
- `backend/app/services/trading/base_exchange.py`
- `backend/app/services/trading/client.py`
- `backend/app/services/trading/executor.py` (Critical Path)
- `backend/app/services/trading/paper_exchange.py`
- `backend/app/services/trading/pnl.py`
- `backend/app/services/trading/positions.py`
- `backend/app/services/trading/recorder.py`
- `backend/app/services/trading/safety.py` (Critical Path)
- `backend/app/services/trading/scheduler.py`
- `backend/app/services/trading/strategies/ma_crossover.py`
- `backend/app/services/trading/watcher.py`
- `backend/app/services/websocket_manager.py`

### ⚠️ API Routes (Validation)
*FastAPI routes often suffer from missing return type annotations (`-> Any`) or dependency injection complexity.*

- `backend/app/api/middleware/rate_limiting.py`
- `backend/app/api/routes/agent.py`
- `backend/app/api/routes/floor.py`
- `backend/app/api/routes/mock_ui.py`
- `backend/app/api/routes/risk.py`
- `backend/app/api/routes/trading.py`
- `backend/app/api/routes/websockets.py`
