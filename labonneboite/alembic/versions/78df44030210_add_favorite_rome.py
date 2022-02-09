"""
add favorite rome

Revision ID: 78df44030210
Revises: 29cdae903fb3
Create Date: 2022-02-03 14:11:43.111858
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = '78df44030210'
down_revision = '29cdae903fb3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_favorite_offices',
                  sa.Column('rome_code', sa.String(length=5), nullable=True))


def downgrade():
    op.drop_column('user_favorite_offices', 'rome_code')
