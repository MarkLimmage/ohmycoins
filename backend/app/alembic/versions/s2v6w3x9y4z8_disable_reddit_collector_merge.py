"""disable reddit collector and merge heads

Revision ID: s2v6w3x9y4z8
Revises: l5m6n7o8p9q0, n4k7w2x8y5z1
Create Date: 2026-04-09 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "s2v6w3x9y4z8"
down_revision = ("l5m6n7o8p9q0", "n4k7w2x8y5z1")
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE collector SET is_enabled = false WHERE plugin_name = 'human_reddit'"
    )


def downgrade():
    op.execute(
        "UPDATE collector SET is_enabled = true WHERE plugin_name = 'human_reddit'"
    )
