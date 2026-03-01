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
            "schedule_cron": "*/1 * * * *",
            "config": {
                "use_web_scraping": True,
                "max_retries": 3,
                "retry_delay": 5,
                "timeout": 30.0,
            },
            "status": "active",
        },
        {
            "name": "GlassChainWalker",
            "description": "On-chain metrics via public RPCs",
            "plugin_name": "GlassChainWalker",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {"chain": "ethereum", "mock_mode": False},
            "status": "idle",
        },
        {
            "name": "DeFiLlama",
            "description": "DeFi protocol TVL, fees, revenue",
            "plugin_name": "glass_defillama",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "NansenSmartMoney",
            "description": "Smart money wallet flow tracking",
            "plugin_name": "glass_nansen",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "CryptoPanicNews",
            "description": "Crypto news with sentiment (API)",
            "plugin_name": "news_cryptopanic",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "RedditSentiment",
            "description": "Reddit crypto community sentiment",
            "plugin_name": "human_reddit",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "NewscatcherNews",
            "description": "Aggregated news from 60k+ sources",
            "plugin_name": "human_newscatcher",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "HumanRSSCollector",
            "description": "RSS feed aggregator for crypto news",
            "plugin_name": "HumanRSSCollector",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {
                "feed_urls": [
                    "https://www.coindesk.com/arc/outboundfeeds/rss/",
                    "https://cointelegraph.com/rss",
                ]
            },
            "status": "idle",
        },
        {
            "name": "BeInCryptoNews",
            "description": "BeInCrypto news via RSS",
            "plugin_name": "news_beincrypto",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "CoinDeskNews",
            "description": "CoinDesk news via RSS",
            "plugin_name": "news_coindesk",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "CoinTelegraphNews",
            "description": "CoinTelegraph news via RSS",
            "plugin_name": "news_cointelegraph",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "CryptoSlateNews",
            "description": "CryptoSlate news via RSS",
            "plugin_name": "news_cryptoslate",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "DecryptNews",
            "description": "Decrypt news via RSS",
            "plugin_name": "news_decrypt",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "NewsBTCNews",
            "description": "NewsBTC news via RSS",
            "plugin_name": "news_newsbtc",
            "is_enabled": True,
            "schedule_cron": "*/15 * * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "SECFilings",
            "description": "SEC EDGAR regulatory filings",
            "plugin_name": "catalyst_sec",
            "is_enabled": True,
            "schedule_cron": "0 */6 * * *",
            "config": {},
            "status": "idle",
        },
        {
            "name": "CoinSpotAnnouncements",
            "description": "CoinSpot exchange announcements",
            "plugin_name": "catalyst_coinspot_announcements",
            "is_enabled": True,
            "schedule_cron": "0 */1 * * *",
            "config": {},
            "status": "idle",
        },
    ]

    for seed_data in collectors_to_seed:
        # Check by name
        existing = session.exec(
            select(Collector).where(Collector.name == seed_data["name"])
        ).first()
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
