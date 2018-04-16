"""
initial migration create etablissements

Revision ID: d0c07945abc1
Revises: None
Create Date: 2018-04-16 17:45:37.243833
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'd0c07945abc1'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('etablissements',
        sa.Column('siret', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('raisonsociale', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('enseigne', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('codenaf', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('trancheeffectif', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('numerorue', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('libellerue', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('codepostal', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=11), nullable=True),
        sa.Column('tel', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('email', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('website', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('flag_alternance', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('flag_junior', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('flag_senior', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('flag_handicap', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('has_multi_geolocations', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('codecommune', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('coordinates_x', mysql.FLOAT(), nullable=True),
        sa.Column('coordinates_y', mysql.FLOAT(), nullable=True),
        sa.Column('departement', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=11), nullable=True),
        sa.Column('score', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('siret'),
        mysql_collate=u'utf8mb4_unicode_ci',
        mysql_default_charset=u'utf8mb4',
        mysql_engine=u'InnoDB'
    )


def downgrade():
    op.drop_table('etablissements')
