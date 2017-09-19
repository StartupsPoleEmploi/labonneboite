"""
Add `romes_to_boost` column to `OfficeAdminUpdate`.

Revision ID: 1124e80be448
Revises: f03cff523555
Create Date: 2017-09-19 09:25:28.681977
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '1124e80be448'
down_revision = 'f03cff523555'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'etablissements_admin_update',
        sa.Column('romes_to_boost', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False)
    )


def downgrade():
    op.drop_column('etablissements_admin_update', 'romes_to_boost')
