
import datetime
import requests

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Unicode
from sqlalchemy import desc
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from flask_login import UserMixin
from social_flask.utils import load_strategy
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import Base, db_session
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common import user_util


class TokenRefreshFailure(Exception):
    pass


class User(CRUDMixin, UserMixin, Base):
    """
    A user.

    UserMixin provides default implementations for the methods that Flask-Login
    expects user objects to have.
    """

    __tablename__ = 'users'

    GENDERS = [
        (user_util.GENDER_MALE, 'Homme'),
        (user_util.GENDER_FEMALE, 'Femme'),
        (user_util.GENDER_OTHER, 'Autre'),
    ]

    id = Column(Integer, primary_key=True)
    # E-mail may not be unique or may not be available for some third party auth providers, e.g. `PEAM/PE Connect`.
    # Set nullable=False because empty values should be represented by empty strings so that
    # legacy code that assume that `email` is always available as a string will not break.
    email = Column(String(191), nullable=False, index=True)
    gender = Column(ChoiceType(GENDERS))
    first_name = Column(Unicode(191))
    last_name = Column(Unicode(191))
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    # The ID used by third party auth providers (if available).
    external_id = Column(String(191), nullable=True)
    favorite_offices = relationship('UserFavoriteOffice', order_by=desc('date_created'))
    # Designates whether this user can access the admin site.
    is_admin = Column(Boolean, default=False)

    def __unicode__(self):
        return self.email

    def is_active(self):
        return self.active

    def get_peam_access_token(self):
        self.refresh_peam_access_token()
        user_social_auth = get_user_social_auth(self.id)
        peam_access_token = user_social_auth.extra_data['access_token']
        return peam_access_token

    def refresh_peam_access_token(self):
        user_social_auth = get_user_social_auth(self.id)
        strategy = load_strategy()
        # FIXME waiting for ESD approval
        # FIXME refresh only if older than X minutes
        # FTR there is no extra_data['expires'] nor extra_data['expires_in'] :-(
        # pp social.extra_data['auth_time'], int(time.time())
        # social.refresh_token(strategy)
        # pp social.extra_data['auth_time'], int(time.time())

        # ipdb> pp user_social_auth.extra_data
        # {'access_token': 'b3ad2afb-ce83-4834-aac2-8fa9d7c228cb',
        #  'auth_time': 1567775007,
        #  'id': '2bd4848d-a903-4afe-9756-2cdfb1eb773c',
        #  'id_token': 'eyJ0eXAiOiJXXXXXXXXXXXXXXX',
        #  'refresh_token': 'f5e1c77e-ebc9-4ca2-a168-1f79a12cd7d6',
        #  'token_type': 'Bearer'}
        try:
            user_social_auth.refresh_token(strategy)
        except requests.HTTPError as e:
            if e.response.status_code == 400:
                raise TokenRefreshFailure
            raise


def get_user_social_auth(user_id):
    """
    Return the latest `UserSocialAuth` instance for the given `user_id`.
    """
    return (
        db_session.query(UserSocialAuth)
        .filter_by(user_id=user_id)
        .order_by(desc(UserSocialAuth.id))
        .first()
    )


def find_user(strategy, details, backend, *args, user=None, **kwargs):
    """
    Function designed to be inserted just before replace
    social_core.pipeline.user.create_user in the social pipeline. We need to
    search for existing users because we have 2 different authentication
    backends. If we don't find the user before we call the create_user
    function, each backend will create a new user. Thus, a single user may be
    subscribed twice, with different favorites.
    """
    user = user or User.query.filter_by(external_id=details.get('external_id')).first()
    return {
        'user': user
    }
