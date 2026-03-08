# Current Sprint: 2.43

**Status**: COMPLETED
**Objective**: Signal Data Model — `news_enrichment` Migration + Lab Signal Queries
**Previous Sprint**: 2.42 (Enrichment Framework - COMPLETED)

## Context

Sprint 2.42 built the extensible enrichment pipeline (IEnricher, KeywordEnricher, LLMEnricher, EnrichmentPipeline). This sprint replaces the `news_keyword_match` table with a unified `news_enrichment` table using JSONB for flexible enrichment storage, adds materialized views for fast signal aggregation, and exposes signal query endpoints for The Lab's AI agents.

## Tasks

1. [x] **Track A — Signal Data Model & Migration** ✅
   - NewsEnrichment model with JSONB `data` column + GIN indexes
   - Alembic migration: create table + migrate data from news_keyword_match
   - Updated KeywordEnricher + LLMEnricher pipeline to write to news_enrichment
   - POLE EntityEnricher: regex-based entity extraction (30+ patterns)
   - Materialized views: mv_coin_sentiment_24h, mv_signal_summary
   - View refresh utility integrated with EnrichmentPipeline
   - 27 new tests (model CRUD, entity enricher, pipeline storage)

2. [x] **Track B — Signal Query API + Lab Integration** ✅
   - Signal query endpoints: GET /signals/coin/{symbol}, /summary, /trends, /entities
   - POST /signals/refresh-views for materialized view refresh
   - Lab agent tool: query_market_signals for LangGraph workflow
   - Regenerated OpenAPI client with SignalsService
   - 9 new tests (6 API route + 3 agent tool), 902 total passing

## Verification

- All tests pass in container (902 passed)
- mypy --strict clean
- ruff check + ruff format clean
- npm run type-check clean
