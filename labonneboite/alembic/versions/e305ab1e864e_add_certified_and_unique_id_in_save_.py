"""
Add certified and unique id in save forms and office_admin_update

Revision ID: e305ab1e864e
Revises: 2df1845b3dc5
Create Date: 2018-11-28 18:15:01.908123
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'e305ab1e864e'
down_revision = '2df1845b3dc5'
branch_labels = None
depends_on = None


def upgrade():
    # Save form
    op.add_column('etablissements_admin_update', sa.Column('certified_recruiter', mysql.BOOLEAN(), default=False))
    op.add_column('etablissements_admin_update', sa.Column('recruiter_uid', mysql.TINYTEXT(), default=''))

    # Recruiter messages
    op.add_column('other_recruiter_message', sa.Column('certified_recruiter', mysql.BOOLEAN(), default=False))
    op.add_column('other_recruiter_message', sa.Column('recruiter_uid', mysql.TINYTEXT(), default=''))

    op.add_column('remove_recruiter_message', sa.Column('certified_recruiter', mysql.BOOLEAN(), default=False))
    op.add_column('remove_recruiter_message', sa.Column('recruiter_uid', mysql.TINYTEXT(), default=''))

    op.add_column('update_coordinates_recruiter_message', sa.Column('certified_recruiter', mysql.BOOLEAN(), default=False))
    op.add_column('update_coordinates_recruiter_message', sa.Column('recruiter_uid', mysql.TINYTEXT(), default=''))

    op.add_column('update_jobs_recruiter_message', sa.Column('certified_recruiter', mysql.BOOLEAN(), default=False))
    op.add_column('update_jobs_recruiter_message', sa.Column('recruiter_uid', mysql.TINYTEXT(), default=''))


def downgrade():
    # Save form
    op.drop_column('etablissements_admin_update', 'certified_recruiter')
    op.drop_column('etablissements_admin_update', 'recruiter_uid')

    # Recruiter messages
    op.drop_column('other_recruiter_message', 'certified_recruiter')
    op.drop_column('other_recruiter_message', 'recruiter_uid')

    op.drop_column('remove_recruiter_message', 'certified_recruiter')
    op.drop_column('remove_recruiter_message', 'recruiter_uid')

    op.drop_column('update_coordinates_recruiter_message', 'certified_recruiter')
    op.drop_column('update_coordinates_recruiter_message', 'recruiter_uid')

    op.drop_column('update_jobs_recruiter_message', 'certified_recruiter')
    op.drop_column('update_jobs_recruiter_message', 'recruiter_uid')
