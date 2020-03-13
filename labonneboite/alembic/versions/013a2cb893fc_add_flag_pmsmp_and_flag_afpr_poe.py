"""
add_flag_pmsmp_and_flag_afpr_poe

Revision ID: 013a2cb893fc
Revises: c5cd5037cb31
Create Date: 2019-03-01 11:39:05.272684
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "013a2cb893fc"
down_revision = "c5cd5037cb31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "etablissements_raw",
        sa.Column("flag_poe_afpr", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements_raw",
        sa.Column("flag_pmsmp", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements",
        sa.Column("flag_poe_afpr", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements", sa.Column("flag_pmsmp", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False)
    )
    op.add_column(
        "etablissements_admin_add",
        sa.Column("flag_poe_afpr", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements_admin_add",
        sa.Column("flag_pmsmp", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements_exportable",
        sa.Column("flag_poe_afpr", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements_exportable",
        sa.Column("flag_pmsmp", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements_backoffice",
        sa.Column("flag_poe_afpr", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )
    op.add_column(
        "etablissements_backoffice",
        sa.Column("flag_pmsmp", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )


def downgrade():
    op.drop_column("etablissements_raw", "flag_poe_afpr")
    op.drop_column("etablissements_raw", "flag_pmsmp")
    op.drop_column("etablissements", "flag_poe_afpr")
    op.drop_column("etablissements", "flag_pmsmp")
    op.drop_column("etablissements_admin_add", "flag_poe_afpr")
    op.drop_column("etablissements_admin_add", "flag_pmsmp")
    op.drop_column("etablissements_exportable", "flag_poe_afpr")
    op.drop_column("etablissements_exportable", "flag_pmsmp")
    op.drop_column("etablissements_backoffice", "flag_poe_afpr")
    op.drop_column("etablissements_backoffice", "flag_pmsmp")
