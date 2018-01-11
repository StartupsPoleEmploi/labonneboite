"""
convert OfficeAdminUpdate.siret in text

Revision ID: e21ab8255e02
Revises: 38fad89a549c
Create Date: 2018-01-11 14:10:58.780076
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'e21ab8255e02'
down_revision = '38fad89a549c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name='etablissements_admin_update',
        column_name='siret',
        type=mysql.TEXT(collation=u'utf8mb4_unicode_ci', length=65000),
        null=False
    )


def downgrade():
    op.alter_column(
        table_name='etablissements_admin_update',
        column_name='siret',
        type=mysql.VARCHAR(collation=u'utf8mb4_unicode_ci', length=191),
        null=False
    )
