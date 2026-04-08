"""Social sentiment enricher using LLM batch analysis."""

from __future__ import annotations

import logging
from typing import Any

from sqlmodel import Session

from app.enrichment.base import EnrichmentResult, IEnricher
from app.enrichment.providers.base import CoinSentiment, ISentimentProvider, TextInput
from app.models import SentimentScore, SocialSentiment

logger = logging.getLogger(__name__)

# Top ~50 crypto symbols allow-list for validation
ALLOWED_COINS: set[str] = {
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
    "MATIC", "SHIB", "TRX", "UNI", "ATOM", "LTC", "ETC", "XLM", "BCH", "FIL",
    "NEAR", "APT", "ARB", "OP", "ICP", "VET", "ALGO", "GRT", "FTM", "SAND",
    "MANA", "AXS", "AAVE", "MKR", "SNX", "CRV", "LDO", "RUNE", "INJ", "SUI",
    "SEI", "TIA", "STX", "IMX", "PEPE", "WIF", "BONK", "RENDER", "FET", "TAO",
}


class SocialSentimentEnricher(IEnricher):
    """Enriches SocialSentiment posts using LLM batch analysis."""

    def __init__(self, provider: ISentimentProvider, session: Session):
        self.provider = provider
        self.session = session

    @property
    def name(self) -> str:
        return "social_llm_sentiment"

    def can_enrich(self, item: Any) -> bool:
        return isinstance(item, SocialSentiment) and bool(item.content)

    async def enrich(self, item: Any) -> list[EnrichmentResult]:
        if not isinstance(item, SocialSentiment):
            return []

        # Build conversation text with graceful degradation
        text_parts: list[str] = []
        if item.content:
            text_parts.append(item.content)

        body = getattr(item, "body", None)
        if body:
            text_parts.append(body)

        top_comments = getattr(item, "top_comments", None)
        if top_comments and isinstance(top_comments, list):
            for comment in top_comments[:10]:
                if isinstance(comment, dict) and comment.get("text"):
                    text_parts.append(comment["text"])

        conversation_text = "\n\n".join(text_parts)

        # Build metadata
        metadata: dict[str, Any] = {
            "platform": item.platform,
            "score": item.score,
            "comment_count": getattr(item, "comment_count", None),
        }

        text_input = TextInput(
            text=conversation_text,
            source_id=item.id,  # type: ignore[arg-type]
            metadata=metadata,
        )

        # Call batch analysis (single item)
        try:
            coin_sentiments = await self.provider.analyse_batch([text_input])
        except Exception as e:
            logger.error(f"LLM analysis failed for social_sentiment id={item.id}: {e}")
            return []

        # Filter to allowed coins and build results
        results: list[EnrichmentResult] = []
        for cs in coin_sentiments:
            coin = cs.coin.upper()
            if coin not in ALLOWED_COINS:
                logger.debug(f"Filtered out non-allowed coin: {coin}")
                continue

            # Write to SentimentScore table
            self._write_sentiment_score(item, cs)

            results.append(
                EnrichmentResult(
                    enricher_name=self.name,
                    enrichment_type="sentiment",
                    data={
                        "coin": coin,
                        "score": cs.score,
                        "rationale": cs.rationale,
                        "source_id": cs.source_id,
                    },
                    currencies=[coin],
                    confidence=cs.confidence,
                )
            )

        return results

    def _write_sentiment_score(
        self, item: SocialSentiment, cs: CoinSentiment
    ) -> None:
        """Write a per-coin row to the SentimentScore table."""
        try:
            score = SentimentScore(
                asset=cs.coin.upper(),
                source="reddit_llm",
                score=max(-1.0, min(1.0, cs.score)),
                magnitude=max(0.0, min(1.0, cs.confidence)),
                raw_data={
                    "rationale": cs.rationale,
                    "source_id": cs.source_id,
                    "platform": item.platform,
                },
                timestamp=item.posted_at,
            )
            self.session.add(score)
        except Exception as e:
            logger.warning(f"Failed to write SentimentScore for {cs.coin}: {e}")
