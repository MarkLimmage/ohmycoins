# Current Sprint: 2.36

**Status**: IN PROGRESS
**Objective**: Advanced Analytics & Alerting
**Previous Sprint**: 2.35 (Data Integrity & Dashboard Polish - COMPLETED)

## Status
- **Data Collections**: Stabilized and Verified.
- **Dashboard**: Production-ready for monitoring.
- **Anomaly Detection**: Shipped — IsolationForest pipeline integrated into LangGraph workflow.
- **Data Explorer**: Shipped — scaffold route with filters and charts at /data-explorer.

## Tasks
1. [x] **Track A (Data Science)**: Implement Anomaly Detection (Isolation Forest) on CoinPrice.
   - `anomaly_detection.py` tool (per-coin IsolationForest, LOW/MEDIUM/HIGH severity)
   - 4 new AgentState fields (`anomaly_detected`, `anomaly_summary`, `alert_triggered`, `alert_payload`)
   - DataAnalystAgent integration + `_route_after_analysis` → "report" route
   - ReportingAgent anomaly summary, recommendations, and alert bridge
   - 24 tests passing across 3 test files
2. [ ] **Track B (Backend)**: Implement Alerting Service (Email/Slack on Error Threshold).
   - Blocked on: nothing — alert bridge payload (`state["alert_payload"]`) is ready to consume
3. [x] **Track C (Frontend)**: Data Explorer View (Advanced filtering/Charting).
   - Scaffold at `frontend/src/routes/_layout/data-explorer.tsx`
   - Coin selector, date range, ledger filters + Recharts line/bar charts
   - Next: wire to backend price/collector APIs

## Shipped Commits
- `b886b14` docs: add agent bootstrap & delegation protocol
- `644b099` feat(sprint-2.36): anomaly detection pipeline, analyst-reporting handoff, data explorer
