"""
harmonize indexes

Revision ID: 200d176f96b6
Revises: 2df1845b3dc5
Create Date: 2018-11-30 15:12:23.807521
"""
import sqlalchemy as sa
from alembic import op


# Revision identifiers, used by Alembic.
revision = "200d176f96b6"
down_revision = "e305ab1e864e"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("dept_i", "etablissements", type_="unique")
    op.drop_constraint("dept_i", "etablissements_exportable", type_="unique")
    op.drop_constraint("dept_i", "etablissements_raw", type_="unique")
    op.drop_constraint("dept_i", "hirings", type_="unique")
    op.create_index("_departement", "etablissements", ["departement"], unique=False)
    op.create_index("_departement", "etablissements_exportable", ["departement"], unique=False)
    op.create_index("_departement", "etablissements_raw", ["departement"], unique=False)
    op.create_index("_departement", "hirings", ["departement"], unique=False)


def downgrade():
    op.drop_constraint("_departement", "etablissements", type_="unique")
    op.drop_constraint("_departement", "etablissements_exportable", type_="unique")
    op.drop_constraint("_departement", "etablissements_raw", type_="unique")
    op.drop_constraint("_departement", "hirings", type_="unique")
    op.create_index("dept_i", "etablissements", ["departement"], unique=False)
    op.create_index("dept_i", "etablissements_exportable", ["departement"], unique=False)
    op.create_index("dept_i", "etablissements_raw", ["departement"], unique=False)
    op.create_index("dept_i", "hirings", ["departement"], unique=False)
