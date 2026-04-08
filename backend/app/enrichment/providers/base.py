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


@dataclass
class TextInput:
    """Input for batch text analysis."""

    text: str
    source_id: int
    metadata: dict


@dataclass
class CoinSentiment:
    """Per-coin sentiment result from batch analysis."""

    coin: str
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    rationale: str
    source_id: int


class ISentimentProvider(ABC):
    """Interface for LLM-based sentiment analysis providers."""

    @abstractmethod
    async def analyse(self, title: str, summary: str) -> list[SentimentResult]:
        """Analyze sentiment from title and summary, return per-coin results."""

    async def analyse_batch(self, inputs: list[TextInput]) -> list[CoinSentiment]:
        """Batch analysis. Default: iterate single calls."""
        results: list[CoinSentiment] = []
        for inp in inputs:
            single_results = await self.analyse(inp.text, "")
            for sr in single_results:
                direction_to_score = {"bullish": 0.5, "bearish": -0.5, "neutral": 0.0}
                results.append(
                    CoinSentiment(
                        coin=sr.coin,
                        score=direction_to_score.get(sr.direction, 0.0),
                        confidence=sr.confidence,
                        rationale=sr.rationale,
                        source_id=inp.source_id,
                    )
                )
        return results
