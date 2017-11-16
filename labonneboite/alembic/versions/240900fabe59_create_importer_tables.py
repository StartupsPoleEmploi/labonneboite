"""
Create main importer tables. Created by @vermeer using `alembic revision --autogenerate`.

Revision ID: 240900fabe59
Revises: bde9330b83fa
Create Date: 2017-11-10 15:25:28.929846
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# works - even if there is a pylint warning which says it does not.
from labonneboite.conf import get_current_env, ENV_LBBDEV

migration_should_run_in_this_environment = get_current_env() != ENV_LBBDEV

# Revision identifiers, used by Alembic.
revision = '240900fabe59'
down_revision = 'bde9330b83fa'
branch_labels = None
depends_on = None


def upgrade():
    if migration_should_run_in_this_environment:
        op.create_table('import_tasks',
        sa.Column('id', mysql.BIGINT(display_width=20), nullable=False),
        sa.Column('filename', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('state', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('import_type', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('created_date', mysql.DATETIME(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate=u'utf8mb4_unicode_ci',
        mysql_default_charset=u'utf8mb4',
        mysql_engine=u'InnoDB'
        )

        op.create_table('dpae_statistics',
        sa.Column('id', mysql.BIGINT(display_width=20), nullable=False),
        sa.Column('last_import', mysql.DATETIME(), nullable=True),
        sa.Column('most_recent_data_date', mysql.DATETIME(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate=u'utf8mb4_unicode_ci',
        mysql_default_charset=u'utf8mb4',
        mysql_engine=u'InnoDB'
        )

        op.create_table('etablissements_raw',
        sa.Column('siret', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('raisonsociale', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('enseigne', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('codenaf', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=8), nullable=False),
        sa.Column('numerorue', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('libellerue', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('codecommune', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('codepostal', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=8), nullable=False),
        sa.Column('email', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('tel', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('departement', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=8), nullable=False),
        sa.Column('trancheeffectif', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=2), nullable=True),
        sa.Column('website1', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('website2', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.PrimaryKeyConstraint('siret'),
        mysql_collate=u'utf8mb4_unicode_ci',
        mysql_default_charset=u'utf8mb4',
        mysql_engine=u'InnoDB'
        )

        op.create_table('etablissements_exportable',
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

        op.create_table('flag_alternance',
        sa.Column('siret', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=False),
        sa.PrimaryKeyConstraint('siret'),
        mysql_collate=u'utf8mb4_unicode_ci',
        mysql_default_charset=u'utf8mb4',
        mysql_engine=u'InnoDB'
        )

        op.create_table('dpae',
        sa.Column('id', mysql.BIGINT(display_width=20), nullable=False),
        sa.Column('siret', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('hiring_date', mysql.DATETIME(), nullable=True),
        sa.Column('zipcode', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=8), nullable=True),
        sa.Column('contract_type', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('departement', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=8), nullable=True),
        sa.Column('contract_duration', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('iiann', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('tranche_age', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('handicap_label', mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate=u'utf8mb4_unicode_ci',
        mysql_default_charset=u'utf8mb4',
        mysql_engine=u'InnoDB'
        )
        # ### end Alembic commands ###

def downgrade():
    if migration_should_run_in_this_environment:
        # ### commands auto generated by Alembic - please adjust! ###
        op.drop_table('dpae')
        op.drop_table('flag_alternance')
        op.drop_table('etablissements_raw')
        op.drop_table('etablissements_exportable')
        op.drop_table('dpae_statistics')
        op.drop_table('import_tasks')
        # ### end Alembic commands ###
