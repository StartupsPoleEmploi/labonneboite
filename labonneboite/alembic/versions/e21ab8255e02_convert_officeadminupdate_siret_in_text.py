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
    conn = op.get_bind()
    conn.execute("ALTER TABLE `etablissements_admin_update` CHANGE siret sirets TEXT;")



def downgrade():
    conn = op.get_bind()
    conn.execute("ALTER TABLE `etablissements_admin_update` CHANGE sirets siret VARCHAR(191);")
