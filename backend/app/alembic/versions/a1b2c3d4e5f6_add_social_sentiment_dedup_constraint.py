"""Add social_sentiment dedup unique constraint

Revision ID: a1b2c3d4e5f6
Revises: d939ddf6ef1a
Create Date: 2026-04-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'd939ddf6ef1a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Delete duplicate rows, keeping the one with the lowest id per group
    op.execute("""
        DELETE FROM social_sentiment
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM social_sentiment
            GROUP BY platform, content, posted_at
        )
    """)

    # Step 2: Add unique constraint to prevent future duplicates
    op.create_unique_constraint(
        'uq_social_sentiment_dedup',
        'social_sentiment',
        ['platform', 'content', 'posted_at']
    )


def downgrade() -> None:
    op.drop_constraint('uq_social_sentiment_dedup', 'social_sentiment', type_='unique')
