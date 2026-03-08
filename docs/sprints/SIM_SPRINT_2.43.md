# Sprint 2.43 Initialization Manifest (SIM)

**Focus**: Signal Data Model — `news_enrichment` Migration + Lab Signal Queries
**Team Composition**: Architect (Opus), Dockmaster (Sonnet), 2x Dev (Haiku)
**Depends On**: Sprint 2.42 (enrichment framework) COMPLETED

---

## Sprint Objectives

### Primary Goal
Replace the `news_keyword_match` table with a unified `news_enrichment` table using JSONB for flexible enrichment storage. Add materialized views for fast signal aggregation. Expose signal query endpoints for The Lab's AI agents.

### Success Criteria
- [ ] `news_enrichment` table created with JSONB `data` column + GIN index
- [ ] Alembic migration: data migrated from `news_keyword_match` → `news_enrichment`
- [ ] All enrichers (KeywordEnricher, LLMEnricher) write to `news_enrichment`
- [ ] `news_keyword_match` table deprecated (kept as backup, no new writes)
- [ ] Materialized views: `mv_signal_summary`, `mv_coin_sentiment_24h`
- [ ] Signal query endpoints for The Lab agents
- [ ] POLE entity enricher (Person, Organisation, Location, Event)
- [ ] All tests pass, mypy --strict clean, ruff clean

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect (Opus)
**Responsibilities**:
- [ ] Validate SIM follows template
- [ ] Review data migration strategy (zero-downtime approach)
- [ ] Review materialized view definitions for query performance
- [ ] Merge Track A before Track B starts API integration
- [ ] Run full test suite after merge
- [ ] Update `CURRENT_SPRINT.md`

### Track D: The Dockmaster (Orchestration)

**Agent**: Dockmaster (Sonnet)
**Responsibilities**:
- [ ] Provision Track A worktree (backend, port 8010)
- [ ] Provision Track B worktree (backend API + frontend, port 8020)
- [ ] Teardown on completion

---

## Architecture: Signal Data Model

### news_enrichment Table

```sql
CREATE TABLE news_enrichment (
    id SERIAL PRIMARY KEY,
    news_item_link VARCHAR NOT NULL REFERENCES news_item(link),
    enricher_name VARCHAR NOT NULL,        -- "keyword", "llm_sentiment", "entity_extraction"
    enrichment_type VARCHAR NOT NULL,      -- "sentiment", "keyword", "entity", "event", "regulatory"
    data JSONB NOT NULL DEFAULT '{}',      -- Flexible per enrichment_type (see schemas below)
    currencies TEXT[] DEFAULT '{}',         -- For fast array-contains filtering
    confidence FLOAT NOT NULL DEFAULT 0.0, -- 0.0 - 1.0
    enriched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate enrichments
    CONSTRAINT uq_enrichment UNIQUE (news_item_link, enricher_name, enrichment_type)
);

-- GIN index on JSONB for flexible querying
CREATE INDEX ix_enrichment_data ON news_enrichment USING GIN (data);

-- Array index for currency filtering
CREATE INDEX ix_enrichment_currencies ON news_enrichment USING GIN (currencies);

-- Composite index for time-range + enricher queries
CREATE INDEX ix_enrichment_enricher_time ON news_enrichment (enricher_name, enriched_at DESC);
```

### JSONB Data Schemas (by enrichment_type)

```python
# enrichment_type = "keyword"
{
    "keyword": "etf_approval",
    "category": "regulatory",
    "direction": "bullish",
    "impact_level": "high",
    "match_context": "SEC approves spot Bitcoin ETF application...",
    "temporal_hint": "recent"
}

# enrichment_type = "sentiment"
{
    "coins": [
        {"symbol": "BTC", "direction": "bullish", "confidence": 0.85, "rationale": "ETF approval positive"},
        {"symbol": "ETH", "direction": "bearish", "confidence": 0.6, "rationale": "Regulatory pressure cited"}
    ],
    "overall_sentiment": "mixed",
    "event_type": "regulatory"
}

# enrichment_type = "entity"
{
    "entities": [
        {"name": "SEC", "type": "organisation", "role": "regulator", "context": "approved filing"},
        {"name": "BlackRock", "type": "organisation", "role": "applicant", "context": "ETF issuer"},
        {"name": "Gary Gensler", "type": "person", "role": "chair", "context": "statement on approval"}
    ],
    "relationships": [
        {"subject": "SEC", "predicate": "approved", "object": "BlackRock ETF"},
        {"subject": "Gary Gensler", "predicate": "leads", "object": "SEC"}
    ]
}
```

### Materialized Views

```sql
-- Signal summary: per-coin sentiment aggregated over sliding windows
CREATE MATERIALIZED VIEW mv_coin_sentiment_24h AS
SELECT
    unnest(ne.currencies) AS coin,
    ne.enrichment_type,
    AVG(ne.confidence) AS avg_confidence,
    COUNT(*) AS signal_count,
    COUNT(*) FILTER (WHERE ne.data->>'direction' = 'bullish'
                     OR ne.data->'coins' @> '[{"direction": "bullish"}]') AS bullish_count,
    COUNT(*) FILTER (WHERE ne.data->>'direction' = 'bearish'
                     OR ne.data->'coins' @> '[{"direction": "bearish"}]') AS bearish_count,
    MAX(ne.enriched_at) AS latest_signal
FROM news_enrichment ne
WHERE ne.enriched_at > NOW() - INTERVAL '24 hours'
GROUP BY unnest(ne.currencies), ne.enrichment_type;

CREATE UNIQUE INDEX ON mv_coin_sentiment_24h (coin, enrichment_type);

-- Signal summary: broader time windows for trend analysis
CREATE MATERIALIZED VIEW mv_signal_summary AS
SELECT
    unnest(ne.currencies) AS coin,
    ne.enricher_name,
    ne.enrichment_type,
    date_trunc('hour', ne.enriched_at) AS hour_bucket,
    COUNT(*) AS signal_count,
    AVG(ne.confidence) AS avg_confidence,
    jsonb_agg(DISTINCT ne.data->'event_type') FILTER (WHERE ne.data ? 'event_type') AS event_types
FROM news_enrichment ne
WHERE ne.enriched_at > NOW() - INTERVAL '7 days'
GROUP BY unnest(ne.currencies), ne.enricher_name, ne.enrichment_type, date_trunc('hour', ne.enriched_at);

CREATE UNIQUE INDEX ON mv_signal_summary (coin, enricher_name, enrichment_type, hour_bucket);
```

### Migration Strategy

```
Phase 1: Create news_enrichment table (additive, zero downtime)
Phase 2: Migrate existing data from news_keyword_match → news_enrichment
Phase 3: Update enrichers to write to news_enrichment (dual-write period)
Phase 4: Verify data integrity, switch reads to news_enrichment
Phase 5: Stop writes to news_keyword_match (keep table as backup)
```

---

## Workspace Orchestration

| Track | Branch Name | Worktree Path | Port | Color | Container Prefix |
|-------|-------------|---------------|------|-------|-----------------|
| **Track A** | `feat/2.43-signal-datamodel` | `../sprint-2.43/track-a` | 8010 | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/2.43-signal-api` | `../sprint-2.43/track-b` | 8020 | `#2b9e3e` (Green) | `track-b` |

---

## Execution Strategy

**Sequential**: Track B depends on Track A's data model and enricher updates.
- Track A completes data model + migration + enricher updates → Track B builds signal query API.
- Track B can scaffold API routes and tests using mocked data while waiting.

**Critical Path**:
1. Track A: `news_enrichment` model + Alembic migration + GIN indexes
2. Track A: Migrate data from `news_keyword_match` → `news_enrichment`
3. Track A: Update KeywordEnricher + LLMEnricher to write to `news_enrichment`
4. Track A: POLE EntityEnricher implementation
5. Track A: Materialized views + refresh mechanism
6. Track B: Signal query API endpoints + Lab agent tool integration

---

### Track A: Signal Data Model & Migration

**Agent**: Dev (Haiku)

#### Context Injection Prompt

```
CONTEXT: Sprint 2.43 - Track A: Signal Data Model & Migration
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: Backend Dev

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.43/track-a
  INSTANCE_PORT: 8010
  CONTAINER_PREFIX: track-a
  STRICT_SCOPE: Locked to this directory.

ENVIRONMENT SETUP (MANAGED):
  docker-compose.override.yml maps 8010:80. DB port 5433, Redis 6380.

MISSION:
Create the unified news_enrichment table, migrate data from news_keyword_match,
update all enrichers to write to the new table, and add POLE entity extraction.

SPECIFIC OBJECTIVES:

1. CREATE news_enrichment MODEL (backend/app/models.py):
   Add a new SQLModel table class:
   - id: int (PK, autoincrement)
   - news_item_link: str (FK → news_item.link, index=True)
   - enricher_name: str (e.g., "keyword", "llm_sentiment", "entity_extraction")
   - enrichment_type: str ("sentiment", "keyword", "entity", "event", "regulatory")
   - data: dict (JSONB — use Column(JSON) with sa_column)
   - currencies: list[str] (TEXT[] — use Column(ARRAY(String)) with sa_column)
   - confidence: float (0.0-1.0, default 0.0)
   - enriched_at: datetime (server_default=func.now())

   Add unique constraint: (news_item_link, enricher_name, enrichment_type)

   IMPORTANT: Do NOT create a relationship back to NewsItem (SQLModel limitation).

2. ALEMBIC MIGRATION:
   Create migration that:
   a) Creates the news_enrichment table
   b) Adds GIN index on data column
   c) Adds GIN index on currencies column
   d) Adds composite index on (enricher_name, enriched_at DESC)
   e) Migrates data from news_keyword_match → news_enrichment:
      - keyword rows → enrichment_type="keyword", data={"keyword": ..., "category": ..., etc.}
      - llm_sentiment rows → enrichment_type="sentiment", data={"coins": [...], etc.}
   f) Does NOT drop news_keyword_match (kept as backup)

3. UPDATE ENRICHERS TO WRITE TO news_enrichment:
   Modify backend/app/enrichment/pipeline.py to store results in news_enrichment
   instead of news_keyword_match.

   Update KeywordEnricher (backend/app/enrichment/keyword_enricher.py):
   - enrich() returns EnrichmentResult objects
   - Pipeline stores as NewsEnrichment rows with enrichment_type="keyword"
   - data JSONB contains: keyword, category, direction, impact_level, match_context, temporal_hint

   Update LLMEnricher (backend/app/enrichment/llm_enricher.py):
   - enrich() returns EnrichmentResult objects
   - Pipeline stores as NewsEnrichment rows with enrichment_type="sentiment"
   - data JSONB contains: coins array, overall_sentiment, event_type

4. POLE ENTITY ENRICHER (backend/app/enrichment/entity_enricher.py):
   Create an EntityEnricher implementing IEnricher:
   - Uses the LLM provider (ISentimentProvider or a separate IEntityProvider)
   - Extracts POLE entities: Person, Organisation, Location, Event
   - Returns EnrichmentResult with enrichment_type="entity"
   - data JSONB contains: entities array + relationships array

   LLM prompt for entity extraction:
   Given a news article title and summary, extract:
   {
     "entities": [
       {"name": "...", "type": "person|organisation|location|event", "role": "...", "context": "..."}
     ],
     "relationships": [
       {"subject": "...", "predicate": "...", "object": "..."}
     ]
   }

   Register EntityEnricher in the pipeline (runs after LLMEnricher).

5. MATERIALIZED VIEWS:
   Create Alembic migration (or raw SQL executed via migration) for:

   a) mv_coin_sentiment_24h:
      - Per-coin sentiment aggregation over last 24 hours
      - Columns: coin, enrichment_type, avg_confidence, signal_count,
        bullish_count, bearish_count, latest_signal

   b) mv_signal_summary:
      - Per-coin, per-enricher, per-hour aggregation over last 7 days
      - Columns: coin, enricher_name, enrichment_type, hour_bucket,
        signal_count, avg_confidence, event_types

   Add a utility function to refresh materialized views:
   backend/app/enrichment/views.py:
     async def refresh_materialized_views(session: AsyncSession) -> None

   Call this at the end of EnrichmentPipeline.run() after all enrichers complete.

6. UPDATE SAMPLE RECORDS:
   Update backend/app/api/routes/sample_records.py PLUGIN_DATA_MAP
   to reflect news_enrichment columns instead of news_keyword_match.

7. TESTS:
   - test_news_enrichment_model.py — model CRUD, JSONB queries, GIN index usage
   - test_data_migration.py — verify news_keyword_match → news_enrichment migration
   - test_entity_enricher.py — mock LLM, test POLE extraction + relationship parsing
   - test_materialized_views.py — verify view creation and refresh
   - test_enricher_new_storage.py — verify enrichers write to news_enrichment

CONSTRAINTS:
  - NO LOCAL VENVS. Test inside Docker: docker compose exec backend bash scripts/test.sh
  - mypy --strict must pass
  - ruff check + ruff format must pass
  - MagicMock (not AsyncMock) for context managers in tests
  - SQLModel: no bidirectional relationships
  - Zero-downtime migration: news_keyword_match kept as backup
  - JSONB queries use PostgreSQL operators (@>, ?, ->>, etc.)

SUCCESS CRITERIA:
  - [ ] news_enrichment table created with all indexes
  - [ ] Data migrated from news_keyword_match (verified row counts match)
  - [ ] KeywordEnricher + LLMEnricher write to news_enrichment
  - [ ] EntityEnricher extracts POLE entities via LLM
  - [ ] Materialized views created and refreshable
  - [ ] All tests pass + mypy --strict clean

BRANCH: feat/2.43-signal-datamodel
```

#### Deliverables

1. **New model**: `NewsEnrichment` in models.py
2. **Migrations**: 2 Alembic migrations (table + materialized views)
3. **New enricher**: `entity_enricher.py` (POLE extraction)
4. **Modified**: pipeline.py, keyword_enricher.py, llm_enricher.py, sample_records.py
5. **New utility**: `enrichment/views.py` (materialized view refresh)
6. **Tests**: 5+ test files, ~25 tests

---

### Track B: Signal Query API + Lab Integration

**Agent**: Dev (Haiku)
**Depends On**: Track A data model

#### Context Injection Prompt

```
CONTEXT: Sprint 2.43 - Track B: Signal Query API + Lab Integration
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: Backend Dev + Frontend Dev

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.43/track-b
  INSTANCE_PORT: 8020
  CONTAINER_PREFIX: track-b
  STRICT_SCOPE: Locked to this directory.

MISSION:
Build signal query API endpoints that The Lab's AI agents can use to query
enrichment signals for trading decisions. Update the enrichment dashboard
to show the new unified enrichment data.

SPECIFIC OBJECTIVES:

1. SIGNAL QUERY API (backend/app/api/routes/signals.py):
   Create a new route module for Lab agent consumption:

   GET /api/v1/signals/coin/{symbol}
   - Returns all signals for a specific coin over a time range
   - Query params: hours (default 24), enrichment_type (optional filter)
   - Response: {
       coin: "BTC",
       period_hours: 24,
       signals: [
         {enrichment_type, enricher_name, data, confidence, enriched_at, news_title}
       ],
       summary: {
         total_signals, avg_confidence,
         bullish_count, bearish_count, neutral_count,
         dominant_sentiment, sentiment_score
       }
     }

   GET /api/v1/signals/summary
   - Returns the mv_coin_sentiment_24h materialized view data
   - Used by The Lab for quick market overview
   - Response: [{coin, enrichment_type, avg_confidence, signal_count,
                  bullish_count, bearish_count, latest_signal}]

   GET /api/v1/signals/trends
   - Returns the mv_signal_summary data for trend analysis
   - Query params: coin (optional), hours (default 168 = 7 days)
   - Response: [{coin, enricher_name, enrichment_type, hour_bucket,
                  signal_count, avg_confidence, event_types}]

   GET /api/v1/signals/entities
   - Returns entity network data (from entity enrichments)
   - Query params: entity_name (optional), entity_type (optional), hours (default 72)
   - Response: {
       entities: [{name, type, mention_count, related_coins, contexts}],
       relationships: [{subject, predicate, object, count, latest_at}]
     }

   POST /api/v1/signals/refresh-views
   - Triggers refresh of materialized views
   - Returns: {status: "refreshed", duration_ms}

   Register the router in backend/app/api/main.py

2. LAB AGENT TOOL (backend/app/services/agent/tools/signal_query.py):
   Create a LangGraph tool that Lab agents can use to query signals:

   @tool
   def query_market_signals(coin: str, hours: int = 24) -> dict:
       """Query enrichment signals for a cryptocurrency.
       Returns sentiment summary and recent signals."""

   This tool calls the signals API internally (or queries DB directly)
   and formats the response for LLM consumption.

   Register in the agent's tool list (backend/app/services/agent/tools/__init__.py)

3. ENRICHMENT DASHBOARD UPDATE (frontend):
   Update the enrichment dashboard (from Sprint 2.42) to show:
   - Signal coverage from news_enrichment (replacing news_keyword_match metrics)
   - Entity network visualization (simple list/table of top entities)
   - Per-coin sentiment breakdown (table or cards)
   - Add a "Refresh Views" button that calls POST /api/v1/signals/refresh-views

4. OPENAPI CLIENT REGENERATION:
   Regenerate the TypeScript client after API changes:
   bash scripts/generate-client.sh

5. TESTS:
   - test_signals_api.py — all signal query endpoints
   - test_signal_query_tool.py — Lab agent tool
   - test_entity_queries.py — entity network queries

CONSTRAINTS:
  - NO LOCAL VENVS. Test inside Docker: docker compose exec backend bash scripts/test.sh
  - mypy --strict must pass
  - ruff check + ruff format must pass
  - Frontend: Chakra UI v3, TanStack Query, Biome lint
  - Signal queries must use materialized views where possible (not raw aggregation)
  - Entity queries use JSONB operators for flexible filtering

SUCCESS CRITERIA:
  - [ ] All signal query endpoints return correct data
  - [ ] Lab agent tool queries signals and formats for LLM
  - [ ] Enrichment dashboard shows unified enrichment data
  - [ ] Materialized view refresh works via API
  - [ ] All tests pass + mypy --strict + npm run type-check + npm run lint

BRANCH: feat/2.43-signal-api
```

#### Deliverables

1. **New route module**: `signals.py` (5 endpoints)
2. **New agent tool**: `signal_query.py`
3. **Updated frontend**: Enrichment dashboard with signal data
4. **Updated**: OpenAPI client, api/main.py (router registration)
5. **Tests**: 3+ test files, ~20 tests

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data migration corrupts enrichments | Low | High | Keep news_keyword_match as backup, verify row counts |
| JSONB query performance | Medium | Medium | GIN indexes + materialized views for hot queries |
| Materialized view refresh latency | Low | Medium | Refresh async after enrichment, not blocking |
| Entity extraction LLM costs | Medium | Low | Batch entities with sentiment in single LLM call |
| news_keyword_match FK dependencies | Low | High | Audit all FK references before deprecation |

---

**Sprint Status**: 🟡 PLANNING
**Created By**: Architect (Opus)
**Depends On**: Sprint 2.42 COMPLETED
