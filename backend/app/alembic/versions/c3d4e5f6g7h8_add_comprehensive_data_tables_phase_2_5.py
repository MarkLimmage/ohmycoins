"""add comprehensive data tables phase 2.5

Revision ID: c3d4e5f6g7h8
Revises: b5pu1jf8qzda
Create Date: 2025-11-16 03:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b5pu1jf8qzda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create protocol_fundamentals table (Glass Ledger)
    op.create_table(
        'protocol_fundamentals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(length=50), nullable=False),
        sa.Column('tvl_usd', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('fees_24h', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('revenue_24h', sa.DECIMAL(precision=20, scale=2), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_protocol_fundamentals_protocol', 'protocol_fundamentals', ['protocol'])
    op.create_index('ix_protocol_fundamentals_collected_at', 'protocol_fundamentals', ['collected_at'])
    op.create_index(
        'uq_protocol_fundamentals_protocol_date',
        'protocol_fundamentals',
        ['protocol', sa.text("DATE(collected_at)")],
        unique=True
    )

    # Create on_chain_metrics table (Glass Ledger)
    op.create_table(
        'on_chain_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset', sa.String(length=10), nullable=False),
        sa.Column('metric_name', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.DECIMAL(precision=30, scale=8), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_on_chain_metrics_asset', 'on_chain_metrics', ['asset'])
    op.create_index('ix_on_chain_metrics_metric_name', 'on_chain_metrics', ['metric_name'])
    op.create_index('ix_on_chain_metrics_collected_at', 'on_chain_metrics', ['collected_at'])
    op.create_index(
        'ix_on_chain_metrics_asset_metric_time',
        'on_chain_metrics',
        ['asset', 'metric_name', 'collected_at']
    )

    # Create news_sentiment table (Human Ledger)
    op.create_table(
        'news_sentiment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('sentiment_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('currencies', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    op.create_index('ix_news_sentiment_collected_at', 'news_sentiment', ['collected_at'])
    op.create_index('ix_news_sentiment_published_at', 'news_sentiment', ['published_at'])

    # Create social_sentiment table (Human Ledger)
    op.create_table(
        'social_sentiment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('currencies', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_social_sentiment_platform', 'social_sentiment', ['platform'])
    op.create_index('ix_social_sentiment_collected_at', 'social_sentiment', ['collected_at'])
    op.create_index(
        'ix_social_sentiment_platform_posted',
        'social_sentiment',
        ['platform', 'posted_at']
    )

    # Create catalyst_events table (Catalyst Ledger)
    op.create_table(
        'catalyst_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('currencies', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('impact_score', sa.Integer(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('impact_score >= 1 AND impact_score <= 10'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_catalyst_events_event_type', 'catalyst_events', ['event_type'])
    op.create_index('ix_catalyst_events_detected_at', 'catalyst_events', ['detected_at'])
    op.create_index(
        'ix_catalyst_events_type_detected',
        'catalyst_events',
        ['event_type', 'detected_at']
    )

    # Create collector_runs table (Collector Metadata)
    op.create_table(
        'collector_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('collector_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('records_collected', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collector_runs_collector_name', 'collector_runs', ['collector_name'])
    op.create_index('ix_collector_runs_status', 'collector_runs', ['status'])
    op.create_index(
        'ix_collector_runs_name_started',
        'collector_runs',
        ['collector_name', 'started_at']
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('collector_runs')
    op.drop_table('catalyst_events')
    op.drop_table('social_sentiment')
    op.drop_table('news_sentiment')
    op.drop_table('on_chain_metrics')
    op.drop_table('protocol_fundamentals')
