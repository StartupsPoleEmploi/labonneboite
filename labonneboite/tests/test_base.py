import logging
import unittest
import pytest
from flask import url_for as flask_url_for
from flask_login import FlaskLoginClient

# from labonneboite.common.database import db_session, delete_db, engine, init_db
from labonneboite.common import env
from labonneboite.common import es
from labonneboite.conf import settings
from labonneboite.web.app import app


class AppTest(unittest.TestCase):
    """
    Sets up the app environment and exposes various methods.

    `self.app_context` is used to reverse URLs (see `self.url_for`). It should be used anywhere
    we need to maintain the same app context. For more info:
    http://flask.pocoo.org/docs/0.12/appcontext/
    https://kronosapiens.github.io/blog/2014/08/14/understanding-contexts-in-flask.html

    `self.test_request_context` stores a `RequestContext` object which should be used anywhere
    we need to fire a `get` or `post` while maintaining the same request context. Everything
    that is called from the same request context will have access to the same request globals:
    http://flask.pocoo.org/docs/0.12/testing/#other-testing-tricks

    `self.app.session_transaction()` can be used to modify sessions:
    http://flask.pocoo.org/docs/0.12/testing/#accessing-and-modifying-sessions
    """

    # sytt: https://github.com/pytest-dev/pytest-mock/issues/174
    @pytest.fixture(autouse=True)
    def __inject_fixtures_forall(self, db_session):
        self.db_session = db_session
        self.es = es.Elasticsearch()
        es.drop_and_create_index()
        self.app = app.test_client()
        self.app_context = app.app_context
        self.test_request_context = app.test_request_context

        self.login_client = app
        self.login_client.test_client_class = FlaskLoginClient

        # Disable logging
        app.logger.setLevel(logging.CRITICAL)

    def setUp(self):
        return super(AppTest, self).setUp()

    def url_for(self, endpoint, **kwargs):
        """
        A small helper to generate a URL to the given endpoint in the context of `self.app_context`.
        """
        with self.app_context():
            url = flask_url_for(endpoint, **kwargs)
            return url


class DatabaseTest(AppTest):
    """
    Configure MySQL and Elasticsearch for unit tests.

    You need to ensure the `LBB_ENV=test` environment variable is set when running tests.
    This will allow SQLAlchemy to use the right database.

    Also note that the MySQL test DB must exists before before using this class.
    On your local machine, it should've been created by the `alembic/sql/test.sql`
    script.
    """

    def setUp(self):
        if env.get_current_env() != env.ENV_TEST:
            raise ValueError("Running database tests, but not in test mode. You"
                             " most certainly don't want to do that. Set the"
                             " `LBB_ENV=test` environment variable.")

        # Disable elasticsearch logging
        logging.getLogger('elasticsearch').setLevel(logging.CRITICAL)
        logging.getLogger('main').setLevel(logging.CRITICAL)

        # Create ES index.
        self.assertIn('test', settings.ES_INDEX)

        return super(DatabaseTest, self).setUp()

    def tearDown(self):

        # Empty ES index.
        es.drop_and_create_index()

        return super(DatabaseTest, self).tearDown()
