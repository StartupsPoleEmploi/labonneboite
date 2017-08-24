"""
Switch to utf8mb4 (forgotten column)

Revision ID: ba4492177099
Revises: 963bf41f07fa
Create Date: 2017-08-04 12:49:44.849038
"""
from alembic import op

import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'ba4492177099'
down_revision = '963bf41f07fa'
branch_labels = None
depends_on = None


TABLES_WITH_VARCHAR_COLUMNS = {
  'social_auth_code': (
    'email',
  ),
}


def upgrade():
    """
    Convert from utf8 to utf8mb4 to support characters outside of the "Basic Multilingual Plane".
    """

    conn = op.get_bind()

    # For each column.
    for table in TABLES_WITH_VARCHAR_COLUMNS:
        columns = TABLES_WITH_VARCHAR_COLUMNS[table]
        for column in columns:
            sql = "ALTER TABLE %s MODIFY %s VARCHAR(191);" % (table, column)
            conn.execute(sa.sql.text(sql))


def downgrade():
    """
    Convert from utf8mb4 to utf8.
    This should never happen and is here for test purpose.
    Characters outside of the "Basic Multilingual Plane" will be crushed.
    """

    conn = op.get_bind()

    # For each column.
    for table in TABLES_WITH_VARCHAR_COLUMNS:
        columns = TABLES_WITH_VARCHAR_COLUMNS[table]
        for column in columns:
            sql = "ALTER TABLE %s MODIFY %s VARCHAR(255);" % (table, column)
            conn.execute(sa.sql.text(sql))
