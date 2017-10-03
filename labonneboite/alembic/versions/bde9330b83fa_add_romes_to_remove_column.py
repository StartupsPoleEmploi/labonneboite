"""
Add romes_to_remove column

Revision ID: bde9330b83fa
Revises: 1124e80be448
Create Date: 2017-10-03 15:28:07.825231
"""

from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'bde9330b83fa'
down_revision = '1124e80be448'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('etablissements_admin_update', sa.Column('romes_to_remove',
        mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))

def downgrade():
    op.drop_column('etablissements_admin_update', 'romes_to_remove')
