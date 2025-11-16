"""add_agent_session_tables

Revision ID: c0e0bdfc3471
Revises: 8abf25dd5d93
Create Date: 2025-11-16 03:25:51.260318

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c0e0bdfc3471'
down_revision = '8abf25dd5d93'
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_sessions table
    op.create_table(
        'agent_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_goal', sa.String(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('result_summary', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_sessions_user_id'), 'agent_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_sessions_status'), 'agent_sessions', ['status'], unique=False)
    op.create_index(op.f('ix_agent_sessions_created_at'), 'agent_sessions', ['created_at'], unique=False)

    # Create agent_session_messages table
    op.create_table(
        'agent_session_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=True),
        sa.Column('metadata_json', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_session_messages_session_id'), 'agent_session_messages', ['session_id'], unique=False)
    op.create_index(op.f('ix_agent_session_messages_created_at'), 'agent_session_messages', ['created_at'], unique=False)

    # Create agent_artifacts table
    op.create_table(
        'agent_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artifact_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_artifacts_session_id'), 'agent_artifacts', ['session_id'], unique=False)
    op.create_index(op.f('ix_agent_artifacts_artifact_type'), 'agent_artifacts', ['artifact_type'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_agent_artifacts_artifact_type'), table_name='agent_artifacts')
    op.drop_index(op.f('ix_agent_artifacts_session_id'), table_name='agent_artifacts')
    op.drop_table('agent_artifacts')
    
    op.drop_index(op.f('ix_agent_session_messages_created_at'), table_name='agent_session_messages')
    op.drop_index(op.f('ix_agent_session_messages_session_id'), table_name='agent_session_messages')
    op.drop_table('agent_session_messages')
    
    op.drop_index(op.f('ix_agent_sessions_created_at'), table_name='agent_sessions')
    op.drop_index(op.f('ix_agent_sessions_status'), table_name='agent_sessions')
    op.drop_index(op.f('ix_agent_sessions_user_id'), table_name='agent_sessions')
    op.drop_table('agent_sessions')

