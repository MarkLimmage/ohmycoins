"""Tests for keyword taxonomy module."""

from app.collectors.strategies.keyword_taxonomy import (
    KEYWORD_TAXONOMY,
    KeywordEntry,
    extract_context,
    extract_currencies,
    match_keywords,
)


def test_match_keywords_finds_tariff() -> None:
    matches = match_keywords("New tariffs announced by government")
    keywords = [m.keyword for m in matches]
    assert "tariff" in keywords


def test_match_keywords_finds_multiple() -> None:
    text = "Fed announces rate cut amid recession fears"
    matches = match_keywords(text)
    keywords = [m.keyword for m in matches]
    assert "Federal Reserve" in keywords
    assert "rate cut" in keywords
    assert "recession" in keywords


def test_match_keywords_empty_for_irrelevant() -> None:
    matches = match_keywords("The weather is nice today")
    assert matches == []


def test_match_keywords_case_insensitive() -> None:
    matches = match_keywords("TARIFFS are increasing")
    keywords = [m.keyword for m in matches]
    assert "tariff" in keywords


def test_extract_currencies_finds_btc_eth() -> None:
    currencies = extract_currencies("Bitcoin and Ethereum prices surge, BTC hits new high")
    assert "BTC" in currencies
    assert "ETH" in currencies


def test_extract_currencies_deduplicates() -> None:
    currencies = extract_currencies("BTC Bitcoin BTC")
    assert currencies.count("BTC") == 1


def test_extract_currencies_empty() -> None:
    currencies = extract_currencies("No crypto mentioned here")
    assert currencies == []


def test_extract_context_returns_window() -> None:
    text = "The government announced new tariffs on imports today"
    ctx = extract_context(text, "tariff", window=40)
    assert "tariff" in ctx.lower()
    assert len(ctx) <= 50  # approximate window


def test_extract_context_no_match_returns_start() -> None:
    text = "Some random text without matches"
    ctx = extract_context(text, "nonexistent", window=20)
    assert ctx == text[:20]


def test_keyword_entry_is_frozen() -> None:
    entry = KEYWORD_TAXONOMY[0]
    assert isinstance(entry, KeywordEntry)
    try:
        entry.keyword = "modified"  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_all_taxonomy_entries_valid() -> None:
    valid_categories = {"macro", "liquidity", "regulatory", "fundamental"}
    valid_directions = {"bullish", "bearish", "neutral"}
    valid_impacts = {"high", "medium", "low"}
    valid_temporal = {"immediate", "short_term", "long_term"}

    for entry in KEYWORD_TAXONOMY:
        assert entry.category in valid_categories, f"{entry.keyword}: bad category"
        assert entry.direction in valid_directions, f"{entry.keyword}: bad direction"
        assert entry.impact in valid_impacts, f"{entry.keyword}: bad impact"
        assert entry.temporal_signal in valid_temporal, f"{entry.keyword}: bad temporal"
        assert entry.pattern is not None, f"{entry.keyword}: no pattern"


def test_match_keywords_regulatory_category() -> None:
    matches = match_keywords("SEC approves Bitcoin ETF application")
    keywords = [m.keyword for m in matches]
    assert "SEC" in keywords
    assert "ETF" in keywords
    assert "approval" in keywords


def test_match_keywords_fundamental_category() -> None:
    matches = match_keywords("Major exchange hacked, exploit drains funds")
    keywords = [m.keyword for m in matches]
    assert "hack" in keywords
    assert "exploit" in keywords
