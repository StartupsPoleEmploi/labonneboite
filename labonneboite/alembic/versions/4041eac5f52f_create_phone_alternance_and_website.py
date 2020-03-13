"""
Create phone_alternance and website alternance

Revision ID: 4041eac5f52f
Revises: 2aca2291700f
Create Date: 2018-05-22 17:59:15.718908
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "4041eac5f52f"
down_revision = "2aca2291700f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("etablissements_admin_update", sa.Column("phone_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements", sa.Column("phone_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements_admin_add", sa.Column("phone_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements_raw", sa.Column("phone_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements_exportable", sa.Column("phone_alternance", mysql.TINYTEXT, nullable=True))

    op.add_column("etablissements_admin_update", sa.Column("website_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements", sa.Column("website_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements_admin_add", sa.Column("website_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements_raw", sa.Column("website_alternance", mysql.TINYTEXT, nullable=True))
    op.add_column("etablissements_exportable", sa.Column("website_alternance", mysql.TINYTEXT, nullable=True))


def downgrade():
    op.drop_column("etablissements_admin_update", "phone_alternance")
    op.drop_column("etablissements_admin_add", "phone_alternance")
    op.drop_column("etablissements_exportable", "phone_alternance")
    op.drop_column("etablissements_raw", "phone_alternance")
    op.drop_column("etablissements", "phone_alternance")

    op.drop_column("etablissements_admin_update", "website_alternance")
    op.drop_column("etablissements_admin_add", "website_alternance")
    op.drop_column("etablissements_exportable", "website_alternance")
    op.drop_column("etablissements_raw", "website_alternance")
    op.drop_column("etablissements", "website_alternance")
