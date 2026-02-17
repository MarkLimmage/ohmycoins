from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models import AuditLog

# Adjust DB URI if running as script inside container if specific tweaks needed, but settings should load env
# Ensure we are using the internal DB URL
# settings.SQLALCHEMY_DATABASE_URI should be correct if env vars are set

def check_logs():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as session:
        logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5)).all()
        for _log in logs:
            pass

if __name__ == "__main__":
    check_logs()
