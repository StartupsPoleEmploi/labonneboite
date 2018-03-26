"""
add score_alternance field

Revision ID: db2fdfb935ec
Revises: e21ab8255e02
Create Date: 2018-03-26 12:41:51.155213
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'db2fdfb935ec'
down_revision = 'e21ab8255e02'
branch_labels = None
depends_on = None

# works - even if there is a pylint warning which says it does not.
from labonneboite.common.env import get_current_env, ENV_STAGING, ENV_PRODUCTION

etablissements_table_is_managed_by_deploy_data = (get_current_env() in [ENV_STAGING, ENV_PRODUCTION])

def upgrade():
    op.add_column('etablissements_admin_add', sa.Column('score_alternance', mysql.INTEGER, default=0, nullable=False))
    op.add_column('etablissements_exportable', sa.Column('score_alternance', mysql.INTEGER, default=0, nullable=False))
    if not etablissements_table_is_managed_by_deploy_data:
        op.add_column('etablissements', sa.Column('score_alternance', mysql.INTEGER, default=0, nullable=False))

def downgrade():
    op.drop_column('etablissements_admin_add', 'score_alternance')
    op.drop_column('etablissements_exportable', 'score_alternance')
    if not etablissements_table_is_managed_by_deploy_data:
        op.drop_column('etablissements', 'score_alternance')
