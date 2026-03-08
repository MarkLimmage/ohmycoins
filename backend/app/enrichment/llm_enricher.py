"""LLM-based sentiment enricher for news items."""

from __future__ import annotations

import logging

from app.enrichment.base import EnrichmentResult, IEnricher
from app.enrichment.providers.base import ISentimentProvider
from app.models import NewsItem

logger = logging.getLogger(__name__)


class LLMEnricher(IEnricher):
    """Uses an LLM sentiment provider to analyze news sentiment per-coin."""

    def __init__(self, provider: ISentimentProvider):
        """Initialize with a sentiment provider."""
        self.provider = provider

    @property
    def name(self) -> str:
        """Unique identifier for this enricher."""
        return "llm_sentiment"

    def can_enrich(self, item: object) -> bool:
        """Check if item can be enriched (must be NewsItem with title)."""
        return isinstance(item, NewsItem) and bool(item.title)

    async def enrich(self, item: object) -> list[EnrichmentResult]:
        """
        Analyze sentiment for a news item using LLM provider.

        Returns one EnrichmentResult per analyzed coin.
        """
        if not isinstance(item, NewsItem):
            return []

        try:
            # Call provider to get sentiment analysis
            sentiment_results = await self.provider.analyse(
                title=item.title, summary=item.summary or ""
            )

            # Convert to EnrichmentResults
            results: list[EnrichmentResult] = []
            for sent in sentiment_results:
                result = EnrichmentResult(
                    enricher_name="llm_sentiment",
                    enrichment_type="sentiment",
                    data={
                        "coin": sent.coin,
                        "direction": sent.direction,
                        "rationale": sent.rationale,
                    },
                    currencies=[sent.coin],
                    confidence=sent.confidence,
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"LLM enrichment failed for {item.link}: {e}")
            return []
