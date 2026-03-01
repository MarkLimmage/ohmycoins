"""
Alert management API routes.

Provides CRUD operations for alert rules and viewing alert history.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import (
    AlertLog,
    AlertLogsPublic,
    AlertRule,
    AlertRuleCreate,
    AlertRulePublic,
    AlertRulesPublic,
    AlertRuleUpdate,
    User,
)
from app.services.alerting import AlertService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/rules", response_model=AlertRulesPublic)
def list_alert_rules(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    _current_user: User = Depends(get_current_active_superuser),
) -> AlertRulesPublic:
    """List all alert rules (paginated)."""
    statement = select(AlertRule).offset(skip).limit(limit)
    rules = session.exec(statement).all()

    count_statement = select(AlertRule)
    count = len(session.exec(count_statement).all())

    return AlertRulesPublic(data=rules, count=count)


@router.post("/rules", response_model=AlertRulePublic)
def create_alert_rule(
    rule_create: AlertRuleCreate,
    session: SessionDep,
    _current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """Create a new alert rule."""
    rule = AlertRule(**rule_create.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=AlertRulePublic)
def update_alert_rule(
    rule_id: str,
    rule_update: AlertRuleUpdate,
    session: SessionDep,
    _current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """Update an alert rule."""
    rule = session.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    # Update only provided fields
    update_data = rule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_alert_rule(
    rule_id: str,
    session: SessionDep,
    _current_user: User = Depends(get_current_active_superuser),
) -> dict[str, str]:
    """Delete an alert rule."""
    rule = session.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    session.delete(rule)
    session.commit()
    return {"message": "Alert rule deleted"}


@router.get("/log", response_model=AlertLogsPublic)
def list_alert_log(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    alert_type: str | None = Query(None),
    severity: str | None = Query(None),
    _current_user: User = Depends(get_current_active_superuser),
) -> AlertLogsPublic:
    """List alert history (paginated, filterable by type/severity)."""
    statement = select(AlertLog)

    if alert_type:
        statement = statement.where(AlertLog.alert_type == alert_type)
    if severity:
        statement = statement.where(AlertLog.severity == severity)

    statement = statement.order_by(AlertLog.created_at.desc()).offset(skip).limit(limit)  # type: ignore[attr-defined]
    logs = session.exec(statement).all()

    # Get total count for pagination
    count_statement = select(AlertLog)
    if alert_type:
        count_statement = count_statement.where(AlertLog.alert_type == alert_type)
    if severity:
        count_statement = count_statement.where(AlertLog.severity == severity)

    count = len(session.exec(count_statement).all())

    return AlertLogsPublic(data=logs, count=count)


@router.post("/test")
async def send_test_alert(
    session: SessionDep,
    _current_user: User = Depends(get_current_active_superuser),
) -> dict[str, Any]:
    """Send a test alert to verify channel configuration."""
    # Create test payload
    test_payload = {
        "type": "anomaly_severity",
        "severity": "HIGH",
        "count": 1,
        "coins": ["TEST"],
        "summary": "This is a test alert from OMC Alerting Service.",
        "timestamp": "2026-03-01T00:00:00",
    }

    # Process alert using AlertService
    alert_service = AlertService(session=session)
    result = await alert_service.process_alert(test_payload)

    return {
        "success": result.success,
        "message": result.message,
        "channels_dispatched": result.channels_dispatched,
        "error": result.error,
    }
