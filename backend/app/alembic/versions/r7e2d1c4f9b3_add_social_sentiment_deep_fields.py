"""Add body, comment_count, top_comments to social_sentiment

Revision ID: r7e2d1c4f9b3
Revises: f4e3d2c1b0a9
Create Date: 2026-04-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "r7e2d1c4f9b3"
down_revision = "f4e3d2c1b0a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("social_sentiment", sa.Column("body", sa.Text(), nullable=True))
    op.add_column(
        "social_sentiment", sa.Column("comment_count", sa.Integer(), nullable=True)
    )
    op.add_column(
        "social_sentiment", sa.Column("top_comments", postgresql.JSONB(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("social_sentiment", "top_comments")
    op.drop_column("social_sentiment", "comment_count")
    op.drop_column("social_sentiment", "body")
