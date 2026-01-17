"""add user llm credentials and extend agent session for BYOM

Revision ID: a1b2c3d4e5f6
Revises: d1e2f3g4h5i6
Create Date: 2026-01-17 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd1e2f3g4h5i6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_llm_credentials table
    op.create_table(
        'user_llm_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('encrypted_api_key', sa.LargeBinary(), nullable=False),
        sa.Column('encryption_key_id', sa.String(length=50), nullable=True, server_default='default'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for user_llm_credentials
    op.create_index('ix_user_llm_credentials_user_id', 'user_llm_credentials', ['user_id'])
    op.create_index('ix_user_llm_credentials_provider', 'user_llm_credentials', ['provider'])
    op.create_index('ix_user_llm_credentials_is_default', 'user_llm_credentials', ['is_default'])
    op.create_index('ix_user_llm_credentials_is_active', 'user_llm_credentials', ['is_active'])
    
    # Extend agent_sessions table with BYOM fields
    op.add_column('agent_sessions', sa.Column('llm_provider', sa.String(length=20), nullable=True))
    op.add_column('agent_sessions', sa.Column('llm_model', sa.String(length=100), nullable=True))
    op.add_column('agent_sessions', sa.Column('llm_credential_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint for llm_credential_id
    op.create_foreign_key(
        'fk_agent_sessions_llm_credential_id',
        'agent_sessions', 'user_llm_credentials',
        ['llm_credential_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for llm_credential_id
    op.create_index('ix_agent_sessions_llm_credential_id', 'agent_sessions', ['llm_credential_id'])


def downgrade() -> None:
    # Drop foreign key constraint and index from agent_sessions
    op.drop_index('ix_agent_sessions_llm_credential_id', table_name='agent_sessions')
    op.drop_constraint('fk_agent_sessions_llm_credential_id', 'agent_sessions', type_='foreignkey')
    
    # Remove BYOM columns from agent_sessions
    op.drop_column('agent_sessions', 'llm_credential_id')
    op.drop_column('agent_sessions', 'llm_model')
    op.drop_column('agent_sessions', 'llm_provider')
    
    # Drop indexes from user_llm_credentials
    op.drop_index('ix_user_llm_credentials_is_active', table_name='user_llm_credentials')
    op.drop_index('ix_user_llm_credentials_is_default', table_name='user_llm_credentials')
    op.drop_index('ix_user_llm_credentials_provider', table_name='user_llm_credentials')
    op.drop_index('ix_user_llm_credentials_user_id', table_name='user_llm_credentials')
    
    # Drop user_llm_credentials table
    op.drop_table('user_llm_credentials')
