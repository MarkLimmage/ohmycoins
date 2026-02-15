"""
Collector Factory module.
Creates collector instances from DB configuration or registry.
"""
from typing import Any
import importlib
import logging
from app.services.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

class CollectorFactory:
    """Factory to create collector instances based on type string."""
    
    @staticmethod
    def create_collector(type_name: str, config: dict[str, Any]) -> BaseCollector:
        """
        Create a collector instance.
        
        Args:
           type_name: The string identifier for the collector type (e.g., 'DeFiLlamaCollector')
           config: Configuration dictionary for the collector
        
        Returns:
           BaseCollector instance
        """
        # Mapping of supported collectors
        # Note: In a real implementation this could be dynamic or plugin-based
        from app.services.collectors.glass import DeFiLlamaCollector, NansenCollector
        from app.services.collectors.human import CryptoPanicCollector, NewscatcherCollector, RedditCollector
        from app.services.collectors.catalyst import SECAPICollector, CoinSpotAnnouncementsCollector
        from app.services.collectors.scraper import WebScraperCollector

        collectors_map = {
            "DeFiLlamaCollector": DeFiLlamaCollector,
            "NansenCollector": NansenCollector,
            "CryptoPanicCollector": CryptoPanicCollector,
            "NewscatcherCollector": NewscatcherCollector,
            "RedditCollector": RedditCollector,
            "SECAPICollector": SECAPICollector,
            "CoinSpotAnnouncementsCollector": CoinSpotAnnouncementsCollector,
            "WebScraperCollector": WebScraperCollector
        }

        if type_name in collectors_map:
            collector_class = collectors_map[type_name]
            
            # Special handling for WebScraperCollector to pass config
            if type_name == "WebScraperCollector":
                # Ensure name is passed if present in config, or generate one
                name = config.get("name", f"scraper_{len(config)}")
                return collector_class(name=name, config=config)
            
            # For others, we currently support parameterless init (except name/ledger which are hardcoded in subclass __init__)
            # or we might need to update them later.
            return collector_class()
        
        raise ValueError(f"Unknown collector type: {type_name}")
        if type_name == "WebScraperCollector":
             # TODO: Implement generic scraper
             pass

        raise ValueError(f"Unknown collector type: {type_name}")
