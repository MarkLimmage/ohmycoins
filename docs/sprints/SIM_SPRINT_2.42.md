# Sprint 2.42 Initialization Manifest (SIM)

**Focus**: Enrichment Framework — IEnricher Pipeline + LLM Sentiment Integration
**Team Composition**: Architect (Opus), Dockmaster (Sonnet), 2x Dev (Haiku)
**Depends On**: Sprint 2.41 (collector cleanup) COMPLETED

---

## Sprint Objectives

### Primary Goal
Build an extensible enrichment pipeline that automatically extracts sentiment, coins, and keywords from collected news items using both rule-based and LLM-based enrichers. Enrichment runs automatically when new items are collected.

### Success Criteria
- [ ] `IEnricher` interface defined with `can_enrich()` / `enrich()` contract
- [ ] `KeywordEnricher` migrated from inline collector code to standalone enricher
- [ ] `LLMEnricher` calls Gemini 3.1 Flash-Lite via existing credential management
- [ ] LLM prompt handles multi-coin, multi-directional sentiment extraction
- [ ] `ISentimentProvider` interface allows swapping LLM for VADER (or other models)
- [ ] `enrichment_run` table tracks enrichment execution history
- [ ] Enrichment triggered automatically post-collection (in `StrategyAdapterCollector`)
- [ ] Batch enrichment endpoint: `POST /api/v1/enrichment/run`
- [ ] Enrichment stats endpoint: `GET /api/v1/enrichment/stats`
- [ ] Frontend enrichment dashboard with health/coverage metrics
- [ ] All tests pass, mypy --strict clean, ruff clean

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect (Opus)
**Responsibilities**:
- [ ] Validate SIM follows template
- [ ] Define `IEnricher` interface contract (below)
- [ ] Review Track A data model + LLM prompt design
- [ ] Merge Track A before Track B starts API integration
- [ ] Run full test suite after merge
- [ ] Update `CURRENT_SPRINT.md`

### Track D: The Dockmaster (Orchestration)

**Agent**: Dockmaster (Sonnet)
**Responsibilities**:
- [ ] Provision Track A worktree (backend, port 8010)
- [ ] Provision Track B worktree (frontend, port 8020)
- [ ] Teardown on completion

---

## Architecture: Enrichment Pipeline

### IEnricher Interface

```python
# backend/app/enrichment/base.py
from abc import ABC, abstractmethod
from app.models import NewsItem

class EnrichmentResult:
    """Single enrichment output — stored as one row in news_keyword_match (Sprint 2.42)
    or news_enrichment (Sprint 2.43 migration)."""
    enricher_name: str
    enrichment_type: str  # "keyword", "sentiment", "entity"
    data: dict            # Flexible JSON payload
    currencies: list[str]
    confidence: float

class IEnricher(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def can_enrich(self, item: NewsItem) -> bool:
        """Return True if this enricher should process this item."""
        ...

    @abstractmethod
    async def enrich(self, item: NewsItem) -> list[EnrichmentResult]:
        """Extract signals from a news item. Returns enrichment results."""
        ...
```

### ISentimentProvider Interface

```python
# backend/app/enrichment/providers/base.py
class SentimentResult:
    coin: str
    direction: str       # "bullish" | "bearish" | "neutral"
    confidence: float    # 0.0 - 1.0
    rationale: str       # Short explanation

class ISentimentProvider(ABC):
    @abstractmethod
    async def analyse(self, title: str, summary: str) -> list[SentimentResult]:
        """Analyse text and return per-coin sentiment."""
        ...
```

### Pipeline Flow

```
NewsItem collected
  → StrategyAdapterCollector.store_data() persists items
  → EnrichmentPipeline.run(new_items)
    → KeywordEnricher.enrich(item) → NewsKeywordMatch rows
    → LLMEnricher.enrich(item) → NewsKeywordMatch rows (sentiment type)
  → enrichment_run record created with stats
```

### Enrichment Trigger Model

Enrichment is triggered in TWO ways:
1. **Automatic**: After `StrategyAdapterCollector.store_data()` successfully stores new items,
   call `EnrichmentPipeline.run(new_items)` with only the newly-stored items.
2. **Manual batch**: `POST /api/v1/enrichment/run` triggers enrichment on all un-enriched items.

---

## Workspace Orchestration

| Track | Branch Name | Worktree Path | Port | Color | Container Prefix |
|-------|-------------|---------------|------|-------|-----------------|
| **Track A** | `feat/2.42-enrichment-backend` | `../sprint-2.42/track-a` | 8010 | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/2.42-enrichment-frontend` | `../sprint-2.42/track-b` | 8020 | `#2b9e3e` (Green) | `track-b` |

---

## Execution Strategy

**Sequential**: Track B depends on Track A's API endpoints.
- Track A completes enrichment backend + API → Track B builds dashboard.
- Track B can scaffold UI components in parallel using mocked data, then integrate.

**Critical Path**:
1. Track A: IEnricher framework, KeywordEnricher migration, enrichment_run model
2. Track A: LLMEnricher + ISentimentProvider + GeminiProvider
3. Track A: Auto-trigger in StrategyAdapterCollector, batch endpoint, stats endpoint
4. Track B: Enrichment dashboard, wired to real API

---

### Track A: Enrichment Backend

**Agent**: Dev (Haiku)
**Estimated Effort**: 3-4 days

#### Context Injection Prompt

```
CONTEXT: Sprint 2.42 - Track A: Enrichment Backend
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: Backend Dev

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.42/track-a
  INSTANCE_PORT: 8010
  CONTAINER_PREFIX: track-a
  STRICT_SCOPE: Locked to this directory.

ENVIRONMENT SETUP (MANAGED):
  docker-compose.override.yml maps 8010:80. DB port 5433, Redis 6380.

MISSION:
Build an extensible enrichment pipeline that extracts sentiment, coins, and keywords
from news items. Integrate Gemini 3.1 Flash-Lite for LLM-based analysis.

SPECIFIC OBJECTIVES:

1. CREATE ENRICHMENT FRAMEWORK (backend/app/enrichment/):
   Create a new package: backend/app/enrichment/
   Files:
   - __init__.py
   - base.py — IEnricher ABC, EnrichmentResult dataclass
   - pipeline.py — EnrichmentPipeline: registers enrichers, runs them on items
   - providers/__init__.py
   - providers/base.py — ISentimentProvider ABC, SentimentResult dataclass
   - providers/gemini.py — GeminiProvider (uses existing LLMFactory + user_llm_credentials)
   - providers/vader.py — VADERProvider stub (for future fallback)
   - keyword_enricher.py — KeywordEnricher (migrates logic from keyword_taxonomy.py)
   - llm_enricher.py — LLMEnricher (uses ISentimentProvider for multi-coin sentiment)

   The IEnricher interface:
   - name: str property
   - can_enrich(item: NewsItem) -> bool
   - enrich(item: NewsItem) -> list[EnrichmentResult]

   The ISentimentProvider interface:
   - analyse(title: str, summary: str) -> list[SentimentResult]
   - SentimentResult: coin, direction (bullish/bearish/neutral), confidence (0-1), rationale

2. KEYWORD ENRICHER (migrate from inline):
   Move the enrichment logic currently embedded in news_*.py collectors into
   KeywordEnricher. The enricher:
   - Uses match_keywords(), extract_currencies(), extract_context() from keyword_taxonomy.py
   - Returns EnrichmentResult objects with enrichment_type="keyword"
   - Stores results as NewsKeywordMatch rows (existing table, no migration needed)

   IMPORTANT: After migration, the news_*.py collectors should ONLY return NewsItem objects.
   Remove all NewsKeywordMatch creation from:
   - news_coindesk.py, news_cointelegraph.py, news_cryptoslate.py
   - news_decrypt.py, news_newsbtc.py
   Also remove aggregate_sentiment() calls from these collectors — sentiment
   will now be set by the enrichment pipeline.

3. LLM ENRICHER:
   LLMEnricher uses an ISentimentProvider to analyse articles:

   GeminiProvider implementation:
   - Load API key from user_llm_credentials table (provider='google', is_active=True)
   - Use google.generativeai SDK (already in dependencies as langchain_google_genai)
     OR use the existing LLMFactory._create_google_llm() from
     backend/app/services/agent/llm_factory.py
   - Model: read model_name from the credential record (currently 'gemini-3.1-flash-lite-preview')

   LLM Prompt design — single prompt extracts:
   {
     "coins": [
       {"symbol": "BTC", "sentiment": "bullish", "confidence": 0.85, "rationale": "ETF approval positive for price"},
       {"symbol": "ETH", "sentiment": "bearish", "confidence": 0.6, "rationale": "Regulatory pressure cited"}
     ],
     "entities": [
       {"name": "SEC", "type": "organization", "context": "regulatory action"}
     ],
     "event_type": "regulatory",
     "overall_sentiment": "mixed"
   }

   The prompt must handle:
   - Multi-coin articles (BTC positive, ETH negative in same article)
   - Articles with no crypto relevance (return empty coins array)
   - Confidence scoring (high confidence for explicit statements, low for implied)

   Store results as NewsKeywordMatch rows with enrichment metadata in the existing columns:
   - keyword = "llm_sentiment" (for sentiment results)
   - category = "sentiment" / "entity"
   - direction = coin-specific direction
   - currencies = [coin symbols]
   - match_context = rationale text
   - source_collector = enricher name

4. ENRICHMENT RUN TRACKING:
   Add an EnrichmentRun model (new table via Alembic migration):
   - id: int (PK, autoincrement)
   - enricher_name: str (e.g., "keyword", "llm_sentiment")
   - items_processed: int
   - items_enriched: int (items that produced at least one result)
   - items_skipped: int
   - items_failed: int
   - started_at: datetime
   - completed_at: datetime | None
   - status: str ("running", "completed", "failed")
   - error_message: str | None
   - trigger: str ("auto", "manual")

   Create the Alembic migration for this table.

5. AUTO-TRIGGER AFTER COLLECTION:
   In backend/app/services/collectors/strategy_adapter.py, after store_data()
   successfully stores new items:
   - Instantiate EnrichmentPipeline with registered enrichers
   - Call pipeline.run(new_items) with only the newly-persisted items
   - Wrap in try/except — enrichment failure must NOT fail the collector run

6. API ENDPOINTS (backend/app/api/routes/enrichment.py):
   Create a new route module:

   POST /api/v1/enrichment/run
   - Triggers batch enrichment on un-enriched items
   - Query param: enricher (optional, defaults to all)
   - Query param: limit (optional, defaults to 100)
   - Returns: {enrichment_run_id, items_queued}

   GET /api/v1/enrichment/stats
   - Returns enrichment coverage stats:
     {total_items, enriched_items, unenriched_items, coverage_pct,
      by_enricher: [{name, total_runs, items_enriched, last_run, avg_duration}]}

   GET /api/v1/enrichment/runs
   - Returns recent enrichment runs (paginated)

   Register the router in backend/app/api/main.py

7. TESTS:
   - test_keyword_enricher.py — migrated enrichment produces same results
   - test_llm_enricher.py — mock the LLM provider, test prompt/response parsing
   - test_gemini_provider.py — mock API calls, test response parsing
   - test_enrichment_pipeline.py — test pipeline runs enrichers in order
   - test_enrichment_api.py — test API endpoints
   - test_auto_trigger.py — test enrichment fires after collection

CONSTRAINTS:
  - NO LOCAL VENVS. Test inside Docker: docker compose exec backend bash scripts/test.sh
  - mypy --strict must pass
  - ruff check + ruff format must pass
  - MagicMock (not AsyncMock) for context managers in tests
  - SQLModel: no bidirectional relationships
  - Enrichment failure must not crash collectors

SUCCESS CRITERIA:
  - [ ] IEnricher + ISentimentProvider interfaces defined and working
  - [ ] KeywordEnricher produces identical results to old inline code
  - [ ] LLMEnricher calls Gemini and parses structured response
  - [ ] Enrichment auto-triggers after collection (new items only)
  - [ ] Batch enrichment endpoint works for backfill
  - [ ] enrichment_run table tracks all runs
  - [ ] All tests pass + mypy --strict clean

BRANCH: feat/2.42-enrichment-backend
```

#### Deliverables

1. **New package**: `backend/app/enrichment/` (8-10 files)
2. **Migration**: Alembic migration for `enrichment_run` table
3. **Modified**: 5 news collectors (remove inline enrichment), strategy_adapter.py (auto-trigger), api/main.py (register router)
4. **Tests**: 6+ test files, ~30 tests

---

### Track B: Enrichment Dashboard

**Agent**: Dev (Haiku)
**Estimated Effort**: 1-2 days
**Depends On**: Track A API endpoints

#### Context Injection Prompt

```
CONTEXT: Sprint 2.42 - Track B: Enrichment Dashboard
PROJECT: Oh My Coins - Trading Platform Frontend
ROLE: Frontend Dev

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.42/track-b
  INSTANCE_PORT: 8020
  CONTAINER_PREFIX: track-b
  STRICT_SCOPE: Locked to this directory.

MISSION:
Build an enrichment dashboard in the frontend showing enrichment health, coverage,
and run history. Similar in style to the existing collectors dashboard.

SPECIFIC OBJECTIVES:

1. ENRICHMENT DASHBOARD PAGE OR SECTION:
   Add an enrichment section to the existing Ledgers/admin area.
   Components:
   - EnrichmentOverview: total items, enriched items, coverage percentage (pie/donut chart)
   - EnricherCards: one card per enricher (keyword, llm_sentiment) showing:
     - Name and description
     - Items enriched count
     - Last run timestamp
     - Average duration
     - Error rate
   - EnrichmentRunsTable: recent runs with status, items processed, duration
   - ManualEnrichmentButton: triggers POST /api/v1/enrichment/run

2. API INTEGRATION:
   - Hook: useEnrichmentStats() — calls GET /api/v1/enrichment/stats
   - Hook: useEnrichmentRuns() — calls GET /api/v1/enrichment/runs
   - Hook: useTriggerEnrichment() — mutation for POST /api/v1/enrichment/run
   - Regenerate OpenAPI client after Track A merges

3. STYLING:
   - Use Chakra UI v3 components consistent with existing collector cards
   - Coverage metric as a prominent stat (e.g., "78% enriched")
   - Run status colours: completed=green, running=blue, failed=red

CONSTRAINTS:
  - Chakra UI v3 components
  - TanStack Query for data fetching
  - Biome for lint: npm run lint
  - Type check: npm run type-check

SUCCESS CRITERIA:
  - [ ] Enrichment overview shows coverage stats
  - [ ] Enricher cards display per-enricher health
  - [ ] Run history table shows recent enrichment runs
  - [ ] Manual trigger button works
  - [ ] npm run type-check + npm run lint pass

BRANCH: feat/2.42-enrichment-frontend
```

#### Deliverables

1. **New components**: EnrichmentOverview, EnricherCard, EnrichmentRunsTable
2. **New hooks**: useEnrichmentStats, useEnrichmentRuns, useTriggerEnrichment
3. **Updated**: OpenAPI client, route registration

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Gemini API rate limits | Medium | Medium | Implement backoff + batch size limits in LLMEnricher |
| LLM response parsing failures | Medium | Low | Strict JSON schema validation + fallback to keyword-only |
| Enrichment slows collection | Low | High | Enrichment runs async, failure doesn't block collector |
| Credential not found | Low | Medium | Graceful skip if no google credential in user_llm_credentials |

---

**Sprint Status**: 🟡 PLANNING
**Created By**: Architect (Opus)
**Depends On**: Sprint 2.41 COMPLETED
