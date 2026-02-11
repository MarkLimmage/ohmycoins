import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud_risk
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    RiskRule,
    RiskRuleCreate,
    RiskRulePublic,
    RiskRules,
    RiskRuleUpdate,
    AuditLogPublic,
    AuditLogs,
    SystemSettingPublic,
    Message,
)

router = APIRouter()


# -----------------------------------------------------------------------------
# Risk Rules
# -----------------------------------------------------------------------------
@router.get("/rules", response_model=RiskRules)
def read_risk_rules(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve risk rules.
    """
    # Verify superuser for now? Or just authenticated?
    # get_current_active_superuser(current_user)
    
    count_statement = select(func.count()).select_from(RiskRule)
    count = session.exec(count_statement).one()
    
    rules = crud_risk.get_risk_rules(session=session, skip=skip, limit=limit)
    return RiskRules(data=rules, count=count)


@router.post("/rules", response_model=RiskRulePublic)
def create_risk_rule(
    *, session: SessionDep, current_user: CurrentUser, risk_rule_in: RiskRuleCreate
) -> Any:
    """
    Create new risk rule.
    """
    get_current_active_superuser(current_user)
    risk_rule = crud_risk.create_risk_rule(session=session, risk_rule_create=risk_rule_in)
    return risk_rule


@router.put("/rules/{risk_rule_id}", response_model=RiskRulePublic)
def update_risk_rule(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    risk_rule_id: uuid.UUID,
    risk_rule_in: RiskRuleUpdate,
) -> Any:
    """
    Update a risk rule.
    """
    get_current_active_superuser(current_user)
    risk_rule = crud_risk.get_risk_rule(session=session, risk_rule_id=risk_rule_id)
    if not risk_rule:
        raise HTTPException(status_code=404, detail="Risk rule not found")
    risk_rule = crud_risk.update_risk_rule(session=session, db_risk_rule=risk_rule, risk_rule_in=risk_rule_in)
    return risk_rule


@router.delete("/rules/{risk_rule_id}", response_model=Message)
def delete_risk_rule(
    *, session: SessionDep, current_user: CurrentUser, risk_rule_id: uuid.UUID
) -> Any:
    """
    Delete a risk rule.
    """
    get_current_active_superuser(current_user)
    risk_rule = crud_risk.get_risk_rule(session=session, risk_rule_id=risk_rule_id)
    if not risk_rule:
        raise HTTPException(status_code=404, detail="Risk rule not found")
    crud_risk.delete_risk_rule(session=session, db_risk_rule=risk_rule)
    return Message(message="Risk rule deleted successfully")


# -----------------------------------------------------------------------------
# Kill Switch
# -----------------------------------------------------------------------------
@router.get("/kill-switch", response_model=SystemSettingPublic)
def get_kill_switch_status(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Get current kill switch status.
    """
    setting = crud_risk.get_system_setting(session=session, key="kill_switch")
    if not setting:
        # Default to inactive if not set
        return SystemSettingPublic(key="kill_switch", value={"active": False}, updated_at=func.now())
    return setting


@router.post("/kill-switch", response_model=SystemSettingPublic)
def set_kill_switch(
    *, session: SessionDep, current_user: CurrentUser, active: bool
) -> Any:
    """
    Enable or disable the global kill switch.
    """
    get_current_active_superuser(current_user)
    setting = crud_risk.set_system_setting(
        session=session,
        key="kill_switch",
        value={"active": active},
        description="Global Kill Switch - Halts all trading when active"
    )
    
    # Log audit
    crud_risk.create_audit_log(
        session=session,
        audit_log_create=crud_risk.AuditLogCreate(
            event_type="kill_switch_toggle",
            severity="critical",
            details={"active": active},
            user_id=current_user.id
        )
    )
    
    return setting


# -----------------------------------------------------------------------------
# Audit Logs
# -----------------------------------------------------------------------------
@router.get("/audit-logs", response_model=AuditLogs)
def read_audit_logs(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve audit logs.
    """
    get_current_active_superuser(current_user)
    logs = crud_risk.get_audit_logs(session=session, skip=skip, limit=limit)
    # This count is inefficient for large tables, but fine for now
    count_statement = select(func.count()).select_from(crud_risk.AuditLog)
    count = session.exec(count_statement).one()
    return AuditLogs(data=logs, count=count)
