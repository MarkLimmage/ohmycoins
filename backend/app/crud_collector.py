import uuid
from sqlmodel import Session, select
from app.models import Collector, CollectorCreate, CollectorUpdate

def create_collector(*, session: Session, collector_create: CollectorCreate) -> Collector:
    db_obj = Collector.model_validate(collector_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def get_collector(*, session: Session, collector_id: uuid.UUID) -> Collector | None:
    return session.get(Collector, collector_id)

def get_collectors(*, session: Session, skip: int = 0, limit: int = 100) -> list[Collector]:
    statement = select(Collector).offset(skip).limit(limit)
    return session.exec(statement).all()

def update_collector(*, session: Session, db_collector: Collector, collector_in: CollectorUpdate) -> Collector:
    collector_data = collector_in.model_dump(exclude_unset=True)
    db_collector.sqlmodel_update(collector_data)
    session.add(db_collector)
    session.commit()
    session.refresh(db_collector)
    return db_collector

def delete_collector(*, session: Session, db_collector: Collector) -> Collector:
    session.delete(db_collector)
    session.commit()
    return db_collector
