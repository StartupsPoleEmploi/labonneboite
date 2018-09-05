"""
add index on departement etablissements etablissements_exportable

Revision ID: 91ee6fb3e7fd
Revises: 2e6781936bae
Create Date: 2018-09-05 11:54:46.526187
"""
from alembic import op

# Revision identifiers, used by Alembic.
revision = '91ee6fb3e7fd'
down_revision = '2e6781936bae'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('dept_i', 'etablissements', ['departement'], unique=False)
    op.create_index('dept_i', 'etablissements_exportable', ['departement'], unique=False)


def downgrade():
    op.drop_constraint('dept_i', 'etablissements', type_='unique')
    op.drop_constraint('dept_i', 'etablissements_exportable', type_='unique')
