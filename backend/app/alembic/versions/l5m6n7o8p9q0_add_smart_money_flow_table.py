"""add smart money flow table

Revision ID: l5m6n7o8p9q0
Revises: 631783b3b17d
Create Date: 2026-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'l5m6n7o8p9q0'
down_revision = '631783b3b17d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create smart_money_flow table (Glass Ledger - Nansen)
    op.create_table(
        'smart_money_flow',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=20), nullable=False),
        sa.Column('net_flow_usd', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('buying_wallet_count', sa.Integer(), nullable=False),
        sa.Column('selling_wallet_count', sa.Integer(), nullable=False),
        sa.Column('buying_wallets', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('selling_wallets', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_smart_money_flow_token', 'smart_money_flow', ['token'])
    op.create_index('ix_smart_money_flow_collected_at', 'smart_money_flow', ['collected_at'])
    op.create_index(
        'ix_smart_money_flow_token_time',
        'smart_money_flow',
        ['token', 'collected_at']
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_smart_money_flow_token_time', table_name='smart_money_flow')
    op.drop_index('ix_smart_money_flow_collected_at', table_name='smart_money_flow')
    op.drop_index('ix_smart_money_flow_token', table_name='smart_money_flow')
    
    # Drop table
    op.drop_table('smart_money_flow')
