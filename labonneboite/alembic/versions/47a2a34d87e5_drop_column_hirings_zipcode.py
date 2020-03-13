"""
drop column hirings.zipcode

Revision ID: 47a2a34d87e5
Revises: 5d43d4cf1847
Create Date: 2018-03-20 09:45:56.347451
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "47a2a34d87e5"
down_revision = "5d43d4cf1847"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("hirings", "zipcode")


def downgrade():
    op.add_column(
        "hirings", sa.Column("zipcode", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=8), nullable=False)
    )
