import uuid
from typing import Any

from fastapi import APIRouter
from sqlmodel import func, select

from app import crud_trade_audit
from app.api.deps import CurrentUser, SessionDep
from app.models import TradeAudit, TradeAuditCreate, TradeAuditPublic, TradeAudits

router = APIRouter()

@router.get("/", response_model=TradeAudits)
def read_trade_audits(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve trade audits.
    """
    count_statement = select(func.count()).select_from(TradeAudit)
    count = session.exec(count_statement).one()
    
    trade_audits = crud_trade_audit.get_trade_audits(session=session, skip=skip, limit=limit)
    return TradeAudits(data=trade_audits, count=count)

@router.post("/", response_model=TradeAuditPublic)
def create_trade_audit(
    *, session: SessionDep, current_user: CurrentUser, trade_audit_in: TradeAuditCreate
) -> Any:
    """
    Create new trade audit record.
    """
    trade_audit = crud_trade_audit.create_trade_audit(session=session, trade_audit_create=trade_audit_in)
    return trade_audit
