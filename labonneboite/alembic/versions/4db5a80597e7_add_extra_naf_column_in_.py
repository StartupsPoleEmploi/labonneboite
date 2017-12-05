"""
add extra_naf column in adminOfficeUpdate

Revision ID: 4db5a80597e7
Revises: c9f0246b91ef
Create Date: 2017-12-04 13:49:36.321269
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '4db5a80597e7'
down_revision = 'c9f0246b91ef'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('etablissements_admin_update', sa.Column('nafs_to_add', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))


def downgrade():
    op.drop_column('etablissements_admin_update', 'nafs_to_add')
