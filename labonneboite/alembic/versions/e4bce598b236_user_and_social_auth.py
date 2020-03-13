"""
Add User and Social Auth tables.

Revision ID: e4bce598b236
Revises: d0c07945abc1
Create Date: 2017-03-15 14:05:53.077840
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "e4bce598b236"
down_revision = "d0c07945abc1"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "users",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("email", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("gender", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("first_name", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("last_name", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("date_created", mysql.DATETIME(), nullable=True),
        sa.Column("active", mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "social_auth_usersocialauth",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("provider", mysql.VARCHAR(length=32), nullable=True),
        sa.Column("extra_data", mysql.TEXT(), nullable=True),
        sa.Column("uid", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("user_id", mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="social_auth_usersocialauth_ibfk_1"),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "social_auth_nonce",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("server_url", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("timestamp", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("salt", mysql.VARCHAR(length=40), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "social_auth_partial",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("token", mysql.VARCHAR(length=32), nullable=True),
        sa.Column("data", mysql.TEXT(), nullable=True),
        sa.Column("next_step", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("backend", mysql.VARCHAR(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "social_auth_code",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("email", mysql.VARCHAR(length=200), nullable=True),
        sa.Column("code", mysql.VARCHAR(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )

    op.create_table(
        "social_auth_association",
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("server_url", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("handle", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("secret", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("issued", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("lifetime", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column("assoc_type", mysql.VARCHAR(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_collate="utf8mb4_unicode_ci",
        mysql_default_charset="utf8mb4",
        mysql_engine="InnoDB",
    )


def downgrade():
    op.drop_table("social_auth_association")
    op.drop_table("social_auth_code")
    op.drop_table("social_auth_partial")
    op.drop_table("social_auth_nonce")
    op.drop_table("social_auth_usersocialauth")
    op.drop_table("users")
