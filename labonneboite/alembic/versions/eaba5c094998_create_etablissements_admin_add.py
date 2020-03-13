"""
Add `OfficeAdminAdd` table.

Revision ID: eaba5c094998
Revises: ba4492177099
Create Date: 2017-08-08 13:21:40.075614
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "eaba5c094998"
down_revision = "ba4492177099"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "etablissements_admin_add",
        sa.Column("siret", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("raisonsociale", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("enseigne", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("codenaf", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=8), nullable=False),
        sa.Column("numerorue", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("libellerue", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("codecommune", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("codepostal", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=8), nullable=False),
        sa.Column("email", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("tel", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("website", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
        sa.Column("flag_alternance", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("flag_junior", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("flag_senior", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("flag_handicap", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column("departement", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=8), nullable=False),
        sa.Column("trancheeffectif", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=2), nullable=True),
        sa.Column("score", mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
        sa.Column("coordinates_x", mysql.FLOAT(), nullable=False),
        sa.Column("coordinates_y", mysql.FLOAT(), nullable=False),
        sa.Column("id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
        sa.Column("reason", mysql.TEXT(collation="utf8mb4_unicode_ci"), nullable=False),
        sa.Column("date_created", mysql.DATETIME(), nullable=False),
        sa.Column("date_updated", mysql.DATETIME(), nullable=True),
        sa.Column("created_by_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("updated_by_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="etablissements_admin_add_ibfk_1", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"], ["users.id"], name="etablissements_admin_add_ibfk_2", ondelete="SET NULL"
        ),
        # this is a mistake, fixed by a later migration - primary key should be ID only
        sa.PrimaryKeyConstraint("siret", "id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )


def downgrade():
    op.drop_table("etablissements_admin_add")
