"""
deduplicate users

Revision ID: c519ecaf1fa6
Revises: a6ff4a27b063
Create Date: 2018-09-26 16:45:13.810694
"""
# from alembic import op

import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'c519ecaf1fa6'
down_revision = 'a6ff4a27b063'
branch_labels = None
depends_on = None


def upgrade():
    try:
        deduplicate_users()
    except KeyboardInterrupt:
        pass

def downgrade():
    # This migration can be run as many times as we need: just rollback
    # (alembic downgrade -1) and re-apply (alembic upgrade HEAD).
    pass

def deduplicate_users():
    # We import the app to initialize the social models
    import labonneboite.web.app # pylint: disable=unused-import,unused-variable
    from labonneboite.common.database import db_session
    from labonneboite.common.models import auth
    from labonneboite.common.models.user_favorite_offices import UserFavoriteOffice


    # Iterate on duplicated users
    for user in auth.User.query.group_by('external_id').having(sa.func.count(auth.User.external_id) > 1):
        duplicate_user_ids = []
        favorite_count = 0
        # Create favorites, if necessary
        for duplicate_user in auth.User.query.filter(auth.User.external_id == user.external_id, auth.User.id != user.id):
            duplicate_user_ids.append(duplicate_user.id)
            for favorite in duplicate_user.favorite_offices:
                _, created = UserFavoriteOffice.get_or_create(user_id=user.id, office_siret=favorite.office_siret)
                if created:
                    favorite_count += 1

        print("Removing {} duplicates for user #{} ({} favorite added to original user)".format(len(duplicate_user_ids), user.id, favorite_count))
        # Remove duplicate social user
        db_session.query(auth.UserSocialAuth).filter(auth.UserSocialAuth.user_id.in_(duplicate_user_ids)).delete(synchronize_session=False)
        # Remove duplicate user
        auth.User.query.filter(auth.User.id.in_(duplicate_user_ids)).delete(synchronize_session=False)
