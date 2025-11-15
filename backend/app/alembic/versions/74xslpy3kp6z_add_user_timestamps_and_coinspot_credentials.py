"""Add User timestamps and Coinspot credentials table

Revision ID: 74xslpy3kp6z
Revises: b5pu1jf8qzda
Create Date: 2025-11-15 06:35:00.000000

Phase 2: User Authentication & API Credential Management

Changes:
- Add created_at and updated_at timestamps to User table
- Create coinspot_credentials table with encrypted credential storage
- Add relationship between User and CoinspotCredentials

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '74xslpy3kp6z'
down_revision = 'b5pu1jf8qzda'
branch_labels = None
depends_on = None


def upgrade():
    # Add timestamps to user table
    op.add_column('user', 
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.add_column('user', 
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create coinspot_credentials table
    op.create_table('coinspot_credentials',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('api_key_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('api_secret_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create index on user_id for efficient lookups
    op.create_index('idx_coinspot_credentials_user_id', 'coinspot_credentials', ['user_id'], unique=False)


def downgrade():
    # Drop coinspot_credentials table
    op.drop_index('idx_coinspot_credentials_user_id', table_name='coinspot_credentials')
    op.drop_table('coinspot_credentials')
    
    # Remove timestamps from user table
    op.drop_column('user', 'updated_at')
    op.drop_column('user', 'created_at')
