# http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/#declarative
# http://docs.sqlalchemy.org/en/rel_1_1/
import os
from typing import Optional, Dict, Union, TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from labonneboite.common.conf import settings
from labonneboite.common.env import get_current_env, ENV_TEST

CURRENT_ENV = get_current_env()

# Engine
# -----------------------------------------------------------------------------

DATABASE: Dict[str, Union[str, int, None]] = {
    "HOST": settings.DB_HOST,
    "PORT": settings.DB_PORT,
    "NAME": settings.DB_NAME,
    "USER": settings.DB_USER,
    "PASSWORD": settings.DB_PASSWORD,
}


def get_db_string(db_params: Optional[Dict[str, Union[str, int, None]]] = None) -> str:
    """
    Returns the database URI that should be used for the connection.
    It can be overriden (e.g. in tests) by hardcoding the value of `db_params`.
    The environment variable ENABLE_DB_INFILE may be set to enable `LOAD DATA LOCAL INFILE` SQL instructions
    """
    # Build the connection string
    db_params = db_params or DATABASE
    s = "mysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}?charset=utf8mb4".format(
        **db_params
    )
    # Add the optional param to enable `LOAD DATA LOCAL INFILE` SQL instructions
    s = s + "&local_infile=1" if os.environ.get("ENABLE_DB_INFILE") else s
    print(s, flush=True)
    return s


pool_recycle = int(os.environ.get("DB_CONNECTION_TIMEOUT", "30"))
connect_timeout = int(os.environ.get("CONNECT_TIMEOUT", "5"))

ENGINE_PARAMS = {
    "convert_unicode": True,
    "echo": False,
    "pool_recycle": pool_recycle,
    "connect_args": {"connect_timeout": connect_timeout},
}

engine = create_engine(get_db_string(), **ENGINE_PARAMS)

# Session
# -----------------------------------------------------------------------------

_expire_on_commit = True
if CURRENT_ENV == ENV_TEST:
    # Used in unit tests to avoid a `DetachedInstanceError: Instance <x> is not bound to a Session`.
    # http://www.dangtrinh.com/2014/03/i-got-this-error-when-trying-to.html
    _expire_on_commit = False

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=_expire_on_commit,
    )
)


# Base
# -----------------------------------------------------------------------------

if TYPE_CHECKING:

    class Base(declarative_base()):  # type: ignore
        query = db_session.query_property()

else:
    Base = declarative_base()
    Base.query = db_session.query_property()


def init_db() -> None:
    """
    Convenient method for unit tests to create all tables used in the project.
    """

    # Create LBB tables.
    # Import all models so that metadata can be filled in and SQLAlchemy knows what tables to deal with.
    # pylint:disable=unused-variable
    # pylint:enable=unused-variable
    Base.metadata.create_all(bind=engine)

    # for t in Base.metadata.sorted_tables:
    #     print("created table %s" % t.name)

    # Create social_flask_sqlalchemy tables.
    # pylint:disable=unused-variable
    # Imports are used by SQLAlchemy `metadata.create_all()` to know what tables to create.
    from social_flask_sqlalchemy.models import PSABase
    from social_flask_sqlalchemy.models import Nonce, Association, Code

    # pylint:enable=unused-variable
    # InnoDB has a maximum index length of 767 bytes, so for utf8mb4 we can index a maximum of 191 characters.
    Code.email.property.columns[0].type.length = 191
    Nonce.server_url.property.columns[0].type.length = 191
    Association.server_url.property.columns[0].type.length = 191
    Association.handle.property.columns[0].type.length = 191
    Association.secret.property.columns[0].type.length = 191
    PSABase.metadata.create_all(engine)


def delete_db() -> None:
    """
    Convenient method for unit tests to delete all tables used in the project.
    """

    # Drop social_flask_sqlalchemy tables.
    # pylint:disable=unused-variable
    # Imports are used by SQLAlchemy `metadata.create_all()` to know what tables to create.
    from social_flask_sqlalchemy.models import PSABase

    # pylint:enable=unused-variable
    PSABase.metadata.drop_all(engine)

    # Drop LBB tables.
    # Import all models so that metadata can be filled in and SQLAlchemy knows what tables to deal with.
    # pylint:disable=unused-variable
    # pylint:enable=unused-variable
    # for t in Base.metadata.sorted_tables:
    #     print("drop table %s" % t.name)

    Base.metadata.drop_all(bind=engine)
