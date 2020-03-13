"""
add index for offers on etablissements

Revision ID: 7de6af1a7088
Revises: c519ecaf1fa6
Create Date: 2018-09-27 14:51:52.033500
"""
from alembic import op


# Revision identifiers, used by Alembic.
revision = "7de6af1a7088"
down_revision = "c519ecaf1fa6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("_raisonsociale_codecommune", "etablissements", ["raisonsociale", "codecommune"], unique=False)
    op.create_index(
        "_raisonsociale_codecommune", "etablissements_exportable", ["raisonsociale", "codecommune"], unique=False
    )


def downgrade():
    op.drop_constraint("_raisonsociale_codecommune", "etablissements", type_="unique")
    op.drop_constraint("_raisonsociale_codecommune", "etablissements_exportable", type_="unique")
