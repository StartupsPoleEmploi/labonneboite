"""
Change the `users` table:
- the `email` becomes not nullable (an empty value should be represented by an empty string)
- add an `external_id` field
- add an index on the `email` field

Revision ID: 428e168fdf0c
Revises: 94d10e069fea
Create Date: 2017-06-09 08:22:13.869705
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = '428e168fdf0c'
down_revision = '94d10e069fea'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('users', 'email', nullable=False, existing_type=mysql.VARCHAR(length=255))
    op.add_column('users', sa.Column('external_id', mysql.VARCHAR(length=255), nullable=True))
    op.create_index('_email', 'users', ['email'], unique=False)

def downgrade():
    op.alter_column('users', 'email', nullable=True, existing_type=mysql.VARCHAR(length=255))
    op.drop_column('users', 'external_id')
    op.drop_constraint('_email', 'users', type_='unique')
