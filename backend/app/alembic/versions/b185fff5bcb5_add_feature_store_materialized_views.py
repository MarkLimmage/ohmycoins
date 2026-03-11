"""add feature store materialized views

Revision ID: b185fff5bcb5
Revises: 03022c68d6fc
Create Date: 2026-03-11 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b185fff5bcb5'
down_revision = '03022c68d6fc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. mv_coin_targets_5min — future returns + volatility
    op.execute("""
        CREATE MATERIALIZED VIEW mv_coin_targets_5min AS
        SELECT
            timestamp,
            coin_type,
            last as price_close,
            (LEAD(last, 12) OVER (PARTITION BY coin_type ORDER BY timestamp) - last) / NULLIF(last, 0) as target_return_1h,
            (LEAD(last, 288) OVER (PARTITION BY coin_type ORDER BY timestamp) - last) / NULLIF(last, 0) as target_return_24h,
            STDDEV(last) OVER (PARTITION BY coin_type ORDER BY timestamp ROWS BETWEEN 288 PRECEDING AND CURRENT ROW) as volatility_24h
        FROM price_data_5min
    """)
    op.execute("CREATE UNIQUE INDEX idx_mv_targets_coin_time ON mv_coin_targets_5min(coin_type, timestamp)")

    # 2. mv_sentiment_signals_1h — hourly sentiment aggregation
    op.execute("""
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
        GROUP BY 1, 2
    """)
    op.execute("CREATE UNIQUE INDEX idx_mv_sentiment_coin_hour ON mv_sentiment_signals_1h(coin_type, hour_bucket)")

    # 3. mv_catalyst_impact_decay — exponential decay
    op.execute("""
        CREATE MATERIALIZED VIEW mv_catalyst_impact_decay AS
        SELECT
            p.timestamp,
            p.coin_type,
            MAX(c.impact_score * exp(-0.1 * extract(epoch from (p.timestamp - c.detected_at))/3600)) as active_catalyst_score
        FROM price_data_5min p
        JOIN catalyst_events c ON p.coin_type = any(c.currencies)
        WHERE p.timestamp >= c.detected_at
          AND p.timestamp <= c.detected_at + interval '48 hours'
        GROUP BY 1, 2
    """)
    op.execute("CREATE UNIQUE INDEX idx_mv_catalyst_decay_coin_time ON mv_catalyst_impact_decay(coin_type, timestamp)")

    # 4. mv_training_set_v1 — unified training dataset
    op.execute("""
        CREATE MATERIALIZED VIEW mv_training_set_v1 AS
        SELECT
            t.timestamp,
            t.coin_type,
            t.target_return_1h,
            t.target_return_24h,
            t.volatility_24h,
            COALESCE(s.avg_sentiment_score, 0) as sentiment_1h_lag,
            COALESCE(s.news_volume, 0) as news_vol_1h_lag,
            COALESCE(c.active_catalyst_score, 0) as catalyst_score_decay
        FROM mv_coin_targets_5min t
        LEFT JOIN mv_sentiment_signals_1h s
            ON t.coin_type = s.coin_type
            AND date_trunc('hour', t.timestamp) = (s.hour_bucket + interval '1 hour')
        LEFT JOIN mv_catalyst_impact_decay c
            ON t.coin_type = c.coin_type
            AND t.timestamp = c.timestamp
        WHERE t.target_return_1h IS NOT NULL
    """)
    op.execute("CREATE UNIQUE INDEX idx_mv_training_set_coin_time ON mv_training_set_v1(coin_type, timestamp)")


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_training_set_v1 CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_catalyst_impact_decay CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_sentiment_signals_1h CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_coin_targets_5min CASCADE")
