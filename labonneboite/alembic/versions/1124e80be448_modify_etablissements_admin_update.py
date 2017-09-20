"""
Modify `OfficeAdminUpdate`:
- add `romes_to_boost` field
- add `boost` field
- migrate data from `new_score` field to `boost` field
- remove `new_score` field

Revision ID: 1124e80be448
Revises: f03cff523555
Create Date: 2017-09-19 09:25:28.681977
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '1124e80be448'
down_revision = 'f03cff523555'
branch_labels = None
depends_on = None


def upgrade():

    op.add_column('etablissements_admin_update', sa.Column('romes_to_boost',
        mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False))

    op.add_column('etablissements_admin_update', sa.Column('boost', mysql.TINYINT(display_width=1),
        server_default=sa.text(u"'0'"), autoincrement=False, nullable=False))

    conn = op.get_bind()
    for item in conn.execute("SELECT * FROM `etablissements_admin_update`;"):
        if item.new_score == 100:
            conn.execute("UPDATE `etablissements_admin_update` SET `boost` = 1 WHERE id = %s;" % item.id)

    op.drop_column('etablissements_admin_update', 'new_score')

def downgrade():

    op.add_column('etablissements_admin_update', sa.Column('new_score', mysql.INTEGER(display_width=11),
        autoincrement=False, nullable=True))

    conn = op.get_bind()
    for item in conn.execute("SELECT * FROM `etablissements_admin_update`;"):
        if item.boost:
            conn.execute("UPDATE `etablissements_admin_update` SET `new_score` = 100 WHERE id = %s;" % item.id)

    op.drop_column('etablissements_admin_update', 'romes_to_boost')
    op.drop_column('etablissements_admin_update', 'boost')
