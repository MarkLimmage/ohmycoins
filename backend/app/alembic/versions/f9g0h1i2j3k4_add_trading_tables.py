"""add trading tables for positions and orders

Revision ID: f9g0h1i2j3k4
Revises: e7f8g9h0i1j2
Create Date: 2025-11-20 10:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f9g0h1i2j3k4'
down_revision = 'e7f8g9h0i1j2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('coin_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.DECIMAL(precision=20, scale=10), nullable=False),
        sa.Column('average_price', sa.DECIMAL(precision=20, scale=8), nullable=False),
        sa.Column('total_cost', sa.DECIMAL(precision=20, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for positions
    op.create_index('idx_position_user_coin', 'positions', ['user_id', 'coin_type'], unique=True)
    op.create_index(op.f('ix_positions_user_id'), 'positions', ['user_id'], unique=False)
    op.create_index(op.f('ix_positions_coin_type'), 'positions', ['coin_type'], unique=False)
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('algorithm_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('coin_type', sa.String(length=20), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('order_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.DECIMAL(precision=20, scale=10), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=20, scale=8), nullable=True),
        sa.Column('filled_quantity', sa.DECIMAL(precision=20, scale=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('coinspot_order_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('filled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for orders
    op.create_index('idx_order_user_status', 'orders', ['user_id', 'status'], unique=False)
    op.create_index('idx_order_created', 'orders', ['created_at'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_index(op.f('ix_orders_algorithm_id'), 'orders', ['algorithm_id'], unique=False)
    op.create_index(op.f('ix_orders_coin_type'), 'orders', ['coin_type'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_coinspot_order_id'), 'orders', ['coinspot_order_id'], unique=False)


def downgrade() -> None:
    # Drop orders table and indexes
    op.drop_index(op.f('ix_orders_coinspot_order_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_coin_type'), table_name='orders')
    op.drop_index(op.f('ix_orders_algorithm_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_user_id'), table_name='orders')
    op.drop_index('idx_order_created', table_name='orders')
    op.drop_index('idx_order_user_status', table_name='orders')
    op.drop_table('orders')
    
    # Drop positions table and indexes
    op.drop_index(op.f('ix_positions_coin_type'), table_name='positions')
    op.drop_index(op.f('ix_positions_user_id'), table_name='positions')
    op.drop_index('idx_position_user_coin', table_name='positions')
    op.drop_table('positions')
