
import datetime
import requests
import time

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Unicode
from sqlalchemy import desc
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from flask_login import UserMixin
from social_flask.utils import load_strategy
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.conf import settings
from labonneboite.common.database import Base, db_session
from labonneboite.common.models.base import CRUDMixin
from labonneboite.common import constants


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
        (constants.GENDER_MALE, 'Homme'),
        (constants.GENDER_FEMALE, 'Femme'),
        (constants.GENDER_OTHER, 'Autre'),
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
        self.refresh_peam_access_token_if_needed()
        user_social_auth = get_user_social_auth(self.id)
        peam_access_token = user_social_auth.extra_data['access_token']
        return peam_access_token

    def refresh_peam_access_token_if_needed(self):
        user_social_auth = get_user_social_auth(self.id)
        # FTR there is no extra_data['expires'] nor extra_data['expires_in'] :-(
        token_age_in_seconds = int(time.time()) - user_social_auth.extra_data['auth_time']
        # The PEAMU token is valid for 6 months supposedly.
        # We refresh it no more than once every few hours to avoid flooding the PEAM API with too many requests.
        # This way the user will only get disconnected when he did not use LBB for at least 6 months.
        if token_age_in_seconds >= settings.REFRESH_PEAM_TOKEN_NO_MORE_THAN_ONCE_EVERY_SECONDS:
            try:
                strategy = load_strategy()
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
