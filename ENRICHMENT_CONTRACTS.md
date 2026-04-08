# Enrichment Sprint: Inter-Worker Contract
**Version:** 1.0  
**Date:** 2026-04-09

This contract defines the interface between Phase 1 (Engine Worker — Reddit collector) and Phase 2 (Graph Worker — enrichment pipeline). Both workers MUST adhere to these schemas. If a contract is impossible to implement, write a `CONTRACT_RFC.md` and halt.

---

## §1. SocialSentiment Table Schema (Phase 1 → Phase 2 Interface)

Phase 1 extends the existing `SocialSentiment` model. Phase 2 reads from it.

### Current columns (DO NOT MODIFY):
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | int | NO | PK auto-increment |
| `platform` | str(50) | NO | `"reddit"` |
| `content` | text | YES | Post title |
| `author` | str(100) | YES | Username |
| `score` | int | YES | Reddit upvotes |
| `sentiment` | str(20) | YES | **Phase 1 sets NULL** (enrichment fills later) |
| `currencies` | str[] ARRAY | YES | **Phase 1 sets NULL** (enrichment fills later) |
| `posted_at` | datetime(tz) | YES | Reddit `created_utc` |
| `collected_at` | datetime(tz) | NO | UTC now at collection time |

### New columns added by Phase 1:
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `body` | text | YES | Post selftext (body). NULL for title-only posts. |
| `comment_count` | int | YES | Total comment count from Reddit API. |
| `top_comments` | JSONB | YES | Array of top comment objects (see §1.1). |

### §1.1 `top_comments` JSONB Schema
```json
[
  { "text": "Comment body text", "score": 142, "author": "username" },
  { "text": "Another comment", "score": 87, "author": "user2" }
]
```
- Maximum 10 entries per post
- Ordered by `score` descending (best/top sort)
- `text` is the raw comment body (not HTML)
- `score` is the Reddit upvote count at collection time
- `author` may be `"[deleted]"`

### §1.2 Dedup Constraint
Existing: `UNIQUE(platform, content, posted_at)` — unchanged.
Phase 1 MUST NOT alter or remove this constraint.

### §1.3 Backward Compatibility
Phase 2 MUST handle rows where `body`, `comment_count`, and `top_comments` are all NULL. These are pre-upgrade rows collected before Phase 1 deployment. The enrichment prompt degrades gracefully to title-only analysis.

---

## §2. SentimentScore Table (Phase 2 Output)

Phase 2 writes enrichment results here. Existing table — no schema changes.

| Column | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `asset` | str | Coin symbol, e.g. `"BTC"`. MUST be validated against allow-list. |
| `source` | str | `"reddit_llm"` for Reddit-sourced, `"news_llm"` for news-sourced |
| `score` | float | -1.0 (max bearish) to 1.0 (max bullish). 0.0 = neutral. |
| `magnitude` | float | Confidence × engagement weight. Range 0.0 to 1.0. |
| `raw_data` | JSON | Full LLM response for this coin extraction |
| `timestamp` | datetime(tz) | `posted_at` of the source item (NOT enrichment time) |

### §2.1 `source` Values
| Value | Meaning |
|---|---|
| `"reddit_llm"` | LLM sentiment from Reddit conversations |
| `"news_llm"` | LLM sentiment from news articles |
| `"keyword"` | Existing keyword-based extraction |

### §2.2 Coin Symbol Validation
Extracted coins MUST be validated against a configurable allow-list before writing to `SentimentScore`. Hallucinated or irrelevant symbols are discarded. The allow-list source is TBD (config file, DB query, or hardcoded set) — worker chooses implementation.

---

## §3. EnrichmentRecord Table (Phase 2 Creates)

New table for universal enrichment provenance tracking.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | int | NO | PK |
| `source_table` | str(50) | NO | `"social_sentiment"`, `"news_item"`, etc. |
| `source_id` | int | NO | PK of the source row |
| `enricher_name` | str(50) | NO | `"social_llm_sentiment"`, `"keyword"`, etc. |
| `enrichment_type` | str(50) | NO | `"sentiment"`, `"entity"`, `"keyword"` |
| `data` | JSONB | YES | Flexible enrichment payload |
| `currencies` | str[] ARRAY | YES | Detected coins |
| `confidence` | float | YES | 0.0 to 1.0 |
| `enriched_at` | datetime(tz) | NO | UTC timestamp of enrichment |

**Unique constraint:** `(source_table, source_id, enricher_name, enrichment_type)`

This table is the "enriched already?" check: Phase 2 queries for items NOT IN this table to determine what needs enrichment.

---

## §4. Gemini Provider Interface (Phase 2 Internal)

### §4.1 Batch Input
```python
@dataclass
class TextInput:
    text: str           # Concatenated conversation text
    source_id: int      # SocialSentiment.id or NewsItem.id
    metadata: dict      # { "score": 42, "comment_count": 15, "platform": "reddit" }
```

### §4.2 Batch Output
```python
@dataclass
class CoinSentiment:
    coin: str           # Validated symbol, e.g. "BTC"
    score: float        # -1.0 to 1.0
    confidence: float   # 0.0 to 1.0
    rationale: str      # Brief LLM-generated explanation
    source_id: int      # Back-reference to input
```

### §4.3 Batch Size
- Default: 5 items per Gemini call
- Maximum: 10 items per call
- On JSON parse failure: retry with batch size 1

### §4.4 Backward Compatibility
The existing `analyse(title: str, summary: str)` method MUST be preserved for the existing `LLMEnricher` (news). The new batch interface is additive.

---

## §5. Migration Ordering

- Phase 1 migration: `down_revision = 'f4e3d2c1b0a9'` (current head)
- Phase 2 migration: `down_revision = 'f4e3d2c1b0a9'` (current head)
- Both create independent alembic branches from the same parent
- Supervisor creates a merge migration during Phase 3 integration
- **Workers MUST NOT create merge migrations themselves**
