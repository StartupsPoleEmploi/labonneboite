"""
add index on etablissements email

Revision ID: 99473cb51564
Revises: 200d176f96b6
Create Date: 2018-11-30 15:38:57.294679
"""
from alembic import op


# Revision identifiers, used by Alembic.
revision = '99473cb51564'
down_revision = '200d176f96b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('_email', 'etablissements', ['email'], unique=False)
    op.create_index('_email', 'etablissements_exportable', ['email'], unique=False)


def downgrade():
    op.drop_constraint('_email', 'etablissements', type_='unique')
    op.drop_constraint('_email', 'etablissements_exportable', type_='unique')
