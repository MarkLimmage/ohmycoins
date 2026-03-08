"""Tests for EntityEnricher regex-based POLE extraction."""

from __future__ import annotations

import pytest

from app.enrichment.entity_enricher import EntityEnricher
from app.models import NewsItem


@pytest.fixture
def entity_enricher() -> EntityEnricher:
    """Create an EntityEnricher instance."""
    return EntityEnricher()


def test_enricher_name(entity_enricher: EntityEnricher) -> None:
    """Test enricher name."""
    assert entity_enricher.name == "entity_extraction"


def test_can_enrich_with_valid_item(entity_enricher: EntityEnricher) -> None:
    """Test can_enrich returns True for NewsItem with title."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="SEC Investigates Bitcoin Exchange",
        source="TestSource",
    )
    assert entity_enricher.can_enrich(item) is True


def test_can_enrich_with_no_title(entity_enricher: EntityEnricher) -> None:
    """Test can_enrich returns False for item without title."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="",
        source="TestSource",
    )
    assert entity_enricher.can_enrich(item) is False


def test_can_enrich_non_newsitem(entity_enricher: EntityEnricher) -> None:
    """Test can_enrich returns False for non-NewsItem."""
    assert entity_enricher.can_enrich("not a news item") is False


@pytest.mark.asyncio
async def test_extract_organizations(entity_enricher: EntityEnricher) -> None:
    """Test extraction of known organizations."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="SEC and CFTC discuss crypto regulation",
        summary="Federal agencies meet with Coinbase and Binance executives",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]
    entities = result.data["entities"]

    assert "SEC" in entities["organizations"]
    assert "CFTC" in entities["organizations"]
    assert "Coinbase" in entities["organizations"]
    assert "Binance" in entities["organizations"]


@pytest.mark.asyncio
async def test_extract_people(entity_enricher: EntityEnricher) -> None:
    """Test extraction of known people."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="Vitalik Buterin and Elon Musk discuss crypto",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]
    entities = result.data["entities"]

    assert "Vitalik Buterin" in entities["people"]
    assert "Elon Musk" in entities["people"]


@pytest.mark.asyncio
async def test_extract_events(entity_enricher: EntityEnricher) -> None:
    """Test extraction of known events."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="Bitcoin halving and Ethereum fork scheduled",
        summary="Major network upgrades on the horizon",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]
    entities = result.data["entities"]

    assert "halving" in entities["events"]
    assert "fork" in entities["events"]
    assert "upgrade" in entities["events"]


@pytest.mark.asyncio
async def test_extract_locations(entity_enricher: EntityEnricher) -> None:
    """Test extraction of known locations."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="New crypto exchange opens in Singapore and Hong Kong",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]
    entities = result.data["entities"]

    assert "Singapore" in entities["locations"]
    assert "Hong Kong" in entities["locations"]


@pytest.mark.asyncio
async def test_enrichment_type_and_confidence(entity_enricher: EntityEnricher) -> None:
    """Test enrichment type and confidence."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="SEC investigates Coinbase",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) == 1
    result = results[0]

    assert result.enricher_name == "entity_extraction"
    assert result.enrichment_type == "entity"
    assert result.confidence == 0.7


@pytest.mark.asyncio
async def test_no_entities_found(entity_enricher: EntityEnricher) -> None:
    """Test when no entities are found."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="Generic market update",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_case_insensitive_matching(entity_enricher: EntityEnricher) -> None:
    """Test that entity matching is case-insensitive."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="The SEC announced new rules. COINBASE RESPONDS.",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]
    entities = result.data["entities"]

    assert "SEC" in entities["organizations"]
    assert "Coinbase" in entities["organizations"]


@pytest.mark.asyncio
async def test_inferred_relationships(entity_enricher: EntityEnricher) -> None:
    """Test relationship inference between entities."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="SEC investigates Coinbase and Vitalik Buterin",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]
    relationships = result.data["relationships"]

    # Should have relationships between organizations and people
    assert len(relationships) > 0
    assert any(r["type"] == "potential_association" for r in relationships)


@pytest.mark.asyncio
async def test_empty_currencies_in_entity_enrichment(
    entity_enricher: EntityEnricher,
) -> None:
    """Test that entity enrichment returns empty currencies list."""
    item = NewsItem(
        link="https://example.com/news/1",
        title="SEC discusses crypto regulation",
        source="TestSource",
    )
    results = await entity_enricher.enrich(item)

    assert len(results) > 0
    result = results[0]

    assert result.currencies == []
