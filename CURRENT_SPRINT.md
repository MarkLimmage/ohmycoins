# Current Sprint: 2.42

**Status**: COMPLETED
**Objective**: Enrichment Framework — IEnricher Pipeline + LLM Sentiment Integration
**Previous Sprint**: 2.41 (News Collector Foundation Fix - COMPLETED)

## Context

Sprint 2.41 cleaned up dead collectors, centralized User-Agent, and fixed metrics. This sprint builds an extensible enrichment pipeline that extracts sentiment, coins, and keywords from news items using both rule-based (keyword taxonomy) and LLM-based (Gemini) enrichers. Enrichment runs automatically after collection.

## Tasks

1. [x] **Track A — Enrichment Backend** ✅
   - IEnricher interface + ISentimentProvider interface
   - KeywordEnricher (rule-based keyword taxonomy enrichment)
   - LLMEnricher + GeminiSentimentProvider (multi-coin LLM sentiment)
   - EnrichmentPipeline orchestrator with run tracking
   - EnrichmentRun model + Alembic migration
   - Auto-trigger after collection in StrategyAdapterCollector
   - API: POST /api/v1/enrichment/run, GET /stats, GET /runs
   - 34 tests (29 framework + 5 API route), 878 total passing

2. [x] **Track B — Enrichment Dashboard** ✅
   - EnrichmentOverview, EnricherCards, EnrichmentRunsTable components
   - Manual trigger button with loading/success/error states
   - Hooks: useEnrichmentStats, useEnrichmentRuns, useTriggerEnrichment
   - Regenerated OpenAPI client with EnrichmentService
   - Sidebar navigation link, route at /enrichment
   - type-check + lint clean

## Break-In Work (Post-Completion)

3. [x] **Linting & Type Safety Fixes** ✅
   - Addressed mypy strict errors in `backend/app/api/routes/collectors.py` (SQLAlchemy select/where type mismatches).
   - Fixed `backend/app/core/collectors/sample_records.py` type errors (`in_` operator).
   - Verified clean lint run in container: `docker compose run --rm backend bash scripts/lint.sh`.

4. [x] **Collector Stats Bugfix** ✅
   - Resolves 500 Error on dashboard charts (`date_trunc` 12h interval error). Replaced with `date_bin` for correct 12-hour bucketing in `backend/app/api/routes/collectors.py`.
   - improved test hygiene: Updated `backend/tests/conftest.py` to truncate all tables (including `CollectorRuns`, `NewsItem`) between tests to prevent data leakage.

## Verification

- All tests pass in container
- mypy --strict clean
- ruff check + ruff format clean
- npm run type-check + npm run lint clean
