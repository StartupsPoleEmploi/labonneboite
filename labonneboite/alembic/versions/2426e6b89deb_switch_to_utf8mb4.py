"""
Convert database to utf8mb4.

See: "Converting Between 3-Byte and 4-Byte Unicode Character Sets":
https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-conversion.html

Revision ID: 2426e6b89deb
Revises: 428e168fdf0c
Create Date: 2017-07-20 13:19:58.132736
"""
from alembic import op

import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '2426e6b89deb'
down_revision = '428e168fdf0c'
branch_labels = None
depends_on = None


TABLES = [
    'alembic_version',
    'social_auth_association',
    'social_auth_code',
    'social_auth_nonce',
    'social_auth_partial',
    'social_auth_usersocialauth',
    'users',
    'user_favorite_offices',
    'etablissements',
]

TABLES_WITH_VARCHAR_COLUMNS = {
  'etablissements': (
    'siret',
    'raisonsociale',
    'enseigne',
    'codenaf',
    'trancheeffectif',
    'numerorue',
    'libellerue',
    'tel',
    'email',
    'website',
    'codecommune',
  ),
  'social_auth_association': (
    'server_url',
    'handle',
    'secret',
  ),
  'social_auth_nonce': (
    'server_url',
  ),
  'social_auth_usersocialauth': (
    'uid',
  ),
  'user_favorite_offices': (
    'office_siret',
  ),
  'users': (
    'email',
    'gender',
    'first_name',
    'last_name',
    'external_id',
  ),
}


def drop_constraints(conn):
    """
    Drop constraints.
    This must be done before altering tables to avoid a lot of MySQL errors related to index sizes:
    https://dev.mysql.com/doc/refman/5.5/en/charset-unicode-conversion.html
    """
    # Drop foreign key on `office_siret` to `etablissements(siret)` on the `user_favorite_offices` table.
    conn.execute("ALTER TABLE user_favorite_offices DROP FOREIGN KEY `user_favorite_offices_ibfk_2`;")
    # Drop foreign key on `user_id` to `users(user_id)` on the `user_favorite_offices` table.
    conn.execute("ALTER TABLE user_favorite_offices DROP FOREIGN KEY `user_favorite_offices_ibfk_1`;")
    # Drop index `office_siret` on the `user_favorite_offices` table.
    conn.execute("ALTER TABLE user_favorite_offices DROP KEY `user_favorite_offices_ibfk_2`;")
    # Drop unique key (`user_id`, `office_siret`) on the `user_favorite_offices` table.
    conn.execute("ALTER TABLE user_favorite_offices DROP KEY `_user_fav_office`;")
    # Drop the PK on the `etablissements` table.
    conn.execute("ALTER TABLE etablissements DROP INDEX `PRIMARY`;")


def create_constraints(conn):
    """
    Re-create constraints.
    """
    # Create the PK on the `etablissements` table.
    conn.execute("ALTER TABLE etablissements ADD PRIMARY KEY(siret);")
    # Create foreign key on `office_siret` to `etablissements(siret)` on the `user_favorite_offices` table.
    conn.execute(
        "ALTER TABLE user_favorite_offices "
        + "ADD CONSTRAINT user_favorite_offices_ibfk_2 FOREIGN KEY (office_siret) REFERENCES etablissements(siret) "
        + "ON DELETE CASCADE;")
    # Create foreign key on `user_id` to `users(user_id)` on the `user_favorite_offices` table.
    conn.execute(
        "ALTER TABLE user_favorite_offices "
        + "ADD CONSTRAINT `user_favorite_offices_ibfk_1` FOREIGN KEY (user_id) REFERENCES users(id) "
        + "ON DELETE CASCADE;")
    # Create unique key (`user_id`, `office_siret`) on the `user_favorite_offices` table.
    conn.execute("ALTER TABLE user_favorite_offices ADD UNIQUE KEY `_user_fav_office` (user_id, office_siret);")


def upgrade():
    """
    Convert from utf8 to utf8mb4 to support characters outside of the "Basic Multilingual Plane".
    """

    conn = op.get_bind()

    drop_constraints(conn)

    # For each column.
    for table in TABLES_WITH_VARCHAR_COLUMNS:
        columns = TABLES_WITH_VARCHAR_COLUMNS[table]
        for column in columns:
            sql = "ALTER TABLE %s MODIFY %s VARCHAR(191);" % (table, column)
            conn.execute(sa.sql.text(sql))

    # For each table.
    for table in TABLES:
        sql = "ALTER TABLE %s CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" % table
        conn.execute(sa.sql.text(sql))

    create_constraints(conn)


def downgrade():
    """
    Convert from utf8mb4 to utf8.
    This should never happen and is here for test purpose.
    Characters outside of the "Basic Multilingual Plane" will be crushed.
    """

    conn = op.get_bind()

    drop_constraints(conn)

    # For each column.
    for table in TABLES_WITH_VARCHAR_COLUMNS:
        columns = TABLES_WITH_VARCHAR_COLUMNS[table]
        for column in columns:
            sql = "ALTER TABLE %s MODIFY %s VARCHAR(255);" % (table, column)
            conn.execute(sa.sql.text(sql))

    # For each table.
    for table in TABLES:
        sql = "ALTER TABLE %s CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;" % table
        conn.execute(sa.sql.text(sql))

    create_constraints(conn)
