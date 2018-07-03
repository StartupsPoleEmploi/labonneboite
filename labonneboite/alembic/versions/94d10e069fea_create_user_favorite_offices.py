# coding: utf8
"""
Add UserFavoriteOffice table.

Revision ID: 94d10e069fea
Revises: e4bce598b236
Create Date: 2017-05-03 14:26:18.151997
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '94d10e069fea'
down_revision = 'e4bce598b236'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_favorite_offices',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('user_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
        sa.Column('office_siret', mysql.VARCHAR(length=191), nullable=False),
        sa.Column('date_created', mysql.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['office_siret'], ['etablissements.siret'], name='user_favorite_offices_ibfk_2',
            ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_favorite_offices_ibfk_1', ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'office_siret', name='_user_fav_office'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table('user_favorite_offices')
