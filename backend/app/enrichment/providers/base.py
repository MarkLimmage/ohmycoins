"""Base class for sentiment analysis providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Sentiment analysis result for a specific coin."""

    coin: str
    direction: str  # "bullish" | "bearish" | "neutral"
    confidence: float
    rationale: str


class ISentimentProvider(ABC):
    """Interface for LLM-based sentiment analysis providers."""

    @abstractmethod
    async def analyse(self, title: str, summary: str) -> list[SentimentResult]:
        """Analyze sentiment from title and summary, return per-coin results."""
