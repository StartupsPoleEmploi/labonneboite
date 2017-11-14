"""
Add email_alternance column

Revision ID: fecea26e74c9
Revises: bde9330b83fa
Create Date: 2017-11-14 11:48:38.397980
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'fecea26e74c9'
down_revision = 'bde9330b83fa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('etablissements_admin_update', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))
    op.add_column('etablissements_admin_add', sa.Column('email_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))

def downgrade():
    op.drop_column('etablissements_admin_update', 'email_alternance')
    op.drop_column('etablissements_admin_add', 'email_alternance')
