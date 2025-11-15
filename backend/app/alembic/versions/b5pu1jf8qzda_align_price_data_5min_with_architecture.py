"""Align price_data_5min with architecture spec

Revision ID: b5pu1jf8qzda
Revises: 2a5dad6f1c22
Create Date: 2025-11-15 06:25:30.000000

Changes:
- Change primary key from UUID to BIGSERIAL (auto-incrementing integer) for better time-series performance
- Update DECIMAL precision from (18,8) to (20,8) to match architecture specification
- Add created_at field to track when record was inserted

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b5pu1jf8qzda'
down_revision = '2a5dad6f1c22'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table with the correct schema
    op.create_table('price_data_5min_new',
        sa.Column('id', sa.BigInteger().with_variant(postgresql.BIGINT(), 'postgresql'), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('coin_type', sa.String(length=20), nullable=False),
        sa.Column('bid', sa.DECIMAL(precision=20, scale=8), nullable=True),
        sa.Column('ask', sa.DECIMAL(precision=20, scale=8), nullable=True),
        sa.Column('last', sa.DECIMAL(precision=20, scale=8), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Copy existing data from old table to new table
    op.execute("""
        INSERT INTO price_data_5min_new (coin_type, bid, ask, last, timestamp, created_at)
        SELECT coin_type, bid, ask, last, timestamp, CURRENT_TIMESTAMP
        FROM price_data_5min
        ORDER BY timestamp, coin_type
    """)
    
    # Drop old table
    op.drop_table('price_data_5min')
    
    # Rename new table to original name
    op.rename_table('price_data_5min_new', 'price_data_5min')
    
    # Recreate indexes
    op.create_index('ix_price_data_5min_coin_type', 'price_data_5min', ['coin_type'], unique=False)
    op.create_index('ix_price_data_5min_timestamp', 'price_data_5min', ['timestamp'], unique=False)
    op.create_index('ix_price_data_5min_coin_timestamp', 'price_data_5min', ['coin_type', 'timestamp'], unique=False)
    op.create_index('uq_price_data_5min_coin_timestamp', 'price_data_5min', ['coin_type', 'timestamp'], unique=True)


def downgrade():
    # Create old table with UUID schema
    op.create_table('price_data_5min_old',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('coin_type', sa.String(length=20), nullable=False),
        sa.Column('bid', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('ask', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('last', sa.DECIMAL(precision=18, scale=8), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back (note: this will lose the auto-incrementing IDs and created_at)
    op.execute("""
        INSERT INTO price_data_5min_old (id, coin_type, bid, ask, last, timestamp)
        SELECT gen_random_uuid(), coin_type, bid, ask, last, timestamp
        FROM price_data_5min
    """)
    
    # Drop new table
    op.drop_table('price_data_5min')
    
    # Rename old table back
    op.rename_table('price_data_5min_old', 'price_data_5min')
    
    # Recreate old indexes
    op.create_index('ix_price_data_5min_coin_type', 'price_data_5min', ['coin_type'], unique=False)
    op.create_index('ix_price_data_5min_timestamp', 'price_data_5min', ['timestamp'], unique=False)
    op.create_index('ix_price_data_5min_coin_timestamp', 'price_data_5min', ['coin_type', 'timestamp'], unique=False)
    op.create_index('uq_price_data_5min_coin_timestamp', 'price_data_5min', ['coin_type', 'timestamp'], unique=True)
