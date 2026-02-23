import logging

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Collector

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


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        seed_collectors(session)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
