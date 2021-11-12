"""
Add field is_long_duration_job_seekers to users

Revision ID: c1b32b5a8feb
Revises: 29cdae903fb3
Create Date: 2021-11-11 14:57:22.326759
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# Revision identifiers, used by Alembic.
revision = 'c1b32b5a8feb'
down_revision = '29cdae903fb3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('is_long_duration_job_seekers', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    )


def downgrade():
    op.drop_column('users', 'is_long_duration_job_seekers')
