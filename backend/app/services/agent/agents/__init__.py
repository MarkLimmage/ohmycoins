"""
Agent module initialization.

Week 1-2: Base agent and DataRetrievalAgent (placeholder)
Week 3-4: Enhanced DataRetrievalAgent and new DataAnalystAgent
"""

from .base import BaseAgent
from .data_retrieval import DataRetrievalAgent
from .data_analyst import DataAnalystAgent

__all__ = ["BaseAgent", "DataRetrievalAgent", "DataAnalystAgent"]
