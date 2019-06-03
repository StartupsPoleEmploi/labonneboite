"""
drop indexes used for api offres v1

Revision ID: 881f590506b5
Revises: 013a2cb893fc
Create Date: 2019-05-30 14:17:47.453223
"""
from alembic import op

import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '881f590506b5'
down_revision = '013a2cb893fc'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('_raisonsociale_departement', 'etablissements', type_='unique')
    op.drop_constraint('_raisonsociale_departement', 'etablissements_exportable', type_='unique')
    op.drop_constraint('_enseigne_departement', 'etablissements', type_='unique')
    op.drop_constraint('_enseigne_departement', 'etablissements_exportable', type_='unique')

def downgrade():
    op.create_index('_raisonsociale_departement', 'etablissements', ['raisonsociale', 'departement'], unique=False)
    op.create_index('_raisonsociale_departement', 'etablissements_exportable', ['raisonsociale', 'departement'], unique=False)
    op.create_index('_enseigne_departement', 'etablissements', ['enseigne', 'departement'], unique=False)
    op.create_index('_enseigne_departement', 'etablissements_exportable', ['enseigne', 'departement'], unique=False)
