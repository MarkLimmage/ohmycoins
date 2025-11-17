"""
Tools module for agent capabilities.

This module contains all the tools that agents can use to perform their tasks.
Week 3-4 implementation: Data Retrieval and Data Analysis tools.
Week 5-6 implementation: Model Training and Model Evaluation tools.
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
from .model_training_tools import (
    train_classification_model,
    train_regression_model,
    cross_validate_model,
)
from .model_evaluation_tools import (
    evaluate_model,
    tune_hyperparameters,
    compare_models,
    calculate_feature_importance,
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
    # Model Training Tools
    "train_classification_model",
    "train_regression_model",
    "cross_validate_model",
    # Model Evaluation Tools
    "evaluate_model",
    "tune_hyperparameters",
    "compare_models",
    "calculate_feature_importance",
]
