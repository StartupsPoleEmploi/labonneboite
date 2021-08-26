"""
Create third party admin/SAVE table

Revision ID: 29cdae903fb3
Revises: 2271209bf40f
Create Date: 2021-08-13 10:24:00.611107
"""
from alembic import op

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# Revision identifiers, used by Alembic.
revision = '29cdae903fb3'
down_revision = '2271209bf40f'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('etablissements_third_party_update',
        sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),

        sa.Column('certified_recruiter', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        sa.Column('contact_mode', mysql.TINYTEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('romes_to_remove', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('remove_website', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('new_phone', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('score', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('social_network', mysql.TINYTEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('date_created', mysql.DATETIME(), nullable=False),
        sa.Column('remove_phone', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('romes_to_boost', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('requested_by_phone', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('romes_alternance_to_remove', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('remove_email', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
        sa.Column('score_alternance', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
        sa.Column('new_office_name', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('requested_by_first_name', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('email_alternance', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('name', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('phone_alternance', mysql.TINYTEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('boost_alternance', mysql.TINYINT(display_width=1), server_default=sa.text("'0'"), autoincrement=False, nullable=False),
        sa.Column('reason', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('requested_by_email', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('nafs_to_add', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('sirets', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('new_company_name', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('romes_alternance_to_boost', mysql.TEXT(collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('date_updated', mysql.DATETIME(), nullable=True),
        sa.Column('requested_by_last_name', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('recruiter_uid', mysql.TINYTEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('website_alternance', mysql.TINYTEXT(collation='utf8mb4_unicode_ci'), nullable=True),
        sa.Column('new_email', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False),
        sa.Column('boost', mysql.TINYINT(display_width=1), server_default=sa.text("'0'"), autoincrement=False, nullable=False),
        sa.Column('new_website', mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=191), nullable=False)
        )
    #op.drop_constraint(None, 'etablissements_third_party_update', type_='foreignkey')

    # op.execute("""
    #     CREATE TABLE `etablissements_third_party_update` (
    #             `id` int(11) NOT NULL AUTO_INCREMENT,
    #             `sirets` text COLLATE utf8mb4_unicode_ci,
    #             `name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `new_email` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `new_phone` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `new_website` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `remove_email` tinyint(1) NOT NULL,
    #             `remove_phone` tinyint(1) NOT NULL,
    #             `remove_website` tinyint(1) NOT NULL,
    #             `requested_by_email` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `requested_by_first_name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `requested_by_last_name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `requested_by_phone` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `date_created` datetime NOT NULL,
    #             `date_updated` datetime DEFAULT NULL,
    #             `reason` text COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `romes_to_boost` text COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `boost` tinyint(1) NOT NULL DEFAULT '0',
    #             `romes_to_remove` text COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `nafs_to_add` text COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `email_alternance` text COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
    #             `romes_alternance_to_boost` text COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `boost_alternance` tinyint(1) NOT NULL DEFAULT '0',
    #             `romes_alternance_to_remove` text COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `score` int(11) DEFAULT NULL,
    #             `score_alternance` int(11) DEFAULT NULL,
    #             `social_network` tinytext COLLATE utf8mb4_unicode_ci,
    #             `phone_alternance` tinytext COLLATE utf8mb4_unicode_ci,
    #             `website_alternance` tinytext COLLATE utf8mb4_unicode_ci,
    #             `contact_mode` tinytext COLLATE utf8mb4_unicode_ci,
    #             `certified_recruiter` tinyint(1) DEFAULT NULL,
    #             `recruiter_uid` tinytext COLLATE utf8mb4_unicode_ci,
    #             `new_company_name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             `new_office_name` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
    #             PRIMARY KEY (`id`)
    #             ) ENGINE=InnoDB AUTO_INCREMENT=4079593 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    # """)

def downgrade():
    op.drop_table('etablissements_third_party_update')
