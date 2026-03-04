# Current Sprint: 2.40

**Status**: COMPLETED
**Objective**: Keyword Enrichment Rollout + Platform Polish
**Previous Sprint**: 2.39 (CryptoSlate Keyword Enrichment Pilot - COMPLETED)

## Context

Sprint 2.39 piloted keyword enrichment on CryptoSlate — a `NewsKeywordMatch` table captures market-moving keyword signals across 4 categories with directional signals, impact levels, and temporal hints. This sprint rolls out that enrichment to all remaining RSS news collectors and fills Data Explorer backend gaps.

## Tasks

1. [x] **Part A — Keyword Enrichment Rollout**
   - Extracted shared enrichment logic (`aggregate_sentiment`, `DIRECTION_WEIGHTS`, `IMPACT_MULTIPLIER`) from CryptoSlate to `keyword_taxonomy.py`
   - Added keyword enrichment to 5 RSS collectors: BeInCrypto, CoinTelegraph, NewsBTC, Decrypt, CoinDesk
   - Updated `sample_records.py` with enriched display columns and keyword match mappings for all 6 collectors
   - 26 tests (5 sentiment aggregation, 5 collector enrichment, 11 sample records, 5 existing CryptoSlate)

2. [x] **Part B — Available Coins Endpoint**
   - `GET /api/v1/utils/available-coins/` — dynamic coin enumeration from DB
   - Added optional `ledger` query param to `GET /api/v1/utils/price-data/`
   - 4 new tests + fixed 1 pre-existing date-hardcoded test

3. [x] **Part C — Sprint Housekeeping**
   - Updated CURRENT_SPRINT.md, ROADMAP.md (Phase 4 marked complete)

## Verification

- 34 Sprint 2.40 tests passing (26 enrichment + 8 price data)
- mypy --strict: clean (132 files)
- ruff check + ruff format: clean
- Pre-existing tech debt: test_executor.py / test_trading_ws.py hangs (Redis emergency_stop key — Sprint 2.35)
