"""Add partial unique index on user_llm_credentials (user_id, provider, model_name) where is_active

Revision ID: n4k7w2x8y5z1
Revises: m8s6e4p2r0q1
Create Date: 2026-04-09 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "n4k7w2x8y5z1"
down_revision = "m8s6e4p2r0q1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Partial unique index: one active credential per (user, provider, model_name).
    # COALESCE handles NULL model_name by treating it as '' for uniqueness purposes.
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX ix_uq_active_credential_per_model
            ON user_llm_credentials (user_id, provider, COALESCE(model_name, ''))
            WHERE is_active = true
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DROP INDEX IF EXISTS ix_uq_active_credential_per_model")
    )
