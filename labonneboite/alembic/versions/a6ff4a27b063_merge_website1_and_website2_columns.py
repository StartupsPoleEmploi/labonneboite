"""
merge website1 and website2 columns

Revision ID: a6ff4a27b063
Revises: 91ee6fb3e7fd
Create Date: 2018-09-13 14:35:05.886339
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'a6ff4a27b063'
down_revision = '91ee6fb3e7fd'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('etablissements_raw', 'website1')
    op.drop_column('etablissements_raw', 'website2')
    op.add_column('etablissements_raw',
        sa.Column(
            'website',
            mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191),
            nullable=True
        )
    )


def downgrade():
    op.drop_column('etablissements_raw', 'website')
    op.add_column('etablissements_raw',
        sa.Column(
            'website1',
            mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191),
            nullable=True
        )
    )
    op.add_column('etablissements_raw',
        sa.Column(
            'website2',
            mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191),
            nullable=True
        )
    )
