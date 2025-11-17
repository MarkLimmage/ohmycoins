"""
Tools module for agent capabilities.

This module contains all the tools that agents can use to perform their tasks.
Week 3-4 implementation: Data Retrieval and Data Analysis tools.
"""

from .data_retrieval_tools import (
    fetch_price_data,
    fetch_sentiment_data,
    fetch_on_chain_metrics,
    fetch_catalyst_events,
    get_available_coins,
    get_data_statistics,
)
from .data_analysis_tools import (
    calculate_technical_indicators,
    analyze_sentiment_trends,
    analyze_on_chain_signals,
    detect_catalyst_impact,
    clean_data,
    perform_eda,
)

__all__ = [
    # Data Retrieval Tools
    "fetch_price_data",
    "fetch_sentiment_data",
    "fetch_on_chain_metrics",
    "fetch_catalyst_events",
    "get_available_coins",
    "get_data_statistics",
    # Data Analysis Tools
    "calculate_technical_indicators",
    "analyze_sentiment_trends",
    "analyze_on_chain_signals",
    "detect_catalyst_impact",
    "clean_data",
    "perform_eda",
]
