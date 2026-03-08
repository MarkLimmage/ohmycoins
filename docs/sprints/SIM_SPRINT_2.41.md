# Sprint 2.41 Initialization Manifest (SIM)

**Focus**: News Collector Foundation Fix — Deduplicate, Clean, Fix Metrics
**Team Composition**: Architect (Opus), Dockmaster (Sonnet), 2x Dev (Haiku)

---

## Sprint Objectives

### Primary Goal
Fix broken news collection infrastructure: eliminate duplicate collector entries, remove dead/legacy collectors, fix misleading success metrics, and improve chart visualisation.

### Success Criteria
- [ ] Zero duplicate collector entries in DB (one row per plugin)
- [ ] Dead collectors removed from codebase and DB (cryptopanic, newscatcher, nansen, HumanRSS, coinmarketcap, yahoo)
- [ ] BeInCrypto collector disabled (Cloudflare JS challenge — not fixable without headless browser)
- [ ] All collectors use realistic User-Agent string (centralised constant)
- [ ] Frontend shows `error_rate` instead of `success_rate`
- [ ] Charts use 12-hour aggregation instead of per-run
- [ ] All tests pass (`docker compose exec backend bash scripts/test.sh`)
- [ ] `mypy --strict` + `ruff check` clean

---

## Pre-Sprint: Production Database Cleanup

**IMPORTANT**: The Architect provides these SQL statements for the user to run manually against the production database. No Alembic migration is needed — these are data-only operations on existing tables.

```sql
-- ============================================================
-- SPRINT 2.41 — PRODUCTION DATABASE CLEANUP
-- Run these manually. The codebase changes prevent re-seeding.
-- ============================================================

-- 1. Delete orphaned collector_runs for collectors being removed
DELETE FROM public.collector_runs
WHERE collector_name IN (
  -- Old lowercase duplicates (replaced by CamelCase versions)
  'beincrypto', 'coindesk', 'news_cointelegraph', 'news_cryptoslate',
  'news_decrypt', 'news_newsbtc', 'news_cryptopanic', 'news_coinmarketcap',
  -- Dead/legacy collectors
  'yahoo', 'HumanRSSCollector', 'NewscatcherNews', 'NansenSmartMoney',
  'CryptoPanicNews', 'BeInCryptoNews'
);

-- 2. Delete the collector rows themselves
DELETE FROM public.collector
WHERE name IN (
  -- Old lowercase duplicates
  'beincrypto', 'coindesk', 'news_cointelegraph', 'news_cryptoslate',
  'news_decrypt', 'news_newsbtc', 'news_cryptopanic', 'news_coinmarketcap',
  -- Dead/legacy collectors
  'yahoo', 'HumanRSSCollector', 'NewscatcherNews', 'NansenSmartMoney',
  'CryptoPanicNews', 'BeInCryptoNews'
);

-- 3. Disable BeInCrypto (Cloudflare blocks non-browser requests)
UPDATE public.collector SET is_enabled = false
WHERE name = 'BeInCryptoNews';
-- If BeInCryptoNews was already deleted above, also handle any remaining:
UPDATE public.collector SET is_enabled = false
WHERE plugin_name = 'news_beincrypto';

-- 4. Verify remaining collectors (should be ~10)
SELECT name, plugin_name, is_enabled FROM public.collector ORDER BY name;
```

**Expected remaining collectors after cleanup:**
| Name | Plugin | Enabled |
|------|--------|---------|
| CoinDeskNews | news_coindesk | true |
| CoinSpotAnnouncements | catalyst_coinspot_announcements | true |
| CoinspotExchange | CoinspotExchange | true |
| CoinTelegraphNews | news_cointelegraph | true |
| CryptoSlateNews | news_cryptoslate | true |
| DecryptNews | news_decrypt | true |
| DeFiLlama | glass_defillama | true |
| Ethereum Chain Walker | GlassChainWalker | true |
| GlassChainWalker | GlassChainWalker | true |
| NewsBTCNews | news_newsbtc | true |
| RedditSentiment | human_reddit | true |
| SECFilings | catalyst_sec | true |

---

## Agent Assignments

### Track S: The Architect (Strategy & Governance)

**Agent**: The Architect (Opus)
**Responsibilities**:
- [ ] Validate SIM follows template structure
- [ ] Provide DB cleanup SQL to user (above)
- [ ] Review and merge Track A + Track B PRs
- [ ] Run full test suite after merge
- [ ] Update `CURRENT_SPRINT.md` upon completion

### Track D: The Dockmaster (Orchestration)

**Agent**: Dockmaster (Sonnet)
**Responsibilities**:
- [ ] Provision Track A worktree (backend, port 8010)
- [ ] Provision Track B worktree (frontend, port 8020)
- [ ] Inject context prompts per track
- [ ] Teardown worktrees on completion

---

## Workspace Orchestration

| Track | Branch Name | Worktree Path | Port | Color | Container Prefix |
|-------|-------------|---------------|------|-------|-----------------|
| **Track A** | `feat/2.41-collector-cleanup` | `../sprint-2.41/track-a` | 8010 | `#3771c8` (Blue) | `track-a` |
| **Track B** | `feat/2.41-frontend-metrics` | `../sprint-2.41/track-b` | 8020 | `#2b9e3e` (Green) | `track-b` |

---

## Execution Strategy

**Parallelism**: Track A and Track B can run concurrently. Track B depends on Track A's stats API changes, but can mock initially.

**Critical Path**:
1. Track A completes stats API change (error_rate) → Track B consumes new field
2. Track A completes chart aggregation endpoint → Track B wires up 12h charts

---

### Track A: Backend Collector Cleanup

**Agent**: Dev (Haiku)
**Estimated Effort**: 1-2 days

#### Context Injection Prompt

```
CONTEXT: Sprint 2.41 - Track A: Backend Collector Cleanup
PROJECT: Oh My Coins - Autonomous Trading Platform
ROLE: Backend Dev

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.41/track-a
  INSTANCE_PORT: 8010
  CONTAINER_PREFIX: track-a
  STRICT_SCOPE: Locked to this directory.

ENVIRONMENT SETUP (MANAGED):
  docker-compose.override.yml maps 8010:80. DB port 5433, Redis 6380.
  Verify: grep COMPOSE_PROJECT_NAME .env

MISSION:
Clean up news collector infrastructure — remove dead collectors, fix metrics, centralise User-Agent.

SPECIFIC OBJECTIVES:

1. REMOVE DEAD COLLECTOR STRATEGY FILES:
   Delete these files from backend/app/collectors/strategies/:
   - news_cryptopanic.py (needs API key we don't have)
   - human_newscatcher.py (needs API key we don't have)
   - glass_nansen.py (needs API key we don't have)
   - human_rss.py (redundant with dedicated news_* collectors)
   - news_beincrypto.py (Cloudflare JS challenge blocks all non-browser requests — 403)

   Also check and remove any test files for these deleted strategies.
   Update __init__.py if it imports any of these.

2. UPDATE initial_data.py SEEDING:
   Remove these entries from the collectors_to_seed list in backend/app/initial_data.py:
   - NansenSmartMoney (glass_nansen)
   - CryptoPanicNews (news_cryptopanic)
   - NewscatcherNews (human_newscatcher)
   - HumanRSSCollector (HumanRSSCollector)
   - BeInCryptoNews (news_beincrypto)

3. CENTRALISE USER-AGENT:
   Create a constant in backend/app/core/config.py or a shared constants file:

   HTTP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"

   Replace all "OhMyCoins/1.0" in remaining collector strategies with this constant:
   - news_coindesk.py
   - news_cointelegraph.py
   - news_cryptoslate.py
   - news_decrypt.py
   - news_newsbtc.py
   - human_reddit.py
   - catalyst_sec.py
   - glass_defillama.py
   - glass_chain_walker.py
   - exchange_coinspot.py (check if it uses a different UA)
   - catalyst_coinspot_announcements.py (already has browser UA — align to constant)

4. FIX STATS METRIC — ERROR RATE:
   In backend/app/api/routes/collectors.py, function get_summary_stats():
   - Replace uptime_pct calculation:
     OLD: uptime_pct = (success_count / total_runs * 100)
     NEW: error_rate = (error_count / total_runs * 100)
   - Rename the field from "uptime_pct" to "error_rate" in the response dict
   - Keep success_count and warning_count in the response for reference

5. ADD 12-HOUR CHART AGGREGATION ENDPOINT:
   In backend/app/api/routes/collectors.py, add a new endpoint or modify the existing
   chart data endpoint to aggregate records_collected into 12-hour buckets:

   GET /api/v1/collectors/stats/chart-data?collector_name=X&hours=168

   Response: [{bucket: "2026-03-07T00:00:00Z", records: 15, runs: 48, errors: 2}, ...]

   Use SQL date_trunc('hour', started_at) grouped into 12h windows.
   Default range: 7 days (168 hours = 14 buckets).

6. UPDATE sample_records.py:
   Remove plugin entries for deleted collectors (news_cryptopanic, human_newscatcher,
   glass_nansen, HumanRSSCollector, news_beincrypto) from PLUGIN_DATA_MAP.

CONSTRAINTS:
  - NO LOCAL VENVS. Test inside Docker: docker compose exec backend bash scripts/test.sh
  - mypy --strict must pass
  - ruff check + ruff format must pass
  - MagicMock (not AsyncMock) for context managers in tests
  - SQLModel: no bidirectional relationships

SUCCESS CRITERIA:
  - [ ] Dead collector strategy files deleted
  - [ ] initial_data.py no longer seeds removed collectors
  - [ ] All remaining collectors use centralised browser UA constant
  - [ ] Stats API returns error_rate instead of uptime_pct
  - [ ] New/modified chart-data endpoint returns 12h aggregated data
  - [ ] All existing tests pass + new tests for changed endpoints
  - [ ] mypy --strict clean, ruff clean

BRANCH: feat/2.41-collector-cleanup
```

#### Deliverables

1. **Deleted files**: 5 strategy files + their tests
2. **Modified files**: initial_data.py, config.py (UA constant), collectors.py (stats+chart), sample_records.py, 6+ strategy files (UA replacement)
3. **Tests**: Updated/new tests for stats endpoint, chart-data endpoint

---

### Track B: Frontend Metrics & Charts

**Agent**: Dev (Haiku)
**Estimated Effort**: 1 day

#### Context Injection Prompt

```
CONTEXT: Sprint 2.41 - Track B: Frontend Metrics & Charts
PROJECT: Oh My Coins - Trading Platform Frontend
ROLE: Frontend Dev

WORKSPACE ANCHOR:
  ROOT_PATH: ../sprint-2.41/track-b
  INSTANCE_PORT: 8020
  CONTAINER_PREFIX: track-b
  STRICT_SCOPE: Locked to this directory.

MISSION:
Update the collector dashboard to show error_rate instead of success_rate, and switch
sparkline charts from per-run to 12-hour aggregated data.

SPECIFIC OBJECTIVES:

1. UPDATE hooks.ts — ERROR RATE:
   In frontend/src/features/admin/hooks.ts, usePluginCardData():
   - Change: success_rate: stats?.uptime_pct ?? null
   - To: error_rate: stats?.error_rate ?? null

   Update the CollectorCardData type accordingly (rename success_rate to error_rate).

2. UPDATE CollectorCard.tsx — DISPLAY ERROR RATE:
   - Change the "Success Rate" label to "Error Rate"
   - Display error_rate with appropriate styling:
     - 0% errors = green (healthy)
     - 1-10% = yellow (warning)
     - >10% = red (problem)
   - Invert the colour logic from success_rate (where high was good)

3. UPDATE CHART DATA SOURCE:
   - Modify the chart data fetching to use the new 12h aggregated endpoint:
     GET /api/v1/collectors/stats/chart-data?collector_name=X&hours=168
   - Update the sparkline to plot records per 12h bucket (14 data points for 7 days)
   - This replaces the current per-run data which produces mostly-zero flat lines

4. REGENERATE OPENAPI CLIENT:
   After Track A's backend changes are merged, regenerate the TypeScript client:
   bash scripts/generate-client.sh
   (Or extract schema from Docker and generate locally per project conventions)

CONSTRAINTS:
  - Use Chakra UI v3 components
  - Use TanStack Query for data fetching
  - Biome for linting/formatting: npm run lint
  - Type check: npm run type-check

SUCCESS CRITERIA:
  - [ ] Collector cards show "Error Rate" with colour-coded display
  - [ ] Sparkline charts show 12h aggregated data (meaningful trends visible)
  - [ ] npm run type-check passes
  - [ ] npm run lint passes
  - [ ] No regressions in collector dashboard functionality

BRANCH: feat/2.41-frontend-metrics
```

#### Deliverables

1. **Modified files**: hooks.ts, CollectorCard.tsx (or equivalent), chart data hook
2. **Generated**: Updated OpenAPI client
3. **Tests**: Type check + lint passing

---

## Documentation Gates

### Gate 1: Requirement Traceability
- [ ] PRs reference Sprint 2.41 objectives
- [ ] Worktree branches verified

### Gate 4: Test Coverage
- [ ] Backend: all tests pass in container
- [ ] Frontend: type-check + lint pass
- [ ] No new mypy errors

---

**Sprint Status**: 🟡 PLANNING
**Created By**: Architect (Opus)
**Approved By**: Pending user review
