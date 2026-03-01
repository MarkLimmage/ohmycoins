# mypy: ignore-errors
import uuid
from collections.abc import Sequence

from sqlmodel import Session, select

from app.models import TradeAudit, TradeAuditCreate


def create_trade_audit(
    *, session: Session, trade_audit_create: TradeAuditCreate
) -> TradeAudit:
    db_obj = TradeAudit.model_validate(trade_audit_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_trade_audits(
    *, session: Session, skip: int = 0, limit: int = 100
) -> Sequence[TradeAudit]:
    statement = (
        select(TradeAudit)
        .order_by(TradeAudit.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()


def get_trade_audit(
    *, session: Session, trade_audit_id: uuid.UUID
) -> TradeAudit | None:
    return session.get(TradeAudit, trade_audit_id)
