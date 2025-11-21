"""add algorithm and deployed_algorithm tables

Revision ID: 28ac3452fc30
Revises: f9g0h1i2j3k4
Create Date: 2025-11-20 23:11:17.573233

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '28ac3452fc30'
down_revision = 'f9g0h1i2j3k4'
branch_labels = None
depends_on = None


def upgrade():
    # Create algorithms table
    op.create_table('algorithms',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
    sa.Column('algorithm_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('version', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('artifact_id', sa.UUID(), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('configuration_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('default_execution_frequency', sa.Integer(), nullable=False),
    sa.Column('default_position_limit', sa.DECIMAL(precision=20, scale=2), nullable=True),
    sa.Column('performance_metrics_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_by', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['artifact_id'], ['agent_artifacts.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_algorithm_created_by', 'algorithms', ['created_by'], unique=False)
    op.create_index('idx_algorithm_status', 'algorithms', ['status'], unique=False)
    
    # Create deployed_algorithms table
    op.create_table('deployed_algorithms',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('algorithm_id', sa.UUID(), nullable=False),
    sa.Column('deployment_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('execution_frequency', sa.Integer(), nullable=False),
    sa.Column('position_limit', sa.DECIMAL(precision=20, scale=2), nullable=True),
    sa.Column('daily_loss_limit', sa.DECIMAL(precision=20, scale=2), nullable=True),
    sa.Column('parameters_json', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('total_profit_loss', sa.DECIMAL(precision=20, scale=2), nullable=False),
    sa.Column('total_trades', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['algorithm_id'], ['algorithms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_deployed_algorithm_algorithm', 'deployed_algorithms', ['algorithm_id'], unique=False)
    op.create_index('idx_deployed_algorithm_user_active', 'deployed_algorithms', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_deployed_algorithms_algorithm_id'), 'deployed_algorithms', ['algorithm_id'], unique=False)
    op.create_index(op.f('ix_deployed_algorithms_is_active'), 'deployed_algorithms', ['is_active'], unique=False)
    op.create_index(op.f('ix_deployed_algorithms_user_id'), 'deployed_algorithms', ['user_id'], unique=False)


def downgrade():
    # Drop deployed_algorithms table
    op.drop_index(op.f('ix_deployed_algorithms_user_id'), table_name='deployed_algorithms')
    op.drop_index(op.f('ix_deployed_algorithms_is_active'), table_name='deployed_algorithms')
    op.drop_index(op.f('ix_deployed_algorithms_algorithm_id'), table_name='deployed_algorithms')
    op.drop_index('idx_deployed_algorithm_user_active', table_name='deployed_algorithms')
    op.drop_index('idx_deployed_algorithm_algorithm', table_name='deployed_algorithms')
    op.drop_table('deployed_algorithms')
    
    # Drop algorithms table
    op.drop_index('idx_algorithm_status', table_name='algorithms')
    op.drop_index('idx_algorithm_created_by', table_name='algorithms')
    op.drop_table('algorithms')
