"""
add index on dpae.departement

Revision ID: 33e80a1c96e0
Revises: d80c910949e4
Create Date: 2017-11-24 09:29:50.499646
"""
from alembic import op

# Revision identifiers, used by Alembic.
revision = '33e80a1c96e0'
down_revision = 'd80c910949e4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('dept_i', 'dpae', ['departement'], unique=False)


def downgrade():
    op.drop_constraint('dept_i', 'dpae', type_='unique')
