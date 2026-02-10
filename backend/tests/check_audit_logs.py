from sqlmodel import Session, select, create_engine
from app.models import AuditLog
from app.core.config import settings

# Adjust DB URI if running as script inside container if specific tweaks needed, but settings should load env
# Ensure we are using the internal DB URL
# settings.SQLALCHEMY_DATABASE_URI should be correct if env vars are set

def check_logs():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as session:
        logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5)).all()
        print(f"\n--- Checking Last 5 Audit Logs ---")
        for log in logs:
            print(f"[{log.timestamp}] ACTION: {log.action} | SEVERITY: {log.severity}")
            print(f"Actor: {log.actor_id}")
            print(f"Details: {log.details}")
            print("-" * 30)

if __name__ == "__main__":
    check_logs()
