"""
Add `new_company_name` and `new_office_name` fields to `etablissements_admin_update`.

Revision ID: c4c5f7a025c4
Revises: 881f590506b5
Create Date: 2019-06-04 11:22:15.221381
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "c4c5f7a025c4"
down_revision = "881f590506b5"
branch_labels = None
depends_on = None


def upgrade():
    # New "raison sociale".
    op.add_column(
        "etablissements_admin_update",
        sa.Column("new_company_name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
    )
    # New "enseigne".
    op.add_column(
        "etablissements_admin_update",
        sa.Column("new_office_name", mysql.VARCHAR(collation="utf8mb4_unicode_ci", length=191), nullable=False),
    )


def downgrade():
    op.drop_column("etablissements_admin_update", "new_company_name")
    op.drop_column("etablissements_admin_update", "new_office_name")
