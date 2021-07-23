"""
Allow empty alternance email in SAVE

Revision ID: 36188da1a919
Revises: 6a40b75d390a
Create Date: 2021-07-19 10:33:57.780826
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '36188da1a919'
down_revision = '6a40b75d390a'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('etablissements_admin_update', 'email_alternance', nullable=True, existing_type=mysql.TEXT())
    op.alter_column('etablissements_admin_add', 'email_alternance', nullable=True, existing_type=mysql.TEXT())
    op.alter_column('etablissements_exportable', 'email_alternance', nullable=True, existing_type=mysql.TEXT())
    op.alter_column('etablissements', 'email_alternance', nullable=True, existing_type=mysql.TEXT())

def downgrade():
    op.alter_column('etablissements_admin_update', 'email_alternance', nullable=False, existing_type=mysql.TEXT())
    op.alter_column('etablissements_admin_add', 'email_alternance', nullable=False, existing_type=mysql.TEXT())
    op.alter_column('etablissements_exportable', 'email_alternance', nullable=False, existing_type=mysql.TEXT())
    op.alter_column('etablissements', 'email_alternance', nullable=False, existing_type=mysql.TEXT())
