# Sprint: Sentiment Enrichment Pipeline

**Version:** 1.0  
**Date:** 2026-04-09  
**Status:** PLANNING

## Objective

Upgrade the Reddit collector to capture full conversations (post body + top comments), generalize the enrichment pipeline to process any text source (not just NewsItem), and use Gemini Flash for LLM-based coin detection and weighted sentiment scoring.

## Background

### Current State
- Reddit collector (`human_reddit`) fetches **title only** from `/hot.json` (public, no OAuth)
- Sentiment is keyword regex ("bullish"/"bearish") — high false-positive rate (e.g. `\bOP\b` matches "Optimism" on every Reddit post)
- Coin detection is hardcoded regex against ~25 patterns — no link to tracked portfolio
- Enrichment pipeline (`backend/app/enrichment/`) exists but is **NewsItem-only**: `IEnricher.can_enrich()` checks `isinstance(item, NewsItem)`, `EnrichmentPipeline.run()` is typed `list[NewsItem]`, results FK to `news_item.link`
- Gemini provider (`enrichment/providers/gemini.py`) and LLM enricher exist but only process news titles+summaries
- `SentimentScore` table exists (`asset`, `source`, `score` -1..1, `magnitude`, `raw_data` JSON, `timestamp`) — currently written by ingestion service only
- Materialized views `mv_coin_sentiment_24h` and `mv_signal_summary` aggregate from `news_enrichment` only
- `SocialSentiment` dedup now enforced via `UNIQUE(platform, content, posted_at)` constraint

### Target State
- Reddit collector fetches post title + selftext + top N comments with engagement scores
- Shared enrichment service processes Reddit, news, and future sources via unified `IEnricher` interface
- Gemini Flash performs coin identification (replacing hardcoded regex) and conversation-level sentiment
- Engagement weighting (upvotes, comment count) stored alongside raw data
- Per-(source, coin) sentiment scores flow into `SentimentScore` for unified downstream consumption
- Materialized views updated to include social sentiment signals

## Architecture Decisions

### AD-1: Enrichment stays decoupled from collection
Collectors collect raw data. Enrichment runs on a separate schedule against stored data. A Gemini outage doesn't prevent data collection, and enrichment can be re-run/re-prompted without re-scraping.

### AD-2: Generalize enrichment pipeline, don't fork it
The existing `EnrichmentPipeline` and `IEnricher` interface are sound. They need widening (accept any model, not just `NewsItem`) rather than replacing. A parallel pipeline would fragment the codebase.

### AD-3: Results go to `SentimentScore`, not a new table
`SentimentScore` (`asset`, `source`, `score`, `magnitude`, `raw_data`, `timestamp`) already exists and is the right schema. The `source` field distinguishes `"reddit_llm"` from `"news_llm"` from `"keyword"`. No new table needed.

### AD-4: Reddit OAuth is a prerequisite
Without OAuth, Reddit rate-limits to ~10 req/min for public JSON endpoints. Fetching comments for 125 posts = 130+ requests. Reddit OAuth (free, script-type app) gives 100 req/min authenticated. This must be done first or the collector will 429 constantly.

### AD-5: Batch LLM calls to reduce cost
Instead of 1 Gemini call per post, batch 5-10 posts per prompt. Reduces system prompt overhead and cuts cost by 3-5x. Target: <$1/day.

### AD-6: Validate LLM coin extraction against tracked assets
Don't blindly trust Gemini's coin identification. Cross-reference extracted symbols against a configurable coin list (from config or DB) to filter hallucinated tickers.

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
