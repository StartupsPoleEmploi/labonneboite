"""
add alternate index for offers on etablissements

Revision ID: 2df1845b3dc5
Revises: 7de6af1a7088
Create Date: 2018-10-22 14:28:49.887652
"""
from alembic import op


# Revision identifiers, used by Alembic.
revision = '2df1845b3dc5'
down_revision = '7de6af1a7088'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('_enseigne_codecommune', 'etablissements', ['enseigne', 'codecommune'], unique=False)
    op.create_index('_enseigne_codecommune', 'etablissements_exportable', ['enseigne', 'codecommune'], unique=False)


def downgrade():
    op.drop_constraint('_enseigne_codecommune', 'etablissements', type_='unique')
    op.drop_constraint('_enseigne_codecommune', 'etablissements_exportable', type_='unique')

