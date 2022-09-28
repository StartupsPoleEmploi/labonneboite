import os
from packaging import version
import sqlalchemy as sa
import contextlib
import pytest

from flask_sqlalchemy import SQLAlchemy


from labonneboite.common.database import get_db_string


@pytest.fixture(scope='module')
def _db():
    '''
    Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
    database connection.
    '''
    # from labonneboite.common.database import engine
    # return Session(engine)
    from labonneboite.web.app import app
    myapp = app
    myapp.config['SQLALCHEMY_DATABASE_URI'] = get_db_string()

    return SQLAlchemy(app=app)

# Automatically enable transactions for all tests, without importing any extra fixtures.


@pytest.fixture(autouse=True)
def enable_transactional_tests(db_session):
    pass

# write demo data here
