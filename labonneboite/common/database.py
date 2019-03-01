# coding: utf8

# http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/#declarative
# http://docs.sqlalchemy.org/en/rel_1_1/
import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from labonneboite.conf import settings
from labonneboite.common.env import get_current_env, ENV_DEVELOPMENT, ENV_TEST


CURRENT_ENV = get_current_env()

# Engine
# -----------------------------------------------------------------------------

DATABASE = {
    'HOST': settings.DB_HOST,
    'PORT': settings.DB_PORT,
    'NAME': settings.DB_NAME,
    'USER': settings.DB_USER,
    'PASSWORD': settings.DB_PASSWORD,
}

def get_db_string(db_params=None):
    """
    Returns the database URI that should be used for the connection.
    It can be overriden (e.g. in tests) by hardcoding the value of `db_params`.
    """
    db_params = db_params or DATABASE
    return "mysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}?charset=utf8mb4".format(**db_params)

ENGINE_PARAMS = {
    'convert_unicode': True,
    'echo': False,
    'pool_recycle': 30,
}

engine = create_engine(get_db_string(), **ENGINE_PARAMS)

# Session
# -----------------------------------------------------------------------------

SESSIONMAKER_PARAMS = {
    'autocommit': False,
    'autoflush': False,
    'bind': engine,
}

if CURRENT_ENV == ENV_TEST:
    # Used in unit tests to avoid a `DetachedInstanceError: Instance <x> is not bound to a Session`.
    # http://www.dangtrinh.com/2014/03/i-got-this-error-when-trying-to.html
    SESSIONMAKER_PARAMS['expire_on_commit'] = False

db_session = scoped_session(sessionmaker(**SESSIONMAKER_PARAMS))

# Base
# -----------------------------------------------------------------------------

Base = declarative_base()
Base.query = db_session.query_property()


def get_dedicated_session():
    """
    Get a fresh new db connection, useful in very long scripts (importer...)
    where you risk getting a "MySQL server has gone away" error because
    the main db session was unused for too long.
    """
    return scoped_session(sessionmaker(**SESSIONMAKER_PARAMS))


def init_db():
    """
    Convenient method for unit tests to create all tables used in the project.
    """

    # Create LBB tables.
    # Import all models so that metadata can be filled in and SQLAlchemy knows what tables to deal with.
    # FIXME import importer models as well !?
    # pylint:disable=unused-variable
    from labonneboite.common import models
    # pylint:enable=unused-variable
    Base.metadata.create_all(bind=engine)

    # for t in Base.metadata.sorted_tables:
    #     print("created table %s" % t.name)

    # Create social_flask_sqlalchemy tables.
    # pylint:disable=unused-variable
    # Imports are used by SQLAlchemy `metadata.create_all()` to know what tables to create.
    from social_flask_sqlalchemy.models import PSABase
    from social_flask_sqlalchemy.models import UserSocialAuth, Nonce, Association, Code, Partial
    # pylint:enable=unused-variable
    # InnoDB has a maximum index length of 767 bytes, so for utf8mb4 we can index a maximum of 191 characters.
    Code.email.property.columns[0].type.length = 191
    Nonce.server_url.property.columns[0].type.length = 191
    Association.server_url.property.columns[0].type.length = 191
    Association.handle.property.columns[0].type.length = 191
    Association.secret.property.columns[0].type.length = 191
    PSABase.metadata.create_all(engine)


def delete_db():
    """
    Convenient method for unit tests to delete all tables used in the project.
    """

    # Drop social_flask_sqlalchemy tables.
    # pylint:disable=unused-variable
    # Imports are used by SQLAlchemy `metadata.create_all()` to know what tables to create.
    from social_flask_sqlalchemy.models import PSABase
    from social_flask_sqlalchemy.models import UserSocialAuth, Nonce, Association, Code, Partial
    # pylint:enable=unused-variable
    PSABase.metadata.drop_all(engine)

    # Drop LBB tables.
    # FIXME drop importer tables as well !?
    # Import all models so that metadata can be filled in and SQLAlchemy knows what tables to deal with.
    # pylint:disable=unused-variable
    from labonneboite.common import models
    # pylint:enable=unused-variable
    # for t in Base.metadata.sorted_tables:
    #     print("drop table %s" % t.name)

    Base.metadata.drop_all(bind=engine)
