"""
Rename remove_flag_alternance et create new_score and new_score_alternance

Revision ID: 80194630f4fe
Revises: a3c7706b467b
Create Date: 2018-05-17 15:53:02.360349
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '80194630f4fe'
down_revision = '3a70adf06a8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('etablissements_admin_update',
        sa.Column('new_score', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True)
    )

    op.add_column('etablissements_admin_update',
        sa.Column('new_score_alternance', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True)
    )

    # Set 'score_alternance = 0' where 'remove_flag_alternance=true'
    conn = op.get_bind()
    for item in conn.execute("SELECT * FROM `etablissements_admin_update`;"):
        if item.remove_flag_alternance:
            conn.execute("UPDATE `etablissements_admin_update` SET `new_score_alternance`=0 WHERE id = %s;" % item.id)

    op.drop_column('etablissements_admin_update', 'remove_flag_alternance')


def downgrade():
    # Recreate column 'remove_flag_alternance'
    op.add_column(
        'etablissements_admin_update',
        sa.Column('remove_flag_alternance', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False)
    )

    # Set 'remove_flag_alternance = 1' where 'new_score_alternance=100'
    conn = op.get_bind()
    for item in conn.execute("SELECT * FROM `etablissements_admin_update`;"):
        if item.new_score_alternance == 100:
            conn.execute("UPDATE `etablissements_admin_update` SET `remove_flag_alternance`=1 WHERE id = %s;" % item.id)

    op.drop_column('etablissements_admin_update', 'new_score')
    op.drop_column('etablissements_admin_update', 'new_score_alternance')

