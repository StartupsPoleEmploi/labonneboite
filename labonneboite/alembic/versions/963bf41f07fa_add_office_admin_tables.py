"""
Add office admin tables

Revision ID: 963bf41f07fa
Revises: 2426e6b89deb
Create Date: 2017-07-27 14:10:26.763571
"""
import codecs
import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "963bf41f07fa"
down_revision = "2426e6b89deb"
branch_labels = None
depends_on = None


def upgrade():

    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            mysql.TINYINT(display_width=1),
            server_default=sa.text("'0'"),
            autoincrement=False,
            nullable=False,
        ),
    )

    op.create_table(
        "etablissements_admin_remove",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("siret", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("reason", mysql.TEXT(collation="utf8mb4_unicode_ci"), nullable=False),
        sa.Column("initiative", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("date_follow_up_phone_call", mysql.DATETIME(), nullable=True),
        sa.Column("requested_by_email", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column(
            "requested_by_first_name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False
        ),
        sa.Column("requested_by_last_name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("requested_by_phone", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("date_created", mysql.DATETIME(), nullable=False),
        sa.Column("date_updated", mysql.DATETIME(), nullable=True),
        sa.Column("created_by_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("updated_by_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="etablissements_admin_remove_ibfk_1", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"], ["users.id"], name="etablissements_admin_remove_ibfk_2", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "etablissements_admin_update",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("siret", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("new_score", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("new_email", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("new_phone", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("new_website", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("remove_email", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("remove_phone", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("remove_website", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("requested_by_email", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column(
            "requested_by_first_name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False
        ),
        sa.Column("requested_by_last_name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("requested_by_phone", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("date_created", mysql.DATETIME(), nullable=False),
        sa.Column("date_updated", mysql.DATETIME(), nullable=True),
        sa.Column("created_by_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("updated_by_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="etablissements_admin_update_ibfk_1", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"], ["users.id"], name="etablissements_admin_update_ibfk_2", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    # Load initial SQL dumps.
    conn = op.get_bind()
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))

    initial_remove_sql = os.path.join(PARENT_DIR, "sql/initial_etablissements_admin_remove.sql")
    with codecs.open(initial_remove_sql, encoding="utf-8") as f:
        sql = f.read()
        conn.execute(sa.sql.text(sql))

    initial_update_sql = os.path.join(PARENT_DIR, "sql/initial_etablissements_admin_update.sql")
    with codecs.open(initial_update_sql, encoding="utf-8") as f:
        sql = f.read()
        conn.execute(sa.sql.text(sql))


def downgrade():
    op.drop_column("users", "is_admin")
    op.drop_table("etablissements_admin_update")
    op.drop_table("etablissements_admin_remove")
