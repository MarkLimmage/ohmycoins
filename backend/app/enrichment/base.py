"""Base classes and interfaces for the enrichment pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnrichmentResult:
    """Result of enriching a single item through a specific enricher."""

    enricher_name: str
    enrichment_type: str  # "keyword", "sentiment", "entity"
    data: dict[str, Any]
    currencies: list[str] = field(default_factory=list)
    confidence: float = 0.0


class IEnricher(ABC):
    """Base interface for all enrichers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this enricher."""

    @abstractmethod
    def can_enrich(self, item: Any) -> bool:
        """Check if this enricher can process the given item."""

    @abstractmethod
    async def enrich(self, item: Any) -> list[EnrichmentResult]:
        """Enrich an item and return results."""
