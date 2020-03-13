"""
Create contact form table

Revision ID: 0da6b26c212f
Revises: d441dca1e974
Create Date: 2018-07-20 16:12:39.081415
"""
import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql
from sqlalchemy.types import Enum


# Revision identifiers, used by Alembic.
revision = "0da6b26c212f"
down_revision = "d441dca1e974"
branch_labels = None
depends_on = None


def create_table(name, *columns):
    common_colums = [
        sa.Column("id", mysql.INTEGER(display_width=11), nullable=False),
        sa.Column("siret", mysql.TINYTEXT(), nullable=True),
        sa.Column("requested_by_first_name", mysql.TINYTEXT()),
        sa.Column("requested_by_last_name", mysql.TINYTEXT(), nullable=True),
        sa.Column("requested_by_email", mysql.TINYTEXT(), nullable=True),
        sa.Column("requested_by_phone", mysql.TINYTEXT(), nullable=True),
        sa.Column("date_created", mysql.DATETIME(), nullable=True),
        sa.Column("date_updated", mysql.DATETIME(), nullable=True),
    ]
    args = [name] + common_colums + list(columns) + [sa.PrimaryKeyConstraint("id")]
    op.create_table(*args, mysql_collate="utf8mb4_unicode_ci", mysql_default_charset="utf8mb4", mysql_engine="InnoDB")


def upgrade():
    create_table(
        "other_recruiter_message", sa.Column("comment", mysql.TEXT(collation="utf8mb4_unicode_ci"), nullable=True)
    )

    create_table(
        "remove_recruiter_message",
        sa.Column("remove_lba", mysql.BOOLEAN(), default=True),
        sa.Column("remove_lbb", mysql.BOOLEAN(), default=True),
    )

    create_table(
        "update_coordinates_recruiter_message",
        sa.Column("new_website", mysql.TINYTEXT(), nullable=True),
        sa.Column("new_email", mysql.TINYTEXT(), nullable=True),
        sa.Column("new_phone", mysql.TINYTEXT(), nullable=True),
        sa.Column("contact_mode", mysql.TINYTEXT(), nullable=True),
        sa.Column("new_email_alternance", mysql.TINYTEXT(), nullable=True),
        sa.Column("new_phone_alternance", mysql.TINYTEXT(), nullable=True),
        sa.Column("social_network", mysql.TINYTEXT(), nullable=True),
    )

    create_table(
        "update_jobs_recruiter_message",
        # Update jobs : comma-separated rome ids
        sa.Column("romes_to_add", mysql.TINYTEXT(), nullable=True),
        sa.Column("romes_to_remove", mysql.TINYTEXT(), nullable=True),
        sa.Column("romes_alternance_to_add", mysql.TINYTEXT(), nullable=True),
        sa.Column("romes_alternance_to_remove", mysql.TINYTEXT(), nullable=True),
    )


def downgrade():
    op.drop_table("other_recruiter_message")
    op.drop_table("remove_recruiter_message")
    op.drop_table("update_coordinates_recruiter_message")
    op.drop_table("update_jobs_recruiter_message")
