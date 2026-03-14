"""add mv_ohlcv_1m view

Revision ID: c2a4b6c8d0e2
Revises: b185fff5bcb5
Create Date: 2026-03-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = 'c2a4b6c8d0e2'
down_revision = 'b185fff5bcb5'
branch_labels = None
depends_on = None


def upgrade():
    # Create mv_ohlcv_1m which aggregates price_data_5min into 1-minute bars
    # Note: Since source is 5-min snapshots, this view effectively just formalizes the data structure
    # for the Lab pipeline, even if the resolution is strictly 5-min.
    # However, to be safe and future-proof for high-frequency collectors, we define it as:
    
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ohlcv_1m CASCADE")
    op.execute("""
        CREATE MATERIALIZED VIEW mv_ohlcv_1m AS
        SELECT
            date_trunc('minute', timestamp) AS timestamp,
            coin_type,
            (array_agg(last ORDER BY timestamp ASC))[1] AS open,
            MAX(last) AS high,
            MIN(last) AS low,
            (array_agg(last ORDER BY timestamp DESC))[1] AS close,
            SUM(1) AS volume -- Placeholder since we don't have true volume in snapshots
        FROM price_data_5min
        GROUP BY 1, 2
    """)
    
    # Create index for performance
    op.execute("CREATE UNIQUE INDEX idx_mv_ohlcv_1m_coin_time ON mv_ohlcv_1m(coin_type, timestamp)")


def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ohlcv_1m CASCADE")
