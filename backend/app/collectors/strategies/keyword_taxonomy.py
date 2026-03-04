"""Keyword taxonomy for news enrichment — precompiled patterns for market-moving signals."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordEntry:
    """A single keyword with metadata for market signal classification."""

    keyword: str
    pattern: re.Pattern[str]
    category: str
    direction: str
    impact: str
    temporal_signal: str


def _kw(
    keyword: str,
    pattern: str,
    category: str,
    direction: str,
    impact: str,
    temporal_signal: str,
) -> KeywordEntry:
    return KeywordEntry(
        keyword=keyword,
        pattern=re.compile(pattern, re.IGNORECASE),
        category=category,
        direction=direction,
        impact=impact,
        temporal_signal=temporal_signal,
    )


# ── Taxonomy ──────────────────────────────────────────────────────────
KEYWORD_TAXONOMY: list[KeywordEntry] = [
    # Macro & Geopolitical
    _kw("tariff", r"\btariffs?\b", "macro", "bearish", "high", "immediate"),
    _kw("sanction", r"\bsanctions?\b", "macro", "bearish", "high", "short_term"),
    _kw("trade war", r"\btrade\s+war\b", "macro", "bearish", "high", "long_term"),
    _kw(
        "geopolitical", r"\bgeopolitical\b", "macro", "neutral", "medium", "short_term"
    ),
    _kw("recession", r"\brecession\b", "macro", "bearish", "high", "long_term"),
    _kw("inflation", r"\binflation\b", "macro", "bearish", "medium", "long_term"),
    _kw("GDP", r"\bGDP\b", "macro", "neutral", "medium", "short_term"),
    # Liquidity & Monetary Policy
    _kw("rate cut", r"\brate\s+cut\b", "liquidity", "bullish", "high", "immediate"),
    _kw("rate hike", r"\brate\s+hike\b", "liquidity", "bearish", "high", "immediate"),
    _kw(
        "quantitative easing",
        r"\b(?:quantitative\s+easing|QE)\b",
        "liquidity",
        "bullish",
        "high",
        "long_term",
    ),
    _kw(
        "quantitative tightening",
        r"\b(?:quantitative\s+tightening|QT)\b",
        "liquidity",
        "bearish",
        "high",
        "long_term",
    ),
    _kw(
        "Federal Reserve",
        r"\b(?:Fed(?:eral\s+Reserve)?)\b",
        "liquidity",
        "neutral",
        "high",
        "immediate",
    ),
    _kw("liquidity", r"\bliquidity\b", "liquidity", "neutral", "medium", "short_term"),
    _kw("yield", r"\byields?\b", "liquidity", "neutral", "medium", "short_term"),
    # Regulatory & Legal
    _kw("SEC", r"\bSEC\b", "regulatory", "neutral", "high", "short_term"),
    _kw(
        "regulation",
        r"\bregulations?\b",
        "regulatory",
        "neutral",
        "medium",
        "long_term",
    ),
    _kw("ban", r"\bbann?(?:ed|s)?\b", "regulatory", "bearish", "high", "immediate"),
    _kw(
        "approval",
        r"\bapprov(?:al|e[ds]|ing)\b",
        "regulatory",
        "bullish",
        "high",
        "immediate",
    ),
    _kw("ETF", r"\bETF\b", "regulatory", "bullish", "high", "short_term"),
    _kw(
        "lawsuit",
        r"\b(?:lawsuit|legal\s+action)\b",
        "regulatory",
        "bearish",
        "medium",
        "long_term",
    ),
    _kw("compliance", r"\bcompliance\b", "regulatory", "neutral", "low", "long_term"),
    # Fundamental & Ecosystem
    _kw("halving", r"\bhalving\b", "fundamental", "bullish", "high", "long_term"),
    _kw("upgrade", r"\bupgrade\b", "fundamental", "bullish", "medium", "short_term"),
    _kw("hack", r"\bhacks?(?:ed)?\b", "fundamental", "bearish", "high", "immediate"),
    _kw("exploit", r"\bexploit\b", "fundamental", "bearish", "high", "immediate"),
    _kw(
        "partnership",
        r"\bpartnership\b",
        "fundamental",
        "bullish",
        "medium",
        "short_term",
    ),
    _kw("adoption", r"\badoption\b", "fundamental", "bullish", "medium", "long_term"),
    _kw("whale", r"\bwhales?\b", "fundamental", "neutral", "medium", "immediate"),
    _kw("burn", r"\bburn(?:ed|ing)?\b", "fundamental", "bullish", "low", "short_term"),
    _kw("airdrop", r"\bairdrop\b", "fundamental", "bullish", "low", "immediate"),
    _kw("fork", r"\bfork\b", "fundamental", "neutral", "medium", "short_term"),
]

# ── Crypto currency patterns (shared with human_reddit) ──────────────
CRYPTO_PATTERNS: list[tuple[str, str]] = [
    (r"\bBTC\b", "BTC"),
    (r"\bBitcoin\b", "BTC"),
    (r"\bETH\b", "ETH"),
    (r"\bEthereum\b", "ETH"),
    (r"\bADA\b", "ADA"),
    (r"\bCardano\b", "ADA"),
    (r"\bDOGE\b", "DOGE"),
    (r"\bXRP\b", "XRP"),
    (r"\bRipple\b", "XRP"),
    (r"\bSOL\b", "SOL"),
    (r"\bSolana\b", "SOL"),
    (r"\bAVAX\b", "AVAX"),
    (r"\bAvalanche\b", "AVAX"),
    (r"\bPOLYGON\b", "POLYGON"),
    (r"\bARB\b", "ARB"),
    (r"\bArbitrum\b", "ARB"),
    (r"\bOP\b", "OP"),
    (r"\bOptimism\b", "OP"),
    (r"\bLINK\b", "LINK"),
    (r"\bChainlink\b", "LINK"),
    (r"\bUNI\b", "UNI"),
    (r"\bUniswap\b", "UNI"),
    (r"\bAAVE\b", "AAVE"),
    (r"\bCRV\b", "CRV"),
    (r"\bCurve\b", "CRV"),
]

_COMPILED_CRYPTO: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p, re.IGNORECASE), sym) for p, sym in CRYPTO_PATTERNS
]


def match_keywords(text: str) -> list[KeywordEntry]:
    """Return all keyword entries that match in the given text."""
    return [entry for entry in KEYWORD_TAXONOMY if entry.pattern.search(text)]


def extract_currencies(text: str) -> list[str]:
    """Extract unique crypto ticker symbols from text."""
    found: list[str] = []
    for pat, symbol in _COMPILED_CRYPTO:
        if pat.search(text):
            if symbol not in found:
                found.append(symbol)
    return found


def extract_context(text: str, keyword: str, window: int = 100) -> str:
    """Return up to `window` chars around the first occurrence of keyword in text."""
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match:
        return text[:window]
    start = max(0, match.start() - window // 2)
    end = min(len(text), match.end() + window // 2)
    return text[start:end]


# ── Sentiment Aggregation ──────────────────────────────────────────────────

DIRECTION_WEIGHTS = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}
IMPACT_MULTIPLIER = {"high": 3.0, "medium": 2.0, "low": 1.0}


def aggregate_sentiment(matches: list[KeywordEntry]) -> tuple[float, str]:
    """Compute weighted sentiment score from keyword matches."""
    total_weight = sum(IMPACT_MULTIPLIER[m.impact] for m in matches)
    if total_weight == 0:
        return 0.0, "neutral"
    weighted_sum = sum(
        DIRECTION_WEIGHTS[m.direction] * IMPACT_MULTIPLIER[m.impact] for m in matches
    )
    score = round(weighted_sum / total_weight, 4)
    label = "bullish" if score > 0.1 else "bearish" if score < -0.1 else "neutral"
    return score, label
