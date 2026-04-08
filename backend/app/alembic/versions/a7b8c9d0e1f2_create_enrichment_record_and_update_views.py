"""Create enrichment_record table and update materialized views

Revision ID: a7b8c9d0e1f2
Revises: f4e3d2c1b0a9
Create Date: 2026-04-09 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.enrichment.views import MV_COIN_SENTIMENT_24H_SQL, MV_SIGNAL_SUMMARY_SQL

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f4e3d2c1b0a9'
branch_labels = ('graph_enrichment',)
depends_on = None


def upgrade() -> None:
    # Create enrichment_record table
    op.create_table(
        'enrichment_record',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_table', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('enricher_name', sa.String(length=50), nullable=False),
        sa.Column('enrichment_type', sa.String(length=50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('currencies', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('enriched_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'source_table', 'source_id', 'enricher_name', 'enrichment_type',
            name='uq_enrichment_record_source'
        ),
    )
    op.create_index(
        'ix_enrichment_record_enricher_name',
        'enrichment_record',
        ['enricher_name'],
    )

    # Recreate materialized views with social sentiment UNION
    # Drop and recreate to update the SQL definition
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_coin_sentiment_24h CASCADE")
    op.execute(
        f"CREATE MATERIALIZED VIEW mv_coin_sentiment_24h AS {MV_COIN_SENTIMENT_24H_SQL}"
    )
    op.execute(
        "CREATE UNIQUE INDEX ON mv_coin_sentiment_24h (coin, enrichment_type)"
    )

    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_signal_summary CASCADE")
    op.execute(
        f"CREATE MATERIALIZED VIEW mv_signal_summary AS {MV_SIGNAL_SUMMARY_SQL}"
    )
    op.execute(
        "CREATE UNIQUE INDEX ON mv_signal_summary (coin, enricher_name, enrichment_type, hour_bucket)"
    )


def downgrade() -> None:
    # Restore original materialized views (news_enrichment only)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_signal_summary CASCADE")
    op.execute("""
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
        GROUP BY unnest(ne.currencies), ne.enricher_name, ne.enrichment_type, date_trunc('hour', ne.enriched_at)
    """)
    op.execute(
        "CREATE UNIQUE INDEX ON mv_signal_summary (coin, enricher_name, enrichment_type, hour_bucket)"
    )

    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_coin_sentiment_24h CASCADE")
    op.execute("""
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
        GROUP BY unnest(ne.currencies), ne.enrichment_type
    """)
    op.execute(
        "CREATE UNIQUE INDEX ON mv_coin_sentiment_24h (coin, enrichment_type)"
    )

    # Drop enrichment_record table
    op.drop_index('ix_enrichment_record_enricher_name', table_name='enrichment_record')
    op.drop_table('enrichment_record')
