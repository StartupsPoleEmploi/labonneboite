"""
replace_score_by_hiring

Revision ID: 66af73e521cb
Revises: 78df44030210
Create Date: 2022-06-27 11:56:30.828436
"""
import math

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import TableClause

from labonneboite.conf import settings

# Revision identifiers, used by Alembic.
revision = '66af73e521cb'
down_revision = '78df44030210'
branch_labels = None
depends_on = None


def create_table(name: str) -> TableClause:
    return sa.table(
        name,
        sa.Column('score', mysql.INTEGER(display_width=11), default=0, nullable=False, server_default='0'),
        sa.Column('hiring', mysql.INTEGER(display_width=11), default=0, nullable=False, server_default='0')
    )


office = create_table('etablissements')
office_admin_add = create_table('etablissements_admin_add')
office_admin_update = create_table('etablissements_admin_update')
office_third_party_update = create_table('etablissements_third_party_update')


# source:
# https://github.com/StartupsPoleEmploi/labonneboite/blob/310c2dbbfdced92c25bbdb4c842d4fe303f2ea88/labonneboite/common/scoring.py#L118-L134
def upgrade_table(table: TableClause) -> None:
    hiring_0_50 = settings.SCORE_50_HIRINGS * table.c.score / 50.0
    hiring_50_60 = (settings.SCORE_50_HIRINGS + (table.c.score - 50) / 10.0 * (
            settings.SCORE_60_HIRINGS - settings.SCORE_50_HIRINGS))
    hiring_60_80 = (settings.SCORE_60_HIRINGS + (table.c.score - 60) / 20.0 * (
            settings.SCORE_80_HIRINGS - settings.SCORE_60_HIRINGS))
    hiring_80_100 = (-1 + settings.SCORE_80_HIRINGS + sa.func.pow(10.0, (
            (table.c.score - 80) / 20.0 * math.log10(settings.SCORE_100_HIRINGS))))

    hiring_conditions = sa.func.IF(
        table.c.score <= 50,
        hiring_0_50,
        sa.func.IF(table.c.score <= 60,
                   hiring_50_60,
                   sa.func.IF(table.c.score <= 80,
                              hiring_60_80,
                              hiring_80_100)
                   )
    )

    op.add_column(table.name, table.c.hiring.copy())
    op.execute(
        table.update()
        .where(table.c.score <= 100)
        .values({
            'hiring': hiring_conditions
        })
    )
    op.drop_column(table.name, table.c.score.name)


def downgrade_table(table: TableClause) -> None:
    score_0_50 = 0.0 + 50 * (table.c.hiring - 0.0) / (settings.SCORE_50_HIRINGS - 0.0)
    score_100 = 100.0
    score_50_60 = (50.0 + 10 * (table.c.hiring - settings.SCORE_50_HIRINGS) /
                   (settings.SCORE_60_HIRINGS - settings.SCORE_50_HIRINGS))
    score_60_80 = (60.0 + 20 * (table.c.hiring - settings.SCORE_60_HIRINGS) /
                   (settings.SCORE_80_HIRINGS - settings.SCORE_60_HIRINGS))
    score_80_100 = 80.0 + 20.0 / math.log10(settings.SCORE_100_HIRINGS) * sa.func.log10(
        1 + table.c.hiring - settings.SCORE_80_HIRINGS)

    score_conditions = sa.func.IF(
        table.c.hiring <= settings.SCORE_50_HIRINGS,
        score_0_50,
        sa.func.IF(table.c.hiring <= settings.SCORE_60_HIRINGS,
                   score_50_60,
                   sa.func.IF(table.c.hiring <= settings.SCORE_80_HIRINGS,
                              score_60_80,
                              sa.func.IF(table.c.hiring <= settings.SCORE_100_HIRINGS,
                                         score_80_100,
                                         score_100,
                                         ))))

    op.add_column(table.name, table.c.score.copy())
    op.execute(
        table.update()
        .values({
            'score': score_conditions
        })
    )
    op.drop_column(table.name, table.c.hiring.name)


def upgrade() -> None:
    upgrade_table(office)
    upgrade_table(office_admin_add)
    upgrade_table(office_admin_update)
    upgrade_table(office_third_party_update)


def downgrade() -> None:
    downgrade_table(office_third_party_update)
    downgrade_table(office_admin_update)
    downgrade_table(office_admin_add)
    downgrade_table(office)
