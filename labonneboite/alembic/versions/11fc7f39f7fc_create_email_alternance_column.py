"""
create email_alternance column

Revision ID: 11fc7f39f7fc
Revises: 4db5a80597e7
Create Date: 2017-11-20 11:19:59.347665
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# works - even if there is a pylint warning which says it does not.
from labonneboite.common.env import get_current_env, ENV_STAGING, ENV_PRODUCTION

etablissements_table_is_managed_by_deploy_data = (get_current_env() in [ENV_STAGING, ENV_PRODUCTION])


# Revision identifiers, used by Alembic.
revision = '11fc7f39f7fc'
down_revision = '4db5a80597e7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('etablissements_admin_update', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))
    op.add_column('etablissements_admin_add', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))
    op.add_column('etablissements_exportable', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))
    op.add_column('etablissements_raw', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))
    if not etablissements_table_is_managed_by_deploy_data:
        op.add_column('etablissements', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))

def downgrade():
    op.drop_column('etablissements_admin_update', 'email_alternance')
    op.drop_column('etablissements_admin_add', 'email_alternance')
    op.drop_column('etablissements_exportable', 'email_alternance')
    op.drop_column('etablissements_raw', 'email_alternance')
    if not etablissements_table_is_managed_by_deploy_data:
        op.drop_column('etablissements', 'email_alternance')
