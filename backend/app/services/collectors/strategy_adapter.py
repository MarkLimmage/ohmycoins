import logging
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.core.collectors.base import ICollector
from app.enrichment.keyword_enricher import KeywordEnricher
from app.enrichment.llm_enricher import LLMEnricher
from app.enrichment.pipeline import EnrichmentPipeline
from app.enrichment.providers.gemini import GeminiSentimentProvider
from app.models import NewsItem
from app.services.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class StrategyAdapterCollector(BaseCollector):
    """
    Adapter to run ICollector strategies within the BaseCollector orchestration framework.
    """

    def __init__(
        self,
        strategy: ICollector,
        ledger_name: str,
        default_config: dict[str, Any] | None = None,
    ):
        super().__init__(name=strategy.name, ledger=ledger_name)
        self.strategy = strategy
        self.default_config = default_config or {}

    async def collect(self) -> list[Any]:
        logger.info(f"Running strategy: {self.strategy.name}")
        # In a real impl, config would come from DB dynamically
        # For now, use default_config passed during initialization
        return await self.strategy.collect(self.default_config)

    async def validate_data(self, data: list[Any]) -> list[Any]:
        # Basic validation
        if not isinstance(data, list):
            logger.warning(
                f"Strategy {self.strategy.name} returned non-list data: {type(data)}"
            )
            return []
        return data

    async def store_data(self, data: list[Any], session: Session) -> int:
        if not data:
            return 0

        count = 0
        stored_items: list[NewsItem] = []

        for item in data:
            if not hasattr(item, "id"):
                logger.warning(
                    f"Item {item} is not a valid model instance, skipping storage."
                )
                continue

            try:
                with session.begin_nested():
                    session.add(item)
                    session.flush()
                count += 1
                # Track NewsItem objects for enrichment
                if isinstance(item, NewsItem):
                    stored_items.append(item)
            except IntegrityError:
                logger.debug(
                    f"Duplicate item skipped for {self.strategy.name}: "
                    f"{getattr(item, 'link', '?')}"
                )
            except Exception as e:
                logger.error(f"Failed to store item for {self.strategy.name}: {e}")

        # Auto-trigger enrichment for newly stored news items
        if stored_items:
            await self._enrich_items(stored_items, session)

        return count

    async def _enrich_items(self, items: list[NewsItem], session: Session) -> None:
        """Run enrichment pipeline on newly stored news items."""
        try:
            # Build enricher list
            enrichers: list[Any] = [KeywordEnricher()]

            # Attempt to add LLM enricher if credentials available
            try:
                provider = GeminiSentimentProvider(session)
                enrichers.append(LLMEnricher(provider))
            except ValueError:
                logger.debug("Skipping LLM enricher: no active Google credentials")

            # Run pipeline
            pipeline = EnrichmentPipeline(enrichers)
            run = await pipeline.run(items, session, trigger="auto")
            logger.info(
                f"Enrichment completed: {run.items_enriched} enriched, "
                f"{run.items_skipped} skipped, {run.items_failed} failed"
            )

        except Exception as e:
            # Enrichment failure must not crash the collector
            logger.error(f"Enrichment pipeline failed: {e}")
