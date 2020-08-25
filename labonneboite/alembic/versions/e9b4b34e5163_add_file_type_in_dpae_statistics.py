"""
Add file_type in dpae statistics

Revision ID: e9b4b34e5163
Revises: eeee4b88f161
Create Date: 2020-08-21 10:09:23.233281
"""
from alembic import op
from sqlalchemy.dialects import mysql
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'e9b4b34e5163'
down_revision = 'eeee4b88f161'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'dpae_statistics',
        sa.Column('file_type', mysql.INTEGER(), autoincrement=False, nullable=True, default=1)
    )
    
    connection = op.get_bind()
    for dpae_stat in connection.execute('select id from dpae_statistics'):
        #Set all previous import to dpae type
        connection.execute(f"update dpae_statistics set file_type = 1 where id = {dpae_stat[0]}")

    #set last import for app and contrat pro to the last date in database
    connection.execute("INSERT INTO dpae_statistics (last_import, most_recent_data_date, file_type) \
                        VALUES('2017-12-31 00:00:00','2017-12-31 00:00:00', 2), \
                        ('2017-12-30 00:00:00','2017-12-30 00:00:00', 3);")


def downgrade():
    op.drop_column('dpae_statistics', 'file_type')
