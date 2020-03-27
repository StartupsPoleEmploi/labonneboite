"""
Add impact retour emploi tables

Revision ID: ccc88fc92e0f
Revises: c4c5f7a025c4
Create Date: 2020-03-27 15:10:43.410139
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'ccc88fc92e0f'
down_revision = 'c4c5f7a025c4'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'logs_idpe_connect',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('idutilisateur_peconnect', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('dateheure', mysql.DATETIME()),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    op.create_table(
        'logs_activity',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('dateheure', mysql.DATETIME()),
        sa.Column('nom', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('idutilisateur_peconnect', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('siret', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('utm_medium', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('utm_source', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('utm_campaign', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    op.create_table(
        'logs_activity_recherche',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('dateheure', mysql.DATETIME()),
        sa.Column('idutilisateur_peconnect', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('ville', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('code_postal', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('emploi', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    op.create_table(
        'logs_activity_dpae_clean',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('idutilisateur_peconnect', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('siret', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('date_activite', mysql.DATETIME()),
        sa.Column('date_embauche', mysql.DATETIME()),
        sa.Column('type_contrat', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('duree_activite_cdd_mois', mysql.INTEGER()),
        sa.Column('duree_activite_cdd_jours', mysql.INTEGER()),
        sa.Column('diff_activite_embauche_jrs', mysql.INTEGER()),
        sa.Column('dc_lblprioritede', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('tranche_age', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('dc_prive_public', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('duree_prise_en_charge', mysql.INTEGER()),
        sa.Column('dn_tailleetablissement', mysql.INTEGER()),
        sa.Column('code_postal', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('logs_idpe_connect')
    op.drop_table('logs_activity')
    op.drop_table('logs_activity_recherche')
    op.drop_table('logs_activity_dpae_clean')
