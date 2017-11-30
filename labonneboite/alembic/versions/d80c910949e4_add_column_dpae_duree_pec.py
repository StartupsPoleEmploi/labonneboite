"""
add column dpae.duree_pec

Revision ID: d80c910949e4
Revises: 0592646101eb
Create Date: 2017-11-20 14:53:20.499202
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'd80c910949e4'
down_revision = '0592646101eb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'dpae',
        sa.Column('duree_pec', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True)
    )


def downgrade():
    op.drop_column('dpae', 'duree_pec')
