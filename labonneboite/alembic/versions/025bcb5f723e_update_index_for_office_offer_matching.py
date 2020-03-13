"""
update index for office offer matching

Revision ID: 025bcb5f723e
Revises: 8f1ef5533cc7
Create Date: 2018-12-13 12:18:58.492180
"""
import sqlalchemy as sa
from alembic import op


# Revision identifiers, used by Alembic.
revision = "025bcb5f723e"
down_revision = "8f1ef5533cc7"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("_raisonsociale_codecommune", "etablissements", type_="unique")
    op.drop_constraint("_raisonsociale_codecommune", "etablissements_exportable", type_="unique")
    op.drop_constraint("_enseigne_codecommune", "etablissements", type_="unique")
    op.drop_constraint("_enseigne_codecommune", "etablissements_exportable", type_="unique")
    op.create_index("_raisonsociale_departement", "etablissements", ["raisonsociale", "departement"], unique=False)
    op.create_index(
        "_raisonsociale_departement", "etablissements_exportable", ["raisonsociale", "departement"], unique=False
    )
    op.create_index("_enseigne_departement", "etablissements", ["enseigne", "departement"], unique=False)
    op.create_index("_enseigne_departement", "etablissements_exportable", ["enseigne", "departement"], unique=False)


def downgrade():
    op.drop_constraint("_raisonsociale_departement", "etablissements", type_="unique")
    op.drop_constraint("_raisonsociale_departement", "etablissements_exportable", type_="unique")
    op.drop_constraint("_enseigne_departement", "etablissements", type_="unique")
    op.drop_constraint("_enseigne_departement", "etablissements_exportable", type_="unique")
    op.create_index("_raisonsociale_codecommune", "etablissements", ["raisonsociale", "codecommune"], unique=False)
    op.create_index(
        "_raisonsociale_codecommune", "etablissements_exportable", ["raisonsociale", "codecommune"], unique=False
    )
    op.create_index("_enseigne_codecommune", "etablissements", ["enseigne", "codecommune"], unique=False)
    op.create_index("_enseigne_codecommune", "etablissements_exportable", ["enseigne", "codecommune"], unique=False)
