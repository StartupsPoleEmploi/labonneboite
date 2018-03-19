"""
rename dpae table to hirings

Revision ID: 5d43d4cf1847
Revises: e21ab8255e02
Create Date: 2018-03-19 17:31:54.377681
"""
from alembic import op


# Revision identifiers, used by Alembic.
revision = '5d43d4cf1847'
down_revision = 'db2fdfb935ec'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('dpae', 'hirings')


def downgrade():
    op.rename_table('hirings', 'dpae')
