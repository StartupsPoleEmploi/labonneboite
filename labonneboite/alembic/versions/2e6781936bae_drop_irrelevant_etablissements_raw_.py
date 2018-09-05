"""
drop irrelevant etablissements_raw columns

Revision ID: 2e6781936bae
Revises: d441dca1e974
Create Date: 2018-08-23 17:14:11.736661
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '2e6781936bae'
down_revision = '0da6b26c212f'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('etablissements_raw', 'phone_alternance')
    op.drop_column('etablissements_raw', 'website_alternance')
    op.drop_column('etablissements_raw', 'social_network')
    op.drop_column('etablissements_raw', 'email_alternance')
    op.drop_column('etablissements_raw', 'contact_mode')


def downgrade():
    op.add_column('etablissements_raw', sa.Column('phone_alternance', mysql.TINYTEXT, nullable=True))
    op.add_column('etablissements_raw', sa.Column('website_alternance', mysql.TINYTEXT, nullable=True))
    op.add_column('etablissements_raw',
        sa.Column('social_network', mysql.TINYTEXT(), nullable=True))
    op.add_column('etablissements_raw',
        sa.Column('email_alternance', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False))
    op.add_column('etablissements_raw',
        sa.Column('contact_mode', mysql.TINYTEXT(), nullable=True))
