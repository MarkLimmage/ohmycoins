# WORKER MISSION — Graph Agent (Workflow Routing & Rendering)

**You are the Graph Agent.** You are the sole developer in this worktree.
Ignore all legacy documentation (CLAUDE.md, CURRENT_SPRINT.md, AGENT_INSTRUCTIONS.md).
This file is your single source of truth.

## Your Role

Fix the LangGraph workflow routing, stage attribution, quality validation, and report rendering so that the pipeline correctly routes goals, attributes stages, and renders final reports.

## Strict File Ownership

You may ONLY modify these files:
- `backend/app/services/agent/langgraph_workflow.py`
- `backend/app/services/agent/agents/reporting.py`

**DO NOT** touch `clarification.py`, `data_retrieval.py`, `data_analyst.py`, `data_analysis_tools.py`, or any frontend/infra files.
Another worker is handling those files in parallel. Touching them will cause merge conflicts.

## Container & Port Isolation

- You do NOT need to run any Docker containers or servers.
- You are editing Python files only. There is no local test server.
- All integration testing will be done by the Supervisor after merge using `scripts/lab_driver.py` against production.
- Your job is to make the code changes, verify them by reading and tracing the code logic, and commit.

## Your Issues (5 total)

### Issue 3: Quality Check Blind to User Goal (P1 — High)

**Problem**: `_validate_data_node()` checks if data was retrieved but doesn't consider whether the data is sufficient for the user's goal. E.g., user asks for sentiment correlation but quality check passes with 0 sentiment rows.

**Root Cause**: `_validate_data_node` in `langgraph_workflow.py` has access to `user_goal` from state but doesn't use it. It only checks generic data presence.

**Fix**: In `_validate_data_node`, read `scope_interpretation` from state and check if goal-essential data types are present. Specifically:
```python
scope = state.get("scope_interpretation", {})
indicators = scope.get("indicators", [])
analysis_type = scope.get("analysis_type", "")

# Check if goal-essential data is missing
warnings = []
retrieved_data = state.get("retrieved_data", {})

if any("sentiment" in i.lower() for i in indicators):
    sentiment = retrieved_data.get("sentiment_data", {})
    news_count = len(sentiment.get("news_sentiment", []))
    social_count = len(sentiment.get("social_sentiment", []))
    if news_count == 0 and social_count == 0:
        warnings.append("Goal requires sentiment data but none was retrieved")

if any("on_chain" in i.lower() or "onchain" in i.lower() for i in indicators):
    onchain = retrieved_data.get("onchain_data", {})
    if not onchain or all(len(v) == 0 for v in onchain.values() if isinstance(v, list)):
        warnings.append("Goal requires on-chain data but none was retrieved")

# Emit warnings but don't block — data may still be partially useful
for w in warnings:
    await self._emit_event(state, "status_update", "PREPARATION", {
        "status": "WARNING",
        "message": f"⚠ {w}",
    })

# Continue with validation — don't fail the pipeline, just warn
```

The key insight: don't BLOCK on missing data — just WARN. The pipeline should still run with whatever data is available, but the user and the LLM reasoning node should be aware of gaps.

**File**: `backend/app/services/agent/langgraph_workflow.py`

---

### Issue 5: Stage Events Misattributed (P2 — Medium)

**Problem**: Events in DATA_ACQUISITION and later stages show `stage: "BUSINESS_UNDERSTANDING"` in the wrapper.

**Root Cause**: `_reason_node()` in `langgraph_workflow.py` hardcodes `stage="BUSINESS_UNDERSTANDING"` regardless of the current workflow stage. When the reasoning node is re-entered after data acquisition, it still emits events with BUSINESS_UNDERSTANDING.

**Fix**: Determine the correct stage dynamically. The state should contain information about what stages have completed. Read `current_stage` from state, or infer it from the completed stages:
```python
# In _reason_node(), determine current stage
completed_stages = state.get("completed_stages", [])
if "DATA_ACQUISITION" in completed_stages:
    current_stage = "PREPARATION"
elif "BUSINESS_UNDERSTANDING" in completed_stages:
    current_stage = "DATA_ACQUISITION"
else:
    current_stage = "BUSINESS_UNDERSTANDING"

# Use current_stage in all emit_event calls within this node
await self._emit_event(state, "stream_chat", current_stage, {"text_delta": "..."})
```

Also ensure that other nodes that emit events use appropriate stage values. Grep for hardcoded `"BUSINESS_UNDERSTANDING"` strings and fix them.

**File**: `backend/app/services/agent/langgraph_workflow.py`

---

### Issue 6: BU stage_complete Fires Twice (P2 — Medium)

**Problem**: `status_update` with `status: "COMPLETE"` for `BUSINESS_UNDERSTANDING` fires every time the reasoning node is re-entered, not just the first time.

**Root Cause**: The reasoning node unconditionally emits stage completion for BU when it finishes, even on subsequent invocations (after data retrieval, after analysis, etc.).

**Fix**: Track completed stages in state. Only emit stage_complete for a stage if it hasn't been emitted before:
```python
# Add to state schema (if not already present)
completed_stages = list(state.get("completed_stages", []))

# In _reason_node, only emit stage completion once
if current_stage not in completed_stages:
    await self._emit_event(state, "status_update", current_stage, {
        "status": "COMPLETE",
        "message": f"{current_stage} complete"
    })
    completed_stages.append(current_stage)

# Return completed_stages in state update
return {**state, "completed_stages": completed_stages}
```

This also fixes Issue 5 for the completion events — each stage gets exactly one COMPLETE event.

**File**: `backend/app/services/agent/langgraph_workflow.py`

---

### Issue 8: No Report Rendered in DEPLOYMENT Stage (P1 — High)

**Problem**: The final report is written to a file but never emitted as a `render_output` event. The user never sees the report in the UI.

**Root Cause**: `reporting.py` generates a full markdown report and writes it to disk, but only emits a summary render_output if model results exist. The comprehensive report (which is always generated) is never emitted.

**Fix**: In `reporting.py`, after generating the full report, emit it as a `render_output` event:
```python
# After writing report to file
report_content = full_report_markdown  # the complete report string

await self.emit_event(state, "render_output", "DEPLOYMENT", {
    "mime_type": "text/markdown",
    "content": report_content,
})
```

**Important**: The report should ALWAYS be rendered, not only when model results exist. Even a basic analysis (EDA + indicators) should produce a visible report. Check the condition that gates report rendering and make it unconditional — if a report was generated, render it.

Also verify the report content is meaningful: it should include at minimum the query summary, data range, key findings from EDA, and any analysis results (sentiment, correlation, etc.).

**File**: `backend/app/services/agent/agents/reporting.py`

---

### Issue 9: MODELING/EVALUATION Skipped Silently (P1 — High)

**Problem**: User asks "build a model to predict BTC price" → MODELING and EVALUATION stages are skipped, workflow goes straight to DEPLOYMENT.

**Root Cause**: `_route_after_reasoning()` in `langgraph_workflow.py` uses keyword matching to decide the next node. It looks for keywords like "data" or "fetch" to route to data retrieval, but doesn't properly use `scope_interpretation.analysis_type` to determine whether MODELING should be included.

**Fix**: Use `scope_interpretation` from state to determine routing:
```python
def _route_after_reasoning(self, state):
    scope = state.get("scope_interpretation", {})
    analysis_type = scope.get("analysis_type", "")
    
    # Check scope_interpretation for required workflow stages
    requires_modeling = analysis_type.lower() in [
        "prediction", "forecasting", "modeling", "classification",
        "regression", "machine_learning", "ml"
    ]
    
    # Determine which stages have been completed
    completed = state.get("completed_stages", [])
    
    # Route based on what's been done and what's needed
    if "DATA_ACQUISITION" not in completed:
        return "data_retrieval"
    
    if "EXPLORATION" not in completed:
        return "data_analysis"
    
    if requires_modeling and "MODELING" not in completed:
        return "modeling"
    
    if requires_modeling and "EVALUATION" not in completed:
        return "evaluation"
    
    return "reporting"
```

**IMPORTANT**: This fix depends on `completed_stages` being maintained in state (Issue 6). Implement Issues 5, 6, and 9 together — they share the `completed_stages` tracking.

**File**: `backend/app/services/agent/langgraph_workflow.py`

---

## Implementation Order

1. Issue 6 first — add `completed_stages` tracking to state (foundation for 5 and 9)
2. Issue 5 — fix stage attribution using `completed_stages`
3. Issue 9 — fix routing using `scope_interpretation` and `completed_stages`
4. Issue 3 — add goal-aware quality validation warnings
5. Issue 8 — fix report rendering in reporting.py

## Testing Protocol

You cannot run integration tests locally. Verify correctness by:

1. **Code tracing**: For each issue, trace the code path from input to output. Ensure the fix connects the broken wire.
2. **State schema**: Ensure `completed_stages` is a valid key in the LangGraph state. Check the `AgentState` TypedDict definition — add `completed_stages: list[str]` if missing.
3. **Existing behavior**: Your changes must not break the EXISTING happy path (BTC price analysis routing). The fixed routing must be backwards-compatible — a simple "analyze BTC" should still work without MODELING.
4. **Regression safety**: The `_route_after_reasoning` fix must handle ALL existing routing cases. Don't remove non-scope routes — add scope-based routing as the primary path with keyword matching as fallback.

Post-merge integration tests (run by Supervisor):
```
# Scenario 1: Stage attribution
python scripts/lab_driver.py auto --goal "Analyze BTC price trends for the last 7 days" --timeout 300
# Expect: Each event shows correct stage (BU→BU, DATA_ACQ→DATA_ACQ, etc.)

# Scenario 2: No duplicate BU complete
# Same query — expect exactly ONE "COMPLETE" event per stage

# Scenario 3: Goal-aware quality warnings
python scripts/lab_driver.py auto --goal "Analyse correlation between bitcoin price and sentiment" --timeout 300
# Expect: WARNING event in PREPARATION about missing sentiment data

# Scenario 4: Report always renders
# Any query — expect render_output event in DEPLOYMENT with text/markdown mime type

# Scenario 5: MODELING routing
python scripts/lab_driver.py auto --goal "Build a model to predict BTC price using sentiment" --timeout 300
# Expect: MODELING and EVALUATION stages appear in event stream

# Scenario 6: Regression — simple analysis skips MODELING
python scripts/lab_driver.py auto --goal "Analyze BTC price trends for the last 7 days" --timeout 300
# Expect: No MODELING stage — straight from EXPLORATION to DEPLOYMENT
```

## Contract Compliance

- All emitted events must follow the API_CONTRACTS.md v1.2 wrapper schema.
- Valid event_types: `stream_chat`, `status_update`, `render_output`, `action_request`, `error`
- Valid stages: `BUSINESS_UNDERSTANDING`, `DATA_ACQUISITION`, `PREPARATION`, `EXPLORATION`, `MODELING`, `EVALUATION`, `DEPLOYMENT`
- status_update payloads: `{ "status": "PENDING|ACTIVE|COMPLETE|STALE|AWAITING_APPROVAL|DONE|WARNING", "message": "string", "task_id": "string (optional)" }`
- render_output payloads: `{ "mime_type": "text/markdown | application/vnd.plotly.v1+json | image/png | application/json+blueprint | application/json+tearsheet", "content": "any" }`
- If you encounter an impossible constraint, write a `CONTRACT_RFC.md` and halt.

## Commit Protocol

1. Make all changes.
2. Verify by code tracing that no existing happy path is broken.
3. Commit with message: `fix(workflow): stage tracking, goal-aware routing, quality warnings, report rendering`
4. Notify: "Graph branch ready for merge."
