"""
Add a `reason column` to `etablissements_admin_update`.

Revision ID: 090e86dfc304
Revises: eaba5c094998
Create Date: 2017-08-17 12:15:08.841724
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '090e86dfc304'
down_revision = 'eaba5c094998'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'etablissements_admin_update',
        sa.Column('reason', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False)
    )


def downgrade():
    op.drop_column('etablissements_admin_update', 'reason')
