# Sprint 2.61: BYOM Multi-Model & Enrichment Hardening

**Version:** 1.0  
**Date:** 2026-04-09  
**Status:** PLANNING

## Objective

Expand BYOM credential management to support multiple models per provider (e.g. gemini-3-flash-preview AND gemini-3.1-flash-lite-preview under one Google API key), add inline credential editing, and fix the enrichment scheduler phantom-record bug from Sprint 2.60.

## Background

### Current State — BYOM Credential Management
- **One active credential per provider per user** — enforced in application logic (`create_llm_credentials()` rejects if an active credential for the same provider exists)
- **No edit endpoint** — `UserLLMCredentialsUpdate` model exists but no PATCH/PUT route uses it. Error message says "Use PUT to update" but only `PUT .../default` exists (sets default flag, not API key)
- **Frontend is create-only** — `LLMCredentialForm.tsx` has no edit mode; user must delete and re-add to change API key or model
- **No DB uniqueness constraint** — one-per-provider is app logic only; race conditions could create duplicates
- **Model list outdated** — requirements reference gpt-4/gemini-1.5-pro/claude-3; current models are gpt-4o/gemini-3.1/claude-4

### Current State — Enrichment Pipeline
- `_store_enrichment_records()` in `scheduler.py` writes EnrichmentRecord for ALL items unconditionally after `pipeline.run()`, even when LLM calls fail
- This caused 544 phantom records during first backfill attempt (items marked "processed" with no SentimentScore output)
- `_extract_text()` helper added for langchain-google-genai 4.x list content — appears stable but needs hardening

### Key Files
| File | Role |
|------|------|
| `backend/app/models.py` L353-460 | UserLLMCredentials model + CRUD schemas |
| `backend/app/api/routes/users.py` L288-658 | BYOM API endpoints |
| `frontend/src/routes/_layout/llm-settings.tsx` | Settings page route |
| `frontend/src/components/Agent/LLMCredentialForm.tsx` | Create form |
| `frontend/src/components/Agent/LLMCredentialList.tsx` | List + actions |
| `frontend/src/client/types.gen.ts` L1213-1290 | Generated TS types |
| `backend/app/enrichment/scheduler.py` | Enrichment scheduler (bug) |
| `backend/app/enrichment/social_enricher.py` | Social sentiment enricher |

## Workstream A: Backend — BYOM Multi-Model + Edit

### A1. Remove one-per-provider constraint
- In `create_llm_credentials()` (users.py ~L327): change the duplicate check from `(user_id, provider, is_active)` to `(user_id, provider, model_name, is_active)`.
  - Same provider + same model = reject (already exists)
  - Same provider + different model = allow (multiple models per provider)
- Add DB unique constraint: `UniqueConstraint('user_id', 'provider', 'model_name', name='uq_user_llm_cred_provider_model')` filtered to `is_active=True` rows only. If filtered unique isn't feasible in Alembic, use a partial unique index.
- Alembic migration required.

### A2. Add PATCH endpoint for credential editing
- New route: `PATCH /api/v1/users/me/llm-credentials/{credential_id}`
- Uses existing `UserLLMCredentialsUpdate` schema (already defined: `model_name`, `api_key`, `is_default`, `is_active`)
- If `api_key` is provided: re-encrypt with current ENCRYPTION_KEY, update `encrypted_api_key`
- If `model_name` is changed: validate uniqueness against `(user_id, provider, new_model_name, is_active=True)`
- Update `updated_at` timestamp
- Return `UserLLMCredentialsPublic`
- Ownership check: credential must belong to `current_user`

### A3. Regenerate OpenAPI client
- After backend changes, regenerate `frontend/src/client/` from updated OpenAPI spec
- Verify new types appear: `UserLLMCredentialsUpdate`, `updateLlmCredential()` method

## Workstream B: Frontend — Multi-Model UI

### B1. Credential list grouped by provider
- `LLMCredentialList.tsx`: group credentials by `provider` field
- Each provider section: collapsible header with provider icon/name, expand to show all models
- Each credential row: model name, masked API key, is_default badge, last_validated_at, actions

### B2. Inline edit mode
- Add "Edit" button to each credential row in `LLMCredentialList.tsx`
- Clicking Edit: row expands into inline form (model_name field, optional new API key field, save/cancel)
- Save calls `PATCH /api/v1/users/me/llm-credentials/{id}` with only changed fields
- If API key changed: auto-validate via existing `validateLlmCredential()` before saving
- On success: invalidate React Query cache `["llmCredentials"]`, collapse edit form

### B3. Create form update
- `LLMCredentialForm.tsx`: if user already has a credential for the selected provider, allow creation (remove "already exists" error handling)
- Model name should be a required field (not optional) to distinguish multiple credentials per provider

## Workstream C: Enrichment Bug Fixes

### C1. Fix phantom EnrichmentRecord bug
- In `scheduler.py`, `_store_enrichment_records()` currently writes records for ALL items
- Fix: pass the pipeline run results to `_store_enrichment_records()` and only write records for items that produced at least one `EnrichmentResult`
- Approach: `pipeline.run()` returns `EnrichmentRun` — but that's aggregate counts. Need to track per-item success.
- Recommended: have `SocialSentimentEnricher.enrich()` return empty list `[]` on LLM failure (already does this). In `_store_enrichment_records()`, cross-reference against `SentimentScore` rows written in this session (query for source_id match with `source='reddit_llm'` and `timestamp >= run_start`)
- Alternative: simpler — track enriched item IDs in the pipeline and pass to `_store_enrichment_records()`

### C2. Harden _extract_text()
- Add handling for nested content parts (e.g. thinking + text parts mixed)
- Add logging when content type is unexpected
- Guard against None/empty content

## Parallelism Analysis

```
Workstream A (Backend BYOM)  ─────────────────►  merge
Workstream C (Enrichment Fix) ────►  merge        │
                                                    ├─► Integration
Workstream B (Frontend BYOM)  ────────────────►  merge
```

- **A + C** can run in one backend worker (both modify backend, no file conflicts)
- **B** runs in a separate frontend worker (depends on A3 OpenAPI regen)
- Integration: B depends on A being merged first (needs new API endpoint + regenerated client)

## Acceptance Criteria

### BYOM Multi-Model
- [ ] User can add gemini-3-flash-preview AND gemini-3.1-flash-lite-preview under same Google provider
- [ ] User can add gpt-4o AND gpt-4o-mini under same OpenAI provider
- [ ] Duplicate (same provider + same model) is still rejected
- [ ] Editing API key re-encrypts and updates the credential
- [ ] Editing model_name updates without requiring re-entry of API key
- [ ] Frontend shows credentials grouped by provider
- [ ] Frontend inline edit mode works for API key rotation

### Enrichment Hardening
- [ ] After a backfill where LLM fails for some items, only successfully-enriched items get EnrichmentRecord rows
- [ ] Subsequent scheduler run picks up the failed items and retries them
- [ ] `_extract_text()` handles list, string, and None content gracefully

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Frontend depends on backend PATCH endpoint | B blocked until A merged | Run A first, regen client, then spawn B |
| Partial unique index not supported in all Alembic backends | Migration failure | Use application-level check as fallback, add normal unique constraint on `(user_id, provider, model_name)` |
| Edit API key without re-validation could store invalid key | Enrichment fails silently | Enforce validation on API key change in PATCH endpoint |

---

## Phase Breakdown

### Phase 1 — Reddit Collector Upgrade (Engine Worker)
**Branch:** `feature/reddit-deep-collector`  
**Worktree:** `../omc-lab-engine`  
**Parallel:** YES — runs simultaneously with Phase 2

#### 1.1 Reddit OAuth Integration
- Add `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` to `core/config.py` and `.env.template`
- Implement OAuth2 app-only token fetch (`grant_type=client_credentials`) in collector
- Use authenticated requests to `oauth.reddit.com` when credentials present
- Fall back gracefully to public `www.reddit.com` JSON API if not configured
- Token refresh on 401 (Reddit access tokens expire after 1 hour)

#### 1.2 Deep Post Fetching
- After listing `/hot.json`, fetch `{permalink}.json?limit=10&sort=best` for each post
- Extract: `title`, `selftext` (post body), top 10 comments (body + score + author)
- Store in expanded `SocialSentiment` model:
  - `body: str | None` (Text, nullable) — post selftext
  - `comment_count: int | None` — number of comments on post
  - `top_comments: dict | None` (JSONB, nullable) — `[{ "text": "...", "score": 123, "author": "..." }]`

#### 1.3 Remove Hardcoded Sentiment Analysis
- Delete `_analyze_sentiment()` keyword method → store `sentiment=None`
- Delete `_extract_currencies()` regex method → store `currencies=None`
- These fields will be populated by the enrichment pipeline (Phase 2)
- Keep `score` (Reddit upvotes) as raw data

#### 1.4 Rate Limit Management
- With OAuth: 1 req/sec (100/min limit, we use ~130 requests)
- Without OAuth: 2s per request (existing conservative behavior)
- Total time budget: <5 min per run to fit `*/15` schedule
- Add `Retry-After` header handling for 429 responses

#### Schema Migration
```sql
ALTER TABLE social_sentiment ADD COLUMN body TEXT;
ALTER TABLE social_sentiment ADD COLUMN comment_count INTEGER;
ALTER TABLE social_sentiment ADD COLUMN top_comments JSONB;
```

#### NOT in scope
- LLM analysis (Phase 2)
- Enrichment pipeline changes (Phase 2)
- New subreddits or data sources
- Any changes to news collectors or enrichment code

---

### Phase 2 — Generalized Enrichment Pipeline (Graph Worker)
**Branch:** `feature/enrichment-generalization`  
**Worktree:** `../omc-lab-graph`  
**Parallel:** YES — runs simultaneously with Phase 1

#### 2.1 Widen `IEnricher` Interface
- `EnrichmentPipeline.run()` signature: `list[NewsItem]` → `list[SQLModel]` (or `list[Any]`)
- Existing enrichers (`keyword_enricher`, `entity_enricher`, `llm_enricher`) keep `can_enrich()` gating on `isinstance(item, NewsItem)` — no behavioral change for existing code
- New enrichers gate on their specific types

#### 2.2 Create `EnrichmentRecord` Table
Universal enrichment storage that supports any source:
```
enrichment_record:
  id: int (PK)
  source_table: str(50)           # "social_sentiment", "news_item", "catalyst_events"
  source_id: int                  # FK to source item
  enricher_name: str(50)          # "social_llm_sentiment", "keyword", etc.
  enrichment_type: str(50)        # "sentiment", "entity", "keyword"
  data: JSONB                     # Flexible enrichment payload
  currencies: str[] (ARRAY)       # Detected coins
  confidence: float
  enriched_at: datetime(tz)

  UNIQUE(source_table, source_id, enricher_name, enrichment_type)
```
Keep existing `NewsEnrichment` table for backward compatibility. New enrichments go to `EnrichmentRecord`.

#### 2.3 Build `SocialSentimentEnricher`
New enricher implementing `IEnricher`:
- `can_enrich(item)`: accepts `SocialSentiment` items
- `enrich(item)`: builds conversation context from `title + body + top_comments`
  - Gracefully degrades: title-only if `body`/`top_comments` are null (old rows)
  - Includes engagement metadata (score, comment_count) in prompt context
- Calls adapted Gemini provider (see 2.4) with batched input
- Returns per-coin `EnrichmentResult` objects
- Also writes per-coin rows to `SentimentScore` (source=`"reddit_llm"`)

#### 2.4 Adapt Gemini Provider for Generic Text
Current interface: `analyse(title: str, summary: str)` → too narrow.
New interface:
```python
@dataclass
class TextInput:
    text: str
    source_id: int
    metadata: dict  # { "score": 42, "comment_count": 15, "platform": "reddit" }

@dataclass
class CoinSentiment:
    coin: str           # symbol e.g. "BTC"
    score: float        # -1.0 to 1.0
    confidence: float   # 0.0 to 1.0
    rationale: str      # brief explanation
    source_id: int      # back-reference

async def analyse_batch(self, inputs: list[TextInput]) -> list[CoinSentiment]
```
- Batch 5-10 items per Gemini call
- Prompt includes engagement context for weighting
- Validate extracted coin symbols against configurable allow-list
- Keep backward-compatible `analyse(title, summary)` for existing news enricher

#### 2.5 Enrichment Scheduler
New cron job registered in orchestrator APScheduler:
- Schedule: `*/30 * * * *` (every 30 min, configurable)
- Queries `SocialSentiment` rows with no matching `EnrichmentRecord` (LEFT JOIN IS NULL pattern)
- Queries `NewsItem` rows similarly (for future re-enrichment)
- Feeds batches through generalized pipeline
- Tracks runs via existing `EnrichmentRun` model

#### 2.6 Update Materialized Views
- `mv_coin_sentiment_24h`: add UNION with `SentimentScore` rows where `source LIKE '%reddit%'`
- `mv_signal_summary`: include social sentiment signal counts

#### NOT in scope
- Reddit collector changes (Phase 1)
- Frontend/UI changes
- Modifying existing `keyword_enricher` or `entity_enricher` behavior
- Changing the existing `NewsEnrichment` table structure

---

### Phase 3 — Integration & Validation (Supervisor, Sequential)
**No separate worker.** Executed by Supervisor after Phase 1+2 merge.

1. Merge sequence: Engine → Graph → Main (standard protocol)
2. Create alembic merge migration for the two branch heads
3. Wire enrichment scheduler into orchestrator's APScheduler config
4. Backfill: one-time enrichment run on existing `SocialSentiment` rows
5. Validate: confirm `SentimentScore` rows populated for Reddit-sourced coins
6. Verify materialized views include social signals
7. Deploy and monitor enrichment run costs via `EnrichmentRun` stats

---

## The Contract: SocialSentiment Schema

This is the critical interface between Phase 1 and Phase 2.

Phase 1 (Engine) adds columns: `body`, `comment_count`, `top_comments`.  
Phase 2 (Graph) reads from `SocialSentiment` to build enrichment input.

**Rules:**
- Phase 2 MUST handle both old rows (`body=None`, `top_comments=None`) and new rows (populated)
- Enrichment prompt gracefully degrades: title-only analysis for old rows, full conversation for new rows
- Both phases branch from current `main` head (`cc0efa0`)
- Migration ordering resolved at merge time via alembic merge revision

---

## Environment Requirements

### New Environment Variables
| Variable | Required | Default | Used By |
|---|---|---|---|
| `REDDIT_CLIENT_ID` | No (graceful fallback) | `None` | Phase 1: Reddit OAuth |
| `REDDIT_CLIENT_SECRET` | No (graceful fallback) | `None` | Phase 1: Reddit OAuth |
| `GOOGLE_API_KEY` | Yes (or via UserLLMCredentials) | `None` | Phase 2: Gemini enrichment |

### Cost Estimates
| Item | Per-Run | Per-Day (`*/30`) | Per-Month |
|---|---|---|---|
| Gemini Flash (Reddit, ~125 posts batched) | ~$0.003 | ~$0.15 | ~$4.50 |
| Gemini Flash (News, ~200 articles batched) | ~$0.005 | ~$0.24 | ~$7.20 |
| Reddit OAuth API | Free | Free | Free |
| **Total** | | | **~$12/month** |

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Reddit 429 rate-limiting without OAuth | High | Phase 1 unusable | OAuth is prerequisite; fallback to title-only on 429 |
| Gemini hallucinates coin mentions | Medium | Bad data in SentimentScore | Validate against tracked asset allow-list |
| Batched prompts return malformed JSON | Medium | Lost enrichment run | Retry with smaller batch; fall back to single-item |
| Alembic migration conflict at merge | Low | Merge blocked | Independent migrations → merge revision at integration |
| Gemini API cost exceeds estimates | Low | Budget | Monitor via EnrichmentRun stats; add daily spend cap |
| Reddit changes JSON API format | Low | Collector breaks | Schema validation on response; alert on parse failures |
