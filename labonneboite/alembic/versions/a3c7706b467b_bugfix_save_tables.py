"""
bugfix save tables

Revision ID: a3c7706b467b
Revises: 39042f1317e3
Create Date: 2018-04-25 14:10:55.209984
"""
from alembic import op
from sqlalchemy.dialects import mysql


# import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "a3c7706b467b"
down_revision = "39042f1317e3"
branch_labels = None
depends_on = None


def upgrade():
    # ensure siret unicity in SAVE tables to avoid potential issues
    op.create_index("siret_unique", "etablissements_admin_add", ["siret"], unique=True)
    op.create_index("siret_unique", "etablissements_admin_remove", ["siret"], unique=True)
    op.create_index("siret_unique", "etablissements_admin_extra_geolocations", ["siret"], unique=True)

    # primary key should be on 'id' only
    op.drop_constraint("siret_id", "etablissements_admin_add", type_="primary")
    op.create_primary_key("id", "etablissements_admin_add", ["id"], schema=None)

    # enable autoincrement for 'id'
    op.alter_column(
        "etablissements_admin_add", "id", autoincrement=True, existing_type=mysql.INTEGER(display_width=11)
    )


def downgrade():
    op.drop_constraint("siret_unique", "etablissements_admin_add", type_="unique")
    op.drop_constraint("siret_unique", "etablissements_admin_remove", type_="unique")
    op.drop_constraint("siret_unique", "etablissements_admin_extra_geolocations", type_="unique")

    op.alter_column(
        "etablissements_admin_add", "id", autoincrement=False, existing_type=mysql.INTEGER(display_width=11)
    )
    op.drop_constraint("id", "etablissements_admin_add", type_="primary")
    op.create_primary_key("siret_id", "etablissements_admin_add", ["siret", "id"], schema=None)
