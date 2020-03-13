"""
Create 'remove_flag_alternance' in office_admin_update

Revision ID: 38fad89a549c
Revises: 11fc7f39f7fc
Create Date: 2017-12-13 09:58:01.163137
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "38fad89a549c"
down_revision = "11fc7f39f7fc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "etablissements_admin_update",
        sa.Column("remove_flag_alternance", mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
    )


def downgrade():
    op.drop_column("etablissements_admin_update", "remove_flag_alternance")
