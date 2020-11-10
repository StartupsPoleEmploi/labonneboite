"""
add_history_blacklist

Revision ID: bf9cda8a53d2
Revises: e9b4b34e5163
Create Date: 2020-11-09 17:32:59.471122
"""
from alembic import op

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# Revision identifiers, used by Alembic.
revision = 'bf9cda8a53d2'
down_revision = 'e9b4b34e5163'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('history_blacklist',
                    sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
                    sa.Column('email', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
                    sa.Column('datetime_removal', mysql.DATETIME(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_collate='utf8mb4_unicode_ci',
                    mysql_default_charset='utf8mb4',
                    mysql_engine='InnoDB'
                    )
    pass


def downgrade():
    op.drop_table('history_blacklist')
    pass
