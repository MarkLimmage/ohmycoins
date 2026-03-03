# Current Sprint: 2.38

**Status**: IN PROGRESS
**Objective**: Collector Observability & Health
**Previous Sprint**: 2.37 (Collector Rehabilitation & Legacy Removal - COMPLETED)

## Context

Sprint 2.37 shipped the collector plugin system with 16 collectors. Production stats reveal only 3 of 16 are healthy. Root cause: 6 RSS collectors return `list[dict]` from `collect()`, but `StrategyAdapterCollector.store_data()` checks `hasattr(item, "id")` — dicts fail this, so data is silently discarded.

## Tasks

1. [ ] **Part A — Sample Records Feature**
   - Backend: `sample_records.py` module with plugin-to-table mapping + `get_sample_records()` function
   - Backend: `GET /{id}/sample-records` API endpoint on collectors router
   - Frontend: `useSampleRecords` hook, `SampleRecordsDialog.tsx`, `CollectorCard` button
   - Tests: API route tests for sample records endpoint

2. [ ] **Part B — Fix Dict-Returning RSS Collectors**
   - Fix 6 files to return `list[NewsItem]` instead of `list[dict]`:
     - `news_beincrypto.py`, `news_coindesk.py`, `news_cointelegraph.py`
     - `news_cryptoslate.py`, `news_decrypt.py`, `news_newsbtc.py`
   - Parse `pubDate` RSS field → datetime for `published_at`
   - Construct `NewsItem` model instances with `source`, `title`, `link`, `summary`, `published_at`

3. [ ] **Part C — Sprint Housekeeping**
   - Update `CURRENT_SPRINT.md` to Sprint 2.38
   - Update `LOGBOOK.md` at completion

## Shipped Commits
(none yet)
