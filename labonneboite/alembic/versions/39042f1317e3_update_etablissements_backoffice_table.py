"""
update etablissements_backoffice table

Revision ID: 39042f1317e3
Revises: 47a2a34d87e5
Create Date: 2018-04-18 14:30:00.654100
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql


# Revision identifiers, used by Alembic.
revision = "39042f1317e3"
down_revision = "47a2a34d87e5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("etablissements_backoffice", "semester-1")
    op.drop_column("etablissements_backoffice", "semester-2")
    op.drop_column("etablissements_backoffice", "semester-3")
    op.drop_column("etablissements_backoffice", "semester-4")
    op.drop_column("etablissements_backoffice", "semester-5")
    op.drop_column("etablissements_backoffice", "semester-6")
    op.drop_column("etablissements_backoffice", "semester-7")

    op.add_column("etablissements_backoffice", sa.Column("dpae-period-7", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("dpae-period-6", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("dpae-period-5", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("dpae-period-4", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("dpae-period-3", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("dpae-period-2", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("dpae-period-1", mysql.DOUBLE(asdecimal=True), nullable=True))

    op.add_column(
        "etablissements_backoffice",
        sa.Column("score_alternance", mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    )
    op.add_column("etablissements_backoffice", sa.Column("score_alternance_regr", mysql.FLOAT(), nullable=True))

    op.add_column("etablissements_backoffice", sa.Column("alt-period-7", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("alt-period-6", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("alt-period-5", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("alt-period-4", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("alt-period-3", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("alt-period-2", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("alt-period-1", mysql.DOUBLE(asdecimal=True), nullable=True))


def downgrade():
    op.add_column("etablissements_backoffice", sa.Column("semester-1", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("semester-2", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("semester-3", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("semester-4", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("semester-5", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("semester-6", mysql.DOUBLE(asdecimal=True), nullable=True))
    op.add_column("etablissements_backoffice", sa.Column("semester-7", mysql.DOUBLE(asdecimal=True), nullable=True))

    op.drop_column("etablissements_backoffice", "dpae-period-7")
    op.drop_column("etablissements_backoffice", "dpae-period-6")
    op.drop_column("etablissements_backoffice", "dpae-period-5")
    op.drop_column("etablissements_backoffice", "dpae-period-4")
    op.drop_column("etablissements_backoffice", "dpae-period-3")
    op.drop_column("etablissements_backoffice", "dpae-period-2")
    op.drop_column("etablissements_backoffice", "dpae-period-1")

    op.drop_column("etablissements_backoffice", "score_alternance")
    op.drop_column("etablissements_backoffice", "score_alternance_regr")

    op.drop_column("etablissements_backoffice", "alt-period-7")
    op.drop_column("etablissements_backoffice", "alt-period-6")
    op.drop_column("etablissements_backoffice", "alt-period-5")
    op.drop_column("etablissements_backoffice", "alt-period-4")
    op.drop_column("etablissements_backoffice", "alt-period-3")
    op.drop_column("etablissements_backoffice", "alt-period-2")
    op.drop_column("etablissements_backoffice", "alt-period-1")
