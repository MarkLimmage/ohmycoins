# Current Sprint: 2.39

**Status**: IN PROGRESS
**Objective**: CryptoSlate Keyword Enrichment (Pilot)
**Previous Sprint**: 2.38 (Collector Observability — Sample Records & RSS Fix - COMPLETED)

## Context

Sprint 2.38 shipped sample records viewer and fixed 6 RSS collectors to persist `NewsItem` records. This sprint pilots structured keyword/sentiment enrichment on the CryptoSlate collector. A `NewsKeywordMatch` table captures market-moving keyword signals across 4 categories (Macro, Liquidity, Regulatory, Fundamental) with directional signals, impact levels, and temporal hints. Additionally, `StrategyAdapterCollector.store_data()` duplicate handling was hardened with per-item savepoints.

## Tasks

1. [x] **Part A — NewsKeywordMatch Model**
   - Added `NewsKeywordMatch` SQLModel table (FK to `news_item.link`, ARRAY currencies, unique constraint)

2. [x] **Part B — Keyword Taxonomy Module**
   - Created `keyword_taxonomy.py` with 30 precompiled keyword patterns across 4 categories
   - Shared `CRYPTO_PATTERNS` for currency extraction
   - Functions: `match_keywords()`, `extract_currencies()`, `extract_context()`

3. [x] **Part C — CryptoSlate Collector Enrichment**
   - Inline keyword matching in `collect()` — creates `NewsKeywordMatch` records alongside `NewsItem`
   - Weighted sentiment aggregation populates `sentiment_score` and `sentiment_label`

4. [x] **Part D — Duplicate Handling Fix**
   - `StrategyAdapterCollector.store_data()` now uses per-item savepoints
   - Duplicate `IntegrityError` rolls back only the offending item, not the entire batch

5. [x] **Part E — Alembic Migration**
   - Migration `d0ff5656d6f6` creates `news_keyword_match` table

6. [x] **Part F — Sample Records Mapping**
   - Updated `news_cryptoslate` to show enrichment columns (sentiment_label, sentiment_score)
   - Added `news_cryptoslate_keywords` mapping for keyword match viewing

## Verification

- 872 tests passing (25 new), mypy + ruff clean
