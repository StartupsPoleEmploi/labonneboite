"""
SQL optim PE connexion by sreg
Add indexes to the `social_auth_association` table

Revision ID: 6a40b75d390a
Revises: f628f8fac32d
Create Date: 2021-06-03 16:27:50.213192
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '6a40b75d390a'
down_revision = 'f628f8fac32d'
branch_labels = None
depends_on = None


def upgrade():
    # ALTER TABLE labonneboite.social_auth_association ADD INDEX index1(handle);
    op.create_index('handle', 'social_auth_association', ['handle'], unique=False)
    # ALTER TABLE `labonneboite`.`social_auth_usersocialauth` ADD INDEX `provider_uid`(`provider`, `uid`)
    op.create_index('provider_uid', 'social_auth_usersocialauth', ['provider', 'uid'], unique=False)

def downgrade():
    op.drop_constraint('handle', 'social_auth_association', type_='unique')
    op.drop_constraint('provider_uid', 'social_auth_usersocialauth', type_='unique')
