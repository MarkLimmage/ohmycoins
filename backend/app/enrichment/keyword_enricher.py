"""Keyword-based enricher for news items."""

from __future__ import annotations

from app.collectors.strategies.keyword_taxonomy import (
    extract_context,
    extract_currencies,
    match_keywords,
)
from app.enrichment.base import EnrichmentResult, IEnricher
from app.models import NewsItem


class KeywordEnricher(IEnricher):
    """Extracts keywords and sentiment from news items using taxonomy."""

    @property
    def name(self) -> str:
        """Unique identifier for this enricher."""
        return "keyword"

    def can_enrich(self, item: object) -> bool:
        """Check if item can be enriched (must be NewsItem with title/summary)."""
        return isinstance(item, NewsItem) and bool(
            item.title and (item.summary or "")
        )

    async def enrich(self, item: object) -> list[EnrichmentResult]:
        """
        Extract keywords and sentiment from a news item.

        Returns one EnrichmentResult per matched keyword.
        """
        results: list[EnrichmentResult] = []

        if not isinstance(item, NewsItem):
            return results

        # Build search text from title and summary
        search_text = f"{item.title} {item.summary or ''}"

        # Match keywords
        matches = match_keywords(search_text)
        if not matches:
            return results

        # Extract currencies mentioned in the text
        currencies = extract_currencies(search_text)

        # Create a result for each matched keyword
        for kw in matches:
            result = EnrichmentResult(
                enricher_name="keyword",
                enrichment_type="keyword",
                data={
                    "keyword": kw.keyword,
                    "category": kw.category,
                    "direction": kw.direction,
                    "impact": kw.impact,
                    "temporal_signal": kw.temporal_signal,
                    "match_context": extract_context(search_text, kw.keyword),
                },
                currencies=currencies,
                confidence=1.0,
            )
            results.append(result)

        return results
