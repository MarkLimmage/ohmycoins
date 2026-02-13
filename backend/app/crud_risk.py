import uuid
from typing import Sequence

from sqlmodel import Session, select

from app.models import (
    RiskRule,
    RiskRuleCreate,
    RiskRuleUpdate,
    AuditLog,
    AuditLogCreate,
    SystemSetting,
    SystemSettingCreate,
    SystemSettingUpdate,
)


# Risk Rules
def create_risk_rule(*, session: Session, risk_rule_create: RiskRuleCreate) -> RiskRule:
    db_obj = RiskRule.model_validate(risk_rule_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_risk_rules(*, session: Session, skip: int = 0, limit: int = 100) -> Sequence[RiskRule]:
    statement = select(RiskRule).offset(skip).limit(limit)
    return session.exec(statement).all()


def get_risk_rule(*, session: Session, risk_rule_id: uuid.UUID) -> RiskRule | None:
    return session.get(RiskRule, risk_rule_id)


def update_risk_rule(
    *, session: Session, db_risk_rule: RiskRule, risk_rule_in: RiskRuleUpdate
) -> RiskRule:
    risk_rule_data = risk_rule_in.model_dump(exclude_unset=True)
    db_risk_rule.sqlmodel_update(risk_rule_data)
    session.add(db_risk_rule)
    session.commit()
    session.refresh(db_risk_rule)
    return db_risk_rule


def delete_risk_rule(*, session: Session, db_risk_rule: RiskRule) -> RiskRule:
    session.delete(db_risk_rule)
    session.commit()
    return db_risk_rule


# Audit Logs
def create_audit_log(*, session: Session, audit_log_create: AuditLogCreate) -> AuditLog:
    db_obj = AuditLog.model_validate(audit_log_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_audit_logs(*, session: Session, skip: int = 0, limit: int = 100, event_type: str | None = None) -> Sequence[AuditLog]:
    statement = select(AuditLog)
    if event_type:
        statement = statement.where(AuditLog.event_type == event_type)
    statement = statement.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    return session.exec(statement).all()


# System Settings
def get_system_setting(*, session: Session, key: str) -> SystemSetting | None:
    return session.get(SystemSetting, key)


def set_system_setting(
    *, session: Session, key: str, value: dict, description: str | None = None
) -> SystemSetting:
    db_obj = session.get(SystemSetting, key)
    if db_obj:
        db_obj.value = value
        if description:
            db_obj.description = description
        session.add(db_obj)
    else:
        db_obj = SystemSetting(key=key, value=value, description=description)
        session.add(db_obj)
    
    session.commit()
    session.refresh(db_obj)
    return db_obj
