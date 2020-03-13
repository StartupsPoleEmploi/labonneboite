"""
add index on hirings siret for convenience

Revision ID: 8f1ef5533cc7
Revises: 99473cb51564
Create Date: 2018-11-30 15:47:05.680039
"""
from alembic import op


# Revision identifiers, used by Alembic.
revision = "8f1ef5533cc7"
down_revision = "99473cb51564"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("_siret", "hirings", ["siret"], unique=False)


def downgrade():
    op.drop_constraint("_siret", "hirings", type_="unique")
