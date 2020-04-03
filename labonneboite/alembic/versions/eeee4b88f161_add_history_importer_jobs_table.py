"""
Add history importer jobs table

Revision ID: eeee4b88f161
Revises: c4c5f7a025c4
Create Date: 2020-03-30 12:01:57.047087
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = 'eeee4b88f161'
down_revision = 'ccc88fc92e0f'
branch_labels = None
depends_on = None

def upgrade():

    op.create_table(
        'history_importer_jobs',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('start_date', mysql.DATETIME()),
        sa.Column('end_date', mysql.DATETIME()),
        sa.Column('job_name', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('status', mysql.INTEGER()),
        sa.Column('exception', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.Column('trace_log', mysql.TEXT(collation='utf8mb4_unicode_ci')),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

def downgrade():
    op.drop_table('history_importer_jobs')
