"""
add date_insertion

Revision ID: f628f8fac32d
Revises: a4b5f5f737ea
Create Date: 2021-01-08 17:17:49.430997
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'f628f8fac32d'
down_revision = 'a4b5f5f737ea'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('hirings', sa.Column('date_insertion', mysql.DATETIME(), nullable=True))


def downgrade():
    op.drop_column('hirings', 'date_insertion')
