import pytest
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture(scope='session')
def _db():
    '''
    Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
    database connection.
    '''
    from labonneboite.web.app import app
    from labonneboite.common.database import get_db_string
    myapp = app
    myapp.config['SQLALCHEMY_DATABASE_URI'] = get_db_string()

    return SQLAlchemy(app=app)
