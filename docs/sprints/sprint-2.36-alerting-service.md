# Sprint 2.36 — Track B: Alerting Service

> **Author**: The Architect
> **Date**: 2026-02-27
> **Status**: READY FOR IMPLEMENTATION
> **Depends on**: Track A (anomaly detection + alert bridge) — SHIPPED

---

## Problem Statement

The alert bridge in `ReportingAgent` populates `state["alert_triggered"]` and `state["alert_payload"]` when HIGH severity anomalies are detected, but nothing consumes this payload. Alerts are silently lost after the workflow completes.

Track B builds the Alerting Service to:
1. Consume alert payloads from the LangGraph workflow
2. Evaluate them against configurable alert rules
3. Dispatch notifications via Slack and/or email

---

## Existing Infrastructure

These already exist and should be reused:

| Component | Location | What it does |
|---|---|---|
| `send_slack_alert()` | `backend/app/utils/notifications.py` | Sends message to Slack via webhook URL |
| `SLACK_WEBHOOK_URL` | `backend/app/core/config.py:161` | Slack webhook config (nullable) |
| `SMTP_*` settings | `backend/app/core/config.py:91-98` | Email config (host, port, user, password) |
| `emails_enabled` | `backend/app/core/config.py:110` | Property: True if SMTP_HOST and EMAILS_FROM_EMAIL set |
| `TradingSafetyManager` | `backend/app/services/trading/safety.py` | Already calls `send_slack_alert()` for kill switch events |

---

## Design: Alert Payload Shape (From Track A)

The alert bridge in `reporting.py:171-183` produces this payload:

```python
{
    "type": "anomaly_severity",       # Alert type identifier
    "severity": "HIGH",               # Severity level
    "count": 2,                       # Number of HIGH severity anomalies
    "coins": ["BTC", "ETH"],          # Affected coins
    "summary": "7 anomalies detected across 2 coins. 2 HIGH severity events require attention.",
    "timestamp": "2026-02-27T14:30:00"  # ISO timestamp
}
```

---

## Design: AlertService Class

Create `backend/app/services/alerting.py`:

```python
class AlertService:
    """Processes alert payloads and dispatches notifications."""

    async def process_alert(self, payload: dict[str, Any]) -> AlertResult:
        """
        Main entry point. Called after LangGraph workflow completes.
        1. Validate payload shape
        2. Check against alert rules (severity threshold, cooldown)
        3. Dispatch to configured channels (Slack, email)
        4. Log the alert to DB
        """

    async def dispatch_slack(self, payload: dict[str, Any]) -> bool:
        """Format and send Slack notification using existing send_slack_alert()."""

    async def dispatch_email(self, payload: dict[str, Any], recipients: list[str]) -> bool:
        """Format and send email notification using existing SMTP config."""

    def format_alert_message(self, payload: dict[str, Any]) -> str:
        """
        Format payload into human-readable message.
        Example:
          ⚠ HIGH Severity Alert: 2 anomalies detected
          Coins: BTC, ETH
          7 anomalies detected across 2 coins. 2 HIGH severity events require attention.
        """
```

---

## Design: AlertRule Model

Add to `backend/app/models.py`:

```python
class AlertRule(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    alert_type: str = Field(max_length=50)          # e.g., "anomaly_severity"
    min_severity: str = Field(default="HIGH", max_length=20)  # LOW, MEDIUM, HIGH
    channels: list[str] = Field(sa_column=Column(JSON))  # ["slack", "email"]
    recipients: list[str] = Field(sa_column=Column(JSON), default=[])  # email addresses
    cooldown_minutes: int = Field(default=30)        # Min time between duplicate alerts
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

```python
class AlertLog(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rule_id: uuid.UUID | None = Field(default=None, foreign_key="alertrule.id")
    alert_type: str = Field(max_length=50)
    severity: str = Field(max_length=20)
    payload: dict = Field(sa_column=Column(JSON))
    channels_dispatched: list[str] = Field(sa_column=Column(JSON))
    success: bool = Field(default=True)
    error_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Important**: After adding models, generate an Alembic migration:
```bash
docker compose exec backend alembic revision --autogenerate -m "add alert_rule and alert_log tables"
docker compose exec backend alembic upgrade head
```

---

## Design: API Routes

Create `backend/app/api/routes/alerts.py`:

| Method | Path | Description |
|---|---|---|
| `GET /api/v1/alerts/rules` | List all alert rules |
| `POST /api/v1/alerts/rules` | Create alert rule |
| `PATCH /api/v1/alerts/rules/{id}` | Update alert rule (toggle enabled, change channels) |
| `DELETE /api/v1/alerts/rules/{id}` | Delete alert rule |
| `GET /api/v1/alerts/log` | List alert history (paginated, filterable by type/severity) |
| `POST /api/v1/alerts/test` | Send a test alert to verify channel config |

Register in `backend/app/api/main.py`.

---

## Design: LangGraph Integration

In `langgraph_workflow.py`, modify the `_finalize_node` to call the AlertService after workflow completion:

```python
def _finalize_node(self, state: AgentState) -> AgentState:
    # ... existing finalize logic ...

    # Sprint 2.36: Process alerts
    if state.get("alert_triggered") and state.get("alert_payload"):
        # Fire-and-forget: don't block workflow completion on alert dispatch
        import asyncio
        asyncio.create_task(
            alert_service.process_alert(state["alert_payload"])
        )

    return state
```

**Alternative** (simpler, synchronous): Add a new `_dispatch_alerts_node` after finalize in the graph, so alerts are part of the workflow rather than fire-and-forget. This is more testable.

---

## Design: Cooldown Logic

To prevent alert spam:

```python
async def _check_cooldown(self, rule: AlertRule, payload: dict) -> bool:
    """Return True if alert should be sent (cooldown expired)."""
    last_alert = await get_last_alert_for_rule(rule.id)
    if last_alert is None:
        return True
    elapsed = datetime.utcnow() - last_alert.created_at
    return elapsed.total_seconds() > (rule.cooldown_minutes * 60)
```

---

## Test Requirements

1. `test_alert_service_process` — AlertService processes a valid payload and dispatches to Slack
2. `test_alert_service_cooldown` — Second alert within cooldown period is suppressed
3. `test_alert_service_email` — Email dispatch with SMTP config
4. `test_alert_rule_crud` — API CRUD operations for alert rules
5. `test_alert_log_created` — AlertLog record created after dispatch
6. `test_alert_test_endpoint` — POST /alerts/test sends test notification
7. `test_finalize_triggers_alert` — LangGraph finalize node calls AlertService when alert_triggered=True

---

## Implementation Order

1. Add `AlertRule` and `AlertLog` models + migration
2. Create `AlertService` class with Slack dispatch (reuse existing util)
3. Add email dispatch
4. Create API routes for rule management + alert log
5. Wire into LangGraph finalize node
6. Write tests
7. Seed a default alert rule (HIGH severity → Slack)

---

## Files to Create/Modify

| File | Action |
|---|---|
| `backend/app/models.py` | Add AlertRule, AlertLog models |
| `backend/app/services/alerting.py` | **NEW** — AlertService class |
| `backend/app/api/routes/alerts.py` | **NEW** — Alert API routes |
| `backend/app/api/main.py` | Register alerts router |
| `backend/app/services/agent/langgraph_workflow.py` | Wire alert dispatch into finalize |
| `backend/app/utils/notifications.py` | Add `send_email_alert()` alongside existing `send_slack_alert()` |
| `backend/tests/services/test_alerting.py` | **NEW** — AlertService tests |
| `backend/tests/api/routes/test_alerts.py` | **NEW** — Alert API route tests |
| `alembic/versions/xxx_add_alert_tables.py` | **NEW** — Auto-generated migration |
