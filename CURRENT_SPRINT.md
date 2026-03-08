# Current Sprint: 2.41

**Status**: COMPLETED
**Objective**: News Collector Foundation Fix — Deduplicate, Clean, Fix Metrics
**Previous Sprint**: 2.40 (Keyword Enrichment Rollout - COMPLETED)

## Context

Sprint 2.40 rolled out keyword enrichment to all RSS collectors and added the available-coins endpoint. This sprint cleans up the collector infrastructure: removes dead/duplicate collectors, fixes misleading success metrics, centralizes User-Agent strings, and improves chart visualization with 12-hour aggregation.

## Pre-Sprint: Production Database Cleanup

SQL run manually to remove duplicate/dead collector rows and collector_runs. BeInCryptoNews disabled (Cloudflare JS challenge). 12 active collectors remaining after cleanup.

## Tasks

1. [x] **Track A — Backend Collector Cleanup**
   - Deleted 5 dead collector strategy files (news_cryptopanic, human_newscatcher, glass_nansen, human_rss, news_beincrypto)
   - Deleted 4 associated test files
   - Updated `initial_data.py` seeding — removed 5 dead collector entries
   - Centralized `HTTP_USER_AGENT` constant in `core/config.py`, applied to 7 active collectors
   - Fixed `get_summary_stats()` — `error_rate` replaces `uptime_pct`
   - Added `GET /api/v1/collectors/stats/chart-data` endpoint with 12-hour bucketing
   - Updated `sample_records.py` — removed 5 dead plugin mappings
   - Fixed 4 validation tests referencing deleted collectors

2. [x] **Track B — Frontend Metrics & Charts**
   - Regenerated OpenAPI TypeScript client
   - Collector cards show `error_rate` with color coding (0%=green, 1-10%=yellow, >10%=red)
   - Sparkline charts wired to new 12h aggregated chart-data endpoint
   - Updated `CollectorCardData` type and test fixtures

## Verification

- 844 tests passing, 0 failures
- mypy --strict: clean
- ruff check + ruff format: clean
- TypeScript type-check: clean
- Active collectors: 11 plugins (down from 16)
- Pre-existing tech debt: test_executor.py / test_trading_ws.py hangs (Redis emergency_stop key — Sprint 2.35)
