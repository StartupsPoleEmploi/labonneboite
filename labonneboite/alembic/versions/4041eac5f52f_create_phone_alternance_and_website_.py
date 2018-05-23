"""
Create phone_alternance and website alternance

Revision ID: 4041eac5f52f
Revises: 80194630f4fe
Create Date: 2018-05-22 17:59:15.718908
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '4041eac5f52f'
down_revision = '80194630f4fe'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('etablissements_admin_update',
        sa.Column('phone_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False),
    )
    op.add_column('etablissements_admin_update',
        sa.Column('website_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False)
    )

    op.add_column('etablissements',
        sa.Column('phone_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False),
    )
    op.add_column('etablissements',
        sa.Column('website_alternance', mysql.TEXT(collation=u'utf8mb4_unicode_ci'), nullable=False)
    )


def downgrade():
    op.drop_column('etablissements_admin_update', 'phone_alternance')
    op.drop_column('etablissements', 'phone_alternance')

    op.drop_column('etablissements_admin_update', 'website_alternance')
    op.drop_column('etablissements', 'website_alternance')