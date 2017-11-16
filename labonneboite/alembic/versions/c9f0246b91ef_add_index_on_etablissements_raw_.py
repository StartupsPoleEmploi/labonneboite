"""
add index on etablissements_raw.departement

Revision ID: c9f0246b91ef
Revises: 33e80a1c96e0
Create Date: 2017-11-24 09:30:00.888559
"""
from alembic import op

# Revision identifiers, used by Alembic.
revision = 'c9f0246b91ef'
down_revision = '33e80a1c96e0'
branch_labels = None
depends_on = None



def upgrade():
    op.create_index('dept_i', 'etablissements_raw', ['departement'], unique=False)


def downgrade():
    op.drop_constraint('dept_i', 'etablissements_raw', type_='unique')
