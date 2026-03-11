# Implementation Brief: Database-Native Feature Store (Phase 2.5)

The "Vibe Coder" Handover Pack

## Goal
Implement a Feature Store using Postgres Materialized Views to shift expensive window functions and joins from Python/Pandas to the database engine.

## The Schema (SQL)

### 1. `mv_coin_targets_5min` (The Target Variable)
*   Objective: Pre-calculate *future* returns (1h, 24h) and *past* volatility without look-ahead bias.
*   **Key**: `timestamp`

```sql
CREATE MATERIALIZED VIEW mv_coin_targets_5min AS
SELECT
    timestamp,
    coin_type,
    last as price_close,
    -- Target: Price change in next 1 hour (12 periods of 5 mins)
    (LEAD(last, 12) OVER (PARTITION BY coin_type ORDER BY timestamp) - last) / last as target_return_1h,
    -- Target: Price change in next 24 hours (288 periods)
    (LEAD(last, 288) OVER (PARTITION BY coin_type ORDER BY timestamp) - last) / last as target_return_24h,
    -- Feature: Volatility (Std Dev of returns over last 24h)
    STDDEV(last) OVER (PARTITION BY coin_type ORDER BY timestamp ROWS BETWEEN 288 PRECEDING AND CURRENT ROW) as volatility_24h
FROM price_data_5min;

CREATE UNIQUE INDEX idx_mv_targets_coin_time ON mv_coin_targets_5min(coin_type, timestamp);
```

### 2. `mv_sentiment_signals_1h` (Signal Alignment)
*   Objective: Aggregate high-frequency sentiment data into hourly buckets.
*   **Key**: `hour_bucket`, `coin_type`

```sql
CREATE MATERIALIZED VIEW mv_sentiment_signals_1h AS
SELECT
    date_trunc('hour', published_at) as hour_bucket,
    unnest(currencies) as coin_type,
    COUNT(*) as news_volume,
    AVG(sentiment_score) as avg_sentiment_score,
    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as bullish_count,
    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as bearish_count
FROM news_sentiment
WHERE currencies IS NOT NULL
GROUP BY 1, 2;

CREATE UNIQUE INDEX idx_mv_sentiment_coin_hour ON mv_sentiment_signals_1h(coin_type, hour_bucket);
```

### 3. `mv_catalyst_impact_decay` (Event Weighting)
*   Objective: Calculate exponential decay impact from heavy events (SEC filings, etc.).
*   **Key**: `timestamp`, `coin_type`

```sql
CREATE MATERIALIZED VIEW mv_catalyst_impact_decay AS
SELECT 
    p.timestamp,
    p.coin_type,
    MAX(c.impact_score * exp(-0.1 * extract(epoch from (p.timestamp - c.detected_at))/3600)) as active_catalyst_score
FROM price_data_5min p
JOIN catalyst_events c ON p.coin_type = any(c.currencies)
WHERE p.timestamp >= c.detected_at 
  AND p.timestamp <= c.detected_at + interval '48 hours'
GROUP BY 1, 2;

CREATE UNIQUE INDEX idx_mv_catalyst_decay_coin_time ON mv_catalyst_impact_decay(coin_type, timestamp);
```

### 4. `mv_training_set_v1` (The Feature Store)
*   Objective: Unified training dataset.
*   **Feature Engineering**: Strict lag (T-1h) for sentiment joining to prevent look-ahead bias.

```sql
CREATE MATERIALIZED VIEW mv_training_set_v1 AS
SELECT
    t.timestamp,
    t.coin_type,
    -- Targets
    t.target_return_1h,
    t.target_return_24h,
    -- Price Features
    t.volatility_24h,
    -- Sentiment Features (joined on hourly bucket - 1 HOUR LAG)
    COALESCE(s.avg_sentiment_score, 0) as sentiment_1h_lag,
    COALESCE(s.news_volume, 0) as news_vol_1h_lag,
    -- Catalyst Features (joined on daily/decay logic)
    COALESCE(c.active_catalyst_score, 0) as catalyst_score_decay
FROM mv_coin_targets_5min t
LEFT JOIN mv_sentiment_signals_1h s 
    ON t.coin_type = s.coin_type 
    AND date_trunc('hour', t.timestamp) = (s.hour_bucket + interval '1 hour') -- Strict 1h lag
LEFT JOIN mv_catalyst_impact_decay c
    ON t.coin_type = c.coin_type 
    AND t.timestamp = c.timestamp
-- Filter for training (where target is known)
WHERE t.target_return_1h IS NOT NULL;

CREATE UNIQUE INDEX idx_mv_training_set_coin_time ON mv_training_set_v1(coin_type, timestamp);
```

## Integration Path (Alembic)
1.  Use Alembic to generate a revision.
2.  Add the Raw SQL strings to `upgrade()`.
3.  Add `DROP MATERIALIZED VIEW` statements to `downgrade()`.

## Safety Checklist
-   [ ] **Look-Ahead Bias:** Strict T-1h Lag verified in `mv_training_set_v1`.
-   [ ] **Concurrency:** Unique indexes present for `REFRESH CONCURRENTLY`.
-   [ ] **Decay:** Exponential constant set to `-0.1`.
