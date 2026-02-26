# Sprint 2.36 — Analyst → Reporting Anomaly Handoff Design

> **Author**: The Architect
> **Date**: 2026-02-26
> **Status**: APPROVED — Dev-1 (Track B) to implement

---

## Problem Statement

The current LangGraph workflow has no path from `analyze_data` to `generate_report` for non-ML goals. If the Analyst detects anomalies but the user didn't request model training, the workflow routes straight to `finalize`, **skipping the Reporting node entirely**. Anomaly findings are silently lost.

Sprint 2.36 introduces Isolation Forest anomaly detection. This data MUST flow through the Reporting node to:
1. Generate human-readable anomaly summaries
2. Trigger alerts when HIGH severity anomalies are found (consumed by Track C's Alerting Service)

---

## Design: State Changes

### New `AgentState` fields (add to `langgraph_workflow.py`):

```python
# Sprint 2.36 — Anomaly Detection
anomaly_detected: bool           # True if any anomalies above threshold
anomaly_summary: str | None      # Human-readable one-liner for messages

# Sprint 2.36 — Alert Bridge (consumed by Alerting Service)
alert_triggered: bool            # True if HIGH severity anomalies found
alert_payload: dict[str, Any] | None  # Structured payload for alerting service
```

**Important**: Anomaly detection output goes INTO `analysis_results["anomaly_detection"]` (not a separate top-level field). This ensures it flows naturally through `generate_summary()` and `generate_recommendations()` which already consume `analysis_results`.

### Shape of `analysis_results["anomaly_detection"]`:

```python
{
    "model": "IsolationForest",
    "contamination": 0.05,
    "coins_analyzed": ["BTC", "ETH"],
    "total_anomalies": 7,
    "anomalies": [
        {
            "timestamp": "2026-02-25T14:30:00Z",
            "coin": "BTC",
            "price": 52340.0,
            "anomaly_score": -0.87,
            "is_anomaly": True,
            "severity": "HIGH"  # LOW: score < -0.5, MEDIUM: < -0.7, HIGH: < -0.9
        }
    ],
    "severity_distribution": {"LOW": 3, "MEDIUM": 2, "HIGH": 2},
    "summary": "7 anomalies detected across 2 coins. 2 HIGH severity events require attention."
}
```

---

## Design: Routing Change

### Current `_route_after_analysis` signature:
```python
def _route_after_analysis(self, state) -> Literal["train", "finalize", "reason", "error"]:
```

### New signature:
```python
def _route_after_analysis(self, state) -> Literal["train", "report", "finalize", "reason", "error"]:
```

### New routing logic:
```python
if not state.get("analysis_completed"):
    return "error"

user_goal = state.get("user_goal", "").lower()
is_ml_goal = any(kw in user_goal for kw in ["predict", "model", "forecast", "train", "ml"])

if is_ml_goal:
    return "train"
elif state.get("anomaly_detected"):
    return "report"  # NEW: anomalies bypass finalize, go to report
else:
    return "finalize"
```

### New edge in `_build_graph`:
Add `"report"` to the `_route_after_analysis` conditional edges map:
```python
workflow.add_conditional_edges(
    "analyze_data",
    self._route_after_analysis,
    {
        "train": "train_model",
        "report": "generate_report",  # NEW
        "finalize": "finalize",
        "reason": "reason",
        "error": "handle_error",
    }
)
```

---

## Design: Analyst Agent Changes

In `DataAnalystAgent.execute()`, after the existing analysis blocks (technical indicators, sentiment, on-chain, catalyst), add:

```python
# Sprint 2.36: Anomaly Detection
if "price_data" in retrieved_data and retrieved_data["price_data"]:
    if ("anomaly" in user_goal.lower() or
        analysis_params.get("include_anomaly_detection", True)):
        from ..tools.anomaly_detection import detect_price_anomalies
        anomaly_result = detect_price_anomalies(
            retrieved_data["price_data"],
            contamination=analysis_params.get("anomaly_contamination", 0.05)
        )
        analysis_results["anomaly_detection"] = anomaly_result
        state["anomaly_detected"] = anomaly_result.get("total_anomalies", 0) > 0
        state["anomaly_summary"] = anomaly_result.get("summary", "")
```

---

## Design: Reporting Agent Changes

In `ReportingAgent.execute()`, the existing code already passes `analysis_results` to all four reporting tools. Changes needed:

1. **`generate_summary()`** — Add anomaly section:
   ```python
   if "anomaly_detection" in analysis_results:
       ad = analysis_results["anomaly_detection"]
       summary_lines.append("\n## Anomaly Detection\n")
       summary_lines.append(f"- **Model:** {ad.get('model', 'IsolationForest')}")
       summary_lines.append(f"- **Total Anomalies:** {ad.get('total_anomalies', 0)}")
       severity_dist = ad.get("severity_distribution", {})
       if severity_dist.get("HIGH", 0) > 0:
           summary_lines.append(f"- **⚠ HIGH Severity:** {severity_dist['HIGH']} events")
   ```

2. **`generate_recommendations()`** — Add anomaly-based recommendations:
   ```python
   if "anomaly_detection" in analysis_results:
       ad = analysis_results["anomaly_detection"]
       if ad.get("severity_distribution", {}).get("HIGH", 0) > 0:
           recommendations.append(
               "**URGENT**: HIGH severity price anomalies detected. "
               "Review positions in affected coins and consider tightening stop-losses."
           )
   ```

3. **Alert Bridge** — At the end of `ReportingAgent.execute()`, after setting `reporting_completed`:
   ```python
   # Sprint 2.36: Alert Bridge
   anomaly_data = analysis_results.get("anomaly_detection", {})
   high_severity_count = anomaly_data.get("severity_distribution", {}).get("HIGH", 0)
   if high_severity_count > 0:
       state["alert_triggered"] = True
       state["alert_payload"] = {
           "type": "anomaly_severity",
           "severity": "HIGH",
           "count": high_severity_count,
           "coins": list(set(a["coin"] for a in anomaly_data.get("anomalies", []) if a.get("severity") == "HIGH")),
           "summary": anomaly_data.get("summary", ""),
           "timestamp": datetime.utcnow().isoformat(),
       }
   ```

---

## Design: New Tool — `anomaly_detection.py`

Create `backend/app/services/agent/tools/anomaly_detection.py`:

```python
def detect_price_anomalies(
    price_data: list[dict],
    contamination: float = 0.05
) -> dict[str, Any]:
    """
    Detect anomalies in CoinPrice time series using Isolation Forest.

    Args:
        price_data: List of price records with 'timestamp', 'coin', 'price' keys
        contamination: Expected proportion of anomalies (default 5%)

    Returns:
        Dict with anomaly results, severity distribution, and summary
    """
```

**Implementation notes**:
- Use `sklearn.ensemble.IsolationForest`
- Group by coin, fit per-coin model
- Feature engineering: price, price_change_pct, volume (if available)
- Severity thresholds on `decision_function()` output:
  - score < -0.5 → LOW
  - score < -0.7 → MEDIUM
  - score < -0.9 → HIGH
- sklearn is already in the backend's requirements (used by model_training_tools)

---

## Integration Points

| Component | Produces | Consumes |
|---|---|---|
| `detect_price_anomalies()` tool | `analysis_results["anomaly_detection"]` | `price_data` from Data Retrieval |
| `DataAnalystAgent` | `state["anomaly_detected"]`, `state["anomaly_summary"]` | Tool output |
| `_route_after_analysis` | Routing decision | `state["anomaly_detected"]` |
| `ReportingAgent` | Alert bridge payload | `analysis_results["anomaly_detection"]` |
| Track C Alerting Service | Alert dispatch | `state["alert_triggered"]`, `state["alert_payload"]` |

---

## Initialization Defaults

Add to `_initialize_node`:
```python
state["anomaly_detected"] = False
state["anomaly_summary"] = None
state["alert_triggered"] = False
state["alert_payload"] = None
```

---

## Test Requirements

1. `test_detect_price_anomalies` — unit test for the tool with synthetic data
2. `test_analyst_anomaly_flow` — analyst agent sets `anomaly_detected=True` when anomalies found
3. `test_route_after_analysis_with_anomalies` — routes to "report" when `anomaly_detected=True` and non-ML goal
4. `test_reporting_anomaly_section` — report includes anomaly summary
5. `test_alert_bridge` — `alert_triggered=True` when HIGH severity anomalies present
