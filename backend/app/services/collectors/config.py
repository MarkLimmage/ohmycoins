# mypy: ignore-errors
"""
Example configuration for Phase 2.5 comprehensive data collectors.

This module demonstrates how to register and start all collectors with the orchestrator.
"""

import logging

from app.services.collectors.catalyst import (
    CoinSpotAnnouncementsCollector,
    SECAPICollector,
)
from app.services.collectors.glass import DeFiLlamaCollector, NansenCollector
from app.services.collectors.human import (
    CryptoPanicCollector,
    NewscatcherCollector,
    RedditCollector,
)
from app.services.collectors.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


def setup_collectors() -> None:
    """
    Register all Phase 2.5 collectors with the orchestrator.
    
    This function should be called during application startup to initialize
    and schedule all data collectors.
    """
    orchestrator = get_orchestrator()

    logger.info("Setting up Phase 2.5 comprehensive data collectors...")

    # Glass Ledger: DeFiLlama Protocol Fundamentals
    # Collects daily at 2 AM UTC
    try:
        defillama = DeFiLlamaCollector()
        orchestrator.register_collector(
            defillama,
            schedule_type="cron",
            hour=2,
            minute=0,
        )
        logger.info("✓ Registered DeFiLlama collector (Glass Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register DeFiLlama collector: {str(e)}")

    # Human Ledger: CryptoPanic News Sentiment
    # Collects every 5 minutes
    try:
        # Note: Requires CRYPTOPANIC_API_KEY environment variable
        cryptopanic = CryptoPanicCollector()
        orchestrator.register_collector(
            cryptopanic,
            schedule_type="interval",
            minutes=5,
        )
        logger.info("✓ Registered CryptoPanic collector (Human Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register CryptoPanic collector: {str(e)}")
        logger.info("  Get a free API key at: https://cryptopanic.com/developers/api/")

    # Human Ledger: Newscatcher News Aggregation
    # Collects every 5 minutes
    try:
        # Note: Requires NEWSCATCHER_API_KEY environment variable (Tier 2 optional)
        newscatcher = NewscatcherCollector()
        orchestrator.register_collector(
            newscatcher,
            schedule_type="interval",
            minutes=5,
        )
        logger.info("✓ Registered Newscatcher collector (Human Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register Newscatcher collector: {str(e)}")
        logger.info("  Get an API key at: https://www.newscatcherapi.com/ ($10/month - Tier 2)")

    # Glass Ledger: Nansen Smart Money Tracking
    # Collects every 15 minutes
    try:
        # Note: Requires NANSEN_API_KEY environment variable (Tier 2 optional)
        nansen = NansenCollector()
        orchestrator.register_collector(
            nansen,
            schedule_type="interval",
            minutes=15,
        )
        logger.info("✓ Registered Nansen collector (Glass Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register Nansen collector: {str(e)}")
        logger.info("  Get an API key at: https://nansen.ai/ ($49/month - Tier 2)")

    # Catalyst Ledger: SEC API
    # Collects daily at 9 AM UTC (after market open)
    try:
        sec_api = SECAPICollector()
        orchestrator.register_collector(
            sec_api,
            schedule_type="cron",
            hour=9,
            minute=0,
        )
        logger.info("✓ Registered SEC API collector (Catalyst Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register SEC API collector: {str(e)}")

    # Catalyst Ledger: CoinSpot Announcements
    # Collects every hour for new announcements
    try:
        coinspot_announcements = CoinSpotAnnouncementsCollector()
        orchestrator.register_collector(
            coinspot_announcements,
            schedule_type="interval",
            hours=1,
        )
        logger.info("✓ Registered CoinSpot Announcements collector (Catalyst Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register CoinSpot Announcements collector: {str(e)}")

    # Human Ledger: Reddit API
    # Collects every 15 minutes for community sentiment
    try:
        reddit = RedditCollector()
        orchestrator.register_collector(
            reddit,
            schedule_type="interval",
            minutes=15,
        )
        logger.info("✓ Registered Reddit collector (Human Ledger)")
    except Exception as e:
        logger.error(f"✗ Failed to register Reddit collector: {str(e)}")

    # TODO: Add more collectors as they are implemented
    # - Enhanced CoinSpot Client (Exchange Ledger)
    #
    # Sprint 2.12 Status:
    # ✓ CryptoPanic - Implemented and registered
    # ✓ Newscatcher - Implemented and registered (Tier 2)
    # ✓ Nansen - Implemented and registered (Tier 2)

    logger.info("Phase 2.5 collectors setup complete")


def start_collection() -> None:
    """
    Start the collection orchestrator.
    
    All registered collectors will begin running according to their schedules.
    """
    orchestrator = get_orchestrator()
    orchestrator.start()
    logger.info("Collection orchestrator started")


def stop_collection() -> None:
    """
    Stop the collection orchestrator.
    
    All running collectors will be gracefully stopped.
    """
    orchestrator = get_orchestrator()
    orchestrator.stop()
    logger.info("Collection orchestrator stopped")


def get_collection_status() -> dict:
    """
    Get health status of all collectors.
    
    Returns:
        Dictionary containing orchestrator and collector statuses
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_health_status()
