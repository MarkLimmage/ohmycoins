"""Tests for StrategyAdapterCollector duplicate handling with savepoints."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.exc import IntegrityError

from app.services.collectors.strategy_adapter import StrategyAdapterCollector
from app.models import NewsItem


def _make_strategy() -> MagicMock:
    strategy = MagicMock()
    strategy.name = "test_strategy"
    return strategy


def _make_news_item(link: str = "https://example.com/1") -> NewsItem:
    return NewsItem(
        title="Test Article",
        link=link,
        source="TestSource",
    )


@pytest.mark.asyncio
async def test_store_data_skips_duplicates() -> None:
    adapter = StrategyAdapterCollector(
        strategy=_make_strategy(), ledger_name="test"
    )

    session = MagicMock()
    nested = MagicMock()
    session.begin_nested = MagicMock(return_value=nested)

    # First item succeeds, second raises IntegrityError
    call_count = 0
    def flush_side_effect() -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise IntegrityError("duplicate", {}, None)

    session.flush = MagicMock(side_effect=flush_side_effect)

    item1 = _make_news_item("https://example.com/1")
    item2 = _make_news_item("https://example.com/1")  # duplicate

    count = await adapter.store_data([item1, item2], session)
    assert count == 1
    assert nested.rollback.call_count == 1


@pytest.mark.asyncio
async def test_store_data_mixed_valid_and_duplicate() -> None:
    adapter = StrategyAdapterCollector(
        strategy=_make_strategy(), ledger_name="test"
    )

    session = MagicMock()
    nested = MagicMock()
    session.begin_nested = MagicMock(return_value=nested)

    call_count = 0
    def flush_side_effect() -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise IntegrityError("duplicate", {}, None)

    session.flush = MagicMock(side_effect=flush_side_effect)

    items = [
        _make_news_item("https://example.com/1"),
        _make_news_item("https://example.com/dup"),
        _make_news_item("https://example.com/3"),
    ]

    count = await adapter.store_data(items, session)
    assert count == 2  # first and third succeed


@pytest.mark.asyncio
async def test_store_data_skips_non_model_items() -> None:
    adapter = StrategyAdapterCollector(
        strategy=_make_strategy(), ledger_name="test"
    )

    session = MagicMock()
    nested = MagicMock()
    session.begin_nested = MagicMock(return_value=nested)
    session.flush = MagicMock()

    items = [
        {"title": "dict item", "link": "http://example.com"},  # no 'id' attr
        _make_news_item("https://example.com/valid"),
    ]

    count = await adapter.store_data(items, session)  # type: ignore[arg-type]
    assert count == 1  # only the NewsItem


@pytest.mark.asyncio
async def test_store_data_empty_list() -> None:
    adapter = StrategyAdapterCollector(
        strategy=_make_strategy(), ledger_name="test"
    )
    session = MagicMock()
    count = await adapter.store_data([], session)
    assert count == 0


@pytest.mark.asyncio
async def test_store_data_handles_generic_exception() -> None:
    adapter = StrategyAdapterCollector(
        strategy=_make_strategy(), ledger_name="test"
    )

    session = MagicMock()
    nested = MagicMock()
    session.begin_nested = MagicMock(return_value=nested)
    session.flush = MagicMock(side_effect=RuntimeError("unexpected"))

    item = _make_news_item("https://example.com/1")
    count = await adapter.store_data([item], session)
    assert count == 0
    assert nested.rollback.call_count == 1
