"""
add social network link in office

Revision ID: 2aca2291700f
Revises: 80194630f4fe
Create Date: 2018-06-18 16:28:57.263048
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '2aca2291700f'
down_revision = '80194630f4fe'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('etablissements_admin_update',
        sa.Column('social_network', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements_admin_add',
        sa.Column('social_network', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements_exportable',
        sa.Column('social_network', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements_raw',
        sa.Column('social_network', mysql.TINYTEXT(), nullable=True))

    op.add_column('etablissements',
        sa.Column('social_network', mysql.TINYTEXT(), nullable=True))


def downgrade():
    op.drop_column('etablissements_admin_update', 'social_network')
    op.drop_column('etablissements_admin_add', 'social_network')
    op.drop_column('etablissements_exportable', 'social_network')
    op.drop_column('etablissements_raw', 'social_network')
    op.drop_column('etablissements', 'social_network')
