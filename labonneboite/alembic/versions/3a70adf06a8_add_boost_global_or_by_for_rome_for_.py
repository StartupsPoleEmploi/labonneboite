"""
add boost global or by for rome for alternance

Revision ID: 3a70adf06a8
Revises: a3c7706b467b
Create Date: 2018-05-04 11:12:51.494739
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '3a70adf06a8'
down_revision = 'a3c7706b467b'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('etablissements_admin_update', sa.Column('romes_alternance_to_boost',
        mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))
    op.add_column('etablissements_admin_update', sa.Column('boost_alternance', mysql.TINYINT(display_width=1),
        server_default=sa.text(u"'0'"), autoincrement=False, nullable=False))
    op.add_column('etablissements_admin_update', sa.Column('romes_alternance_to_remove',
        mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))

def downgrade():
    op.drop_column('etablissements_admin_update', 'romes_alternance_to_boost')
    op.drop_column('etablissements_admin_update', 'boost_alternance')
    op.drop_column('etablissements_admin_update', 'romes_alternance_to_remove')

