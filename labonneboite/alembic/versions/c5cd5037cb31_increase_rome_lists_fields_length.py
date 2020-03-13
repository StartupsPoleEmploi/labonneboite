"""
increase rome lists fields length

Revision ID: c5cd5037cb31
Revises: 025bcb5f723e
Create Date: 2019-02-05 16:22:03.849183
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "c5cd5037cb31"
down_revision = "025bcb5f723e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("update_jobs_recruiter_message", "romes_to_add", type_=mysql.TEXT(collation="utf8mb4_unicode_ci"))
    op.alter_column(
        "update_jobs_recruiter_message", "romes_to_remove", type_=mysql.TEXT(collation="utf8mb4_unicode_ci")
    )
    op.alter_column(
        "update_jobs_recruiter_message", "romes_alternance_to_add", type_=mysql.TEXT(collation="utf8mb4_unicode_ci")
    )
    op.alter_column(
        "update_jobs_recruiter_message", "romes_alternance_to_remove", type_=mysql.TEXT(collation="utf8mb4_unicode_ci")
    )


def downgrade():
    op.alter_column(
        "update_jobs_recruiter_message", "romes_to_add", type_=mysql.TINYTEXT(collation="utf8mb4_unicode_ci")
    )
    op.alter_column(
        "update_jobs_recruiter_message", "romes_to_remove", type_=mysql.TINYTEXT(collation="utf8mb4_unicode_ci")
    )
    op.alter_column(
        "update_jobs_recruiter_message",
        "romes_alternance_to_add",
        type_=mysql.TINYTEXT(collation="utf8mb4_unicode_ci"),
    )
    op.alter_column(
        "update_jobs_recruiter_message",
        "romes_alternance_to_remove",
        type_=mysql.TINYTEXT(collation="utf8mb4_unicode_ci"),
    )
