# coding: utf8

import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Unicode
from sqlalchemy import desc
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ChoiceType

from flask_login import UserMixin
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import Base, db_session
from labonneboite.common.models.base import CRUDMixin
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect


class User(CRUDMixin, UserMixin, Base):
    """
    A user.

    UserMixin provides default implementations for the methods that Flask-Login
    expects user objects to have.
    """

    __tablename__ = 'users'

    GENDERS = [
        (u'male', u'Homme'),
        (u'female', u'Femme'),
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


def get_user_social_auth(user_id, provider=PEAMOpenIdConnect.name):
    """
    Return the latest `UserSocialAuth` instance for the given `user_id` and `provider`.
    """
    return (
        db_session.query(UserSocialAuth)
        .filter_by(user_id=user_id, provider=provider)
        .order_by(desc(UserSocialAuth.id))
        .first()
    )
