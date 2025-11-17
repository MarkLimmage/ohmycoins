"""add url and collected_at to catalyst_events

Revision ID: e7f8g9h0i1j2
Revises: d1e2f3g4h5i6
Create Date: 2025-11-17 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7f8g9h0i1j2'
down_revision = 'd1e2f3g4h5i6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add url column to catalyst_events
    op.add_column('catalyst_events', sa.Column('url', sa.String(length=500), nullable=True))
    
    # Add collected_at column to catalyst_events
    op.add_column('catalyst_events', sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
    
    # Remove server default after adding the column (it's only needed for existing rows)
    op.alter_column('catalyst_events', 'collected_at', server_default=None)


def downgrade() -> None:
    # Drop columns in reverse order
    op.drop_column('catalyst_events', 'collected_at')
    op.drop_column('catalyst_events', 'url')
