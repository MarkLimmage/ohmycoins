"""merge BYOM and algorithm migrations

Revision ID: 631783b3b17d
Revises: 28ac3452fc30, a1b2c3d4e5f6
Create Date: 2026-01-17 05:22:01.584385

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '631783b3b17d'
down_revision = ('28ac3452fc30', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
