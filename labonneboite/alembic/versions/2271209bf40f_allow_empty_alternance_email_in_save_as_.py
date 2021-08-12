"""
Allow empty alternance email in SAVE as an empty string

Revision ID: 2271209bf40f
Revises: 36188da1a919
Create Date: 2021-08-09 13:26:58.497425
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '2271209bf40f'
down_revision = '36188da1a919'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('etablissements_admin_update', 'email_alternance', nullable=False, server_default='', existing_type=mysql.TEXT())
    op.alter_column('etablissements_admin_add', 'email_alternance', nullable=False, server_default='', existing_type=mysql.TEXT())
    op.alter_column('etablissements_exportable', 'email_alternance', nullable=False, server_default='', existing_type=mysql.TEXT())
    op.alter_column('etablissements', 'email_alternance', nullable=False, server_default='', existing_type=mysql.TEXT())

def downgrade():
    op.alter_column('etablissements_admin_update', 'email_alternance', nullable=True, server_default=None, existing_type=mysql.TEXT())
    op.alter_column('etablissements_admin_add', 'email_alternance', nullable=True, server_default=None, existing_type=mysql.TEXT())
    op.alter_column('etablissements_exportable', 'email_alternance', nullable=True, server_default=None, existing_type=mysql.TEXT())
    op.alter_column('etablissements', 'email_alternance', nullable=True, server_default=None, existing_type=mysql.TEXT())

