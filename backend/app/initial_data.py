import logging

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import AlertRule, Collector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_collectors(session: Session) -> None:
    logger.info("Checking for required data collectors...")
    collectors_to_seed = [
        {
            "name": "CoinspotExchange",
            "description": "Primary Price Data (Coinspot)",
            "plugin_name": "CoinspotExchange",
            "is_enabled": True,
            "schedule_cron": "* * * * *",  # Every minute
            "config": {
                "use_web_scraping": True,
                "max_retries": 3,
                "retry_delay": 5,
                "timeout": 30.0
            },
            "status": "active"
        },
    ]

    for seed_data in collectors_to_seed:
        # Check by name
        existing = session.exec(select(Collector).where(Collector.name == seed_data["name"])).first()
        if not existing:
            logger.info(f"Seeding collector: {seed_data['name']}")
            # Create the collector
            collector = Collector(**seed_data)
            session.add(collector)
            session.commit()  # Commit immediately to ensure it's saved
            session.refresh(collector)
            logger.info(f"Successfully seeded {seed_data['name']}")
        else:
            logger.info(f"Collector {seed_data['name']} already exists. Skipping.")


def seed_alert_rules(session: Session) -> None:
    logger.info("Checking for required alert rules...")
    alert_rules_to_seed = [
        {
            "name": "High Severity Anomalies to Slack",
            "alert_type": "anomaly_severity",
            "min_severity": "HIGH",
            "channels": ["slack"],
            "recipients": [],
            "cooldown_minutes": 30,
            "enabled": True,
        },
    ]

    for seed_data in alert_rules_to_seed:
        # Check by name
        existing = session.exec(
            select(AlertRule).where(AlertRule.name == seed_data["name"])
        ).first()
        if not existing:
            logger.info(f"Seeding alert rule: {seed_data['name']}")
            rule = AlertRule(**seed_data)
            session.add(rule)
            session.commit()
            session.refresh(rule)
            logger.info(f"Successfully seeded alert rule: {seed_data['name']}")
        else:
            logger.info(f"Alert rule {seed_data['name']} already exists. Skipping.")


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        seed_collectors(session)
        seed_alert_rules(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
