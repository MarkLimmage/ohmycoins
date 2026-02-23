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
from app.collectors.strategies.exchange_coinspot import CoinspotExchangeCollector
from app.collectors.strategies.glass_chain_walker import GlassChainWalker
from app.collectors.strategies.human_rss import HumanRSSCollector
from app.services.collectors.strategy_adapter import StrategyAdapterCollector
from app.services.collectors.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


def setup_collectors() -> None:
    """
    Register available Phase 2.5 collectors with the orchestrator.
    
    This function discovers all available collector strategies but does NOT
    instantiate or schedule them immediately. Scheduling is now handled by
    loading configuration from the database.
    """
    orchestrator = get_orchestrator()

    logger.info("Setting up Phase 2.5 comprehensive data collectors...")
    
    # Discover and register all available strategies
    from app.core.collectors.registry import CollectorRegistry
    CollectorRegistry.discover_strategies()
    
    logger.info(f"Discovered {len(CollectorRegistry.list_strategies())} collector strategies.")
    
    # The actual scheduling of jobs is now handled by:
    # orchestrator.load_jobs_from_db()
    # which is called during start_collection()
    
    logger.info("Collectors setup complete (waiting for DB configuration)")

def start_collection() -> None:
    """
    Start the collection orchestrator and load jobs from DB.
    """
    orchestrator = get_orchestrator()
    try:
        # Initial load of jobs from database
        orchestrator.load_jobs_from_db()
        
        # Start the scheduler
        orchestrator.start()
        logger.info("Collection orchestrator started")
    except Exception as e:
        logger.error(f"Failed to start collection orchestrator: {str(e)}")

def stop_collection() -> None:
    """
    Stop the collection orchestrator.
    """
    orchestrator = get_orchestrator()
    try:
        orchestrator.stop()
        logger.info("Collection orchestrator stopped")
    except Exception as e:
        logger.error(f"Failed to stop collection orchestrator: {str(e)}")



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
