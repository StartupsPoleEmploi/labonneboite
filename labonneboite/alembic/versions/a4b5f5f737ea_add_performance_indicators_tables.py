"""
Add performance indicators tables

Revision ID: a4b5f5f737ea
Revises: 7c0cd2948e3d
Create Date: 2020-09-28 17:56:09.835806
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'a4b5f5f737ea'
down_revision = 'e9b4b34e5163'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'perf_importer_cycle_infos',
        sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
        sa.Column('execution_date', mysql.DATETIME(), nullable=True),
        sa.Column('prediction_start_date', mysql.DATETIME(), nullable=True),
        sa.Column('prediction_end_date', mysql.DATETIME(), nullable=True),
        sa.Column('file_name', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('computed', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        sa.Column('on_google_sheets', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )
    op.create_table(
        'perf_division_per_rome',
        sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
        sa.Column('importer_cycle_infos_id', mysql.BIGINT(display_width=20), autoincrement=False, nullable=True),
        sa.Column('codenaf', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=8), nullable=False),
        sa.Column('coderome', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=8), nullable=False),
        sa.Column('threshold_lbb', mysql.FLOAT(), nullable=True),
        sa.Column('threshold_lba', mysql.FLOAT(), nullable=True),
        sa.Column('nb_bonne_boites_lbb', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('nb_bonne_boites_lba', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['importer_cycle_infos_id'], ['perf_importer_cycle_infos.id'], name='perf_division_per_rome_ibfk_1', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )
    op.create_table(
        'perf_prediction_and_effective_hirings',
        sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
        sa.Column('importer_cycle_infos_id', mysql.BIGINT(display_width=20), autoincrement=False, nullable=True),
        sa.Column('siret', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('codenaf', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=8), nullable=True),
        sa.Column('codecommune', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('codepostal', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=8), nullable=True),
        sa.Column('departement', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=8), nullable=True),
        sa.Column('raisonsociale', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('enseigne', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=True),
        sa.Column('lbb_nb_predicted_hirings', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('lba_nb_predicted_hirings', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('lbb_nb_predicted_hirings_score', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('lba_nb_predicted_hirings_score', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('lbb_nb_effective_hirings', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('lba_nb_effective_hirings', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('is_a_bonne_boite', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        sa.Column('is_a_bonne_alternance', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['importer_cycle_infos_id'], ['perf_importer_cycle_infos.id'], name='perf_prediction_and_effective_hirings_ibfk_1', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table('perf_prediction_and_effective_hirings')
    op.drop_table('perf_division_per_rome')
    op.drop_table('perf_importer_cycle_infos')
