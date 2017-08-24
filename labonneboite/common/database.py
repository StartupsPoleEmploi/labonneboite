# coding: utf8

# http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/#declarative
# http://docs.sqlalchemy.org/en/rel_1_1/

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from labonneboite.conf import get_current_env, settings, ENV_DEVELOPMENT, ENV_TEST


CURRENT_ENV = get_current_env()

# Engine
# -----------------------------------------------------------------------------

TEST_DATABASE = {
    'NAME': 'lbb_test2',
    'PASSWORD': 'lbb_test',
    'USER': 'lbb_test',
}

REAL_DATABASE = {
    'NAME': settings.DB,
    'PASSWORD': settings.PASSWORD,
    'USER': settings.USER,
}

DATABASE = TEST_DATABASE if CURRENT_ENV == ENV_TEST else REAL_DATABASE

def get_db_string(db_params=DATABASE):
    """
    Returns the database URI that should be used for the connection.
    It can be overriden (e.g. in tests) by hardcoding the value of `db_params`.
    """
    return "mysql://%s:%s@localhost/%s?charset=utf8mb4" % (db_params['USER'], db_params['PASSWORD'], db_params['NAME'])

ENGINE_PARAMS = {
    'convert_unicode': True,
    'echo': True if CURRENT_ENV == ENV_DEVELOPMENT else False,  # Output all SQL statements in console in dev mode.
    'pool_recycle': 280,
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


def init_db():
    """
    Convenient method for unit tests to create all tables used in the project.
    """

    # Create LBB tables.
    # Import all models so that metadata can be filled in and SQLAlchemy knows what tables to deal with.
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
    # Import all models so that metadata can be filled in and SQLAlchemy knows what tables to deal with.
    # pylint:disable=unused-variable
    from labonneboite.common import models
    # pylint:enable=unused-variable
    # for t in Base.metadata.sorted_tables:
    #     print("drop table %s" % t.name)

    Base.metadata.drop_all(bind=engine)
