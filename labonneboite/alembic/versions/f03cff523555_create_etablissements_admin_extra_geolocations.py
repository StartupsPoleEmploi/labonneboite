"""
Add OfficeAdminExtraGeoLocation table.

Revision ID: f03cff523555
Revises: 090e86dfc304
Create Date: 2017-08-22 12:19:46.926977
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'f03cff523555'
down_revision = '090e86dfc304'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'etablissements_admin_extra_geolocations',
        sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
        sa.Column('siret', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('codes', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('geolocations', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('date_end', mysql.DATETIME(), nullable=False),
        sa.Column('reason', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('date_created', mysql.DATETIME(), nullable=False),
        sa.Column('date_updated', mysql.DATETIME(), nullable=True),
        sa.Column('created_by_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('updated_by_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'],
            name='etablissements_admin_extra_geolocations_ibfk_1', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'],
            name='etablissements_admin_extra_geolocations_ibfk_2', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('etablissements_admin_extra_geolocations')
