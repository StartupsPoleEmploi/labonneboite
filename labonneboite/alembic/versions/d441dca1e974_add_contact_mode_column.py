"""
Add contact_mode column

Revision ID: d441dca1e974
Revises: 4041eac5f52f
Create Date: 2018-06-04 14:22:49.829461
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'd441dca1e974'
down_revision = '4041eac5f52f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('etablissements_admin_update',
        sa.Column('contact_mode', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements_admin_add',
        sa.Column('contact_mode', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements_exportable',
        sa.Column('contact_mode', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements_raw',
        sa.Column('contact_mode', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements',
        sa.Column('contact_mode', mysql.TINYTEXT(), nullable=True))


def downgrade():
    op.drop_column('etablissements_admin_update', 'contact_mode')
    op.drop_column('etablissements_admin_add', 'contact_mode')
    op.drop_column('etablissements_exportable', 'contact_mode')
    op.drop_column('etablissements_raw', 'contact_mode')
    op.drop_column('etablissements', 'contact_mode')
