import logging
import unittest

from flask import _request_ctx_stack, url_for as flask_url_for

from labonneboite.common import env, es
from labonneboite.common.database import db_session, delete_db, engine, init_db
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

    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context
        self.test_request_context = app.test_request_context
        # Disable logging
        app.logger.setLevel(logging.CRITICAL)

        return super(AppTest, self).setUp()

    def url_for(self, endpoint, **kwargs):
        """
        A small helper to generate a URL to the given endpoint in the context of `self.app_context`.
        """
        with self.app_context():
            url = flask_url_for(endpoint, **kwargs)
            return url

    def login(self, user, social_auth_backend="peam-openidconnect"):
        """
        Logs a user in by simulating a third-party authentication process.

        This method should always be called within the same request context
        as the test that uses it in order to use the same session object:
            with self.test_request_context():
                self.login(user)
                ...
        """
        _request_ctx_stack.top.user = user
        with self.app.session_transaction() as sess:
            # Session info set by Flask-Login.
            sess["user_id"] = user.id
            # Session info set by Python Social Auth.
            sess["social_auth_last_login_backend"] = social_auth_backend
            sess["%s_state" % social_auth_backend] = "a1z2e3r4t5y6y"

    def logout(self):
        """
        Logs a user out.

        This method should always be called within the same request context
        as the test that uses it in order to use the same session object:
            with self.test_request_context():
                ...
                self.logout()
        """
        self.app.get("/authentication/logout")
        del _request_ctx_stack.top.user


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
            raise ValueError(
                "Running database tests, but not in test mode. You"
                " most certainly don't want to do that. Set the"
                " `LBB_ENV=test` environment variable."
            )

        # Disable elasticsearch logging
        logging.getLogger("elasticsearch").setLevel(logging.CRITICAL)
        logging.getLogger("main").setLevel(logging.CRITICAL)

        # Create MySQL tables.
        delete_db()
        init_db()

        # Create ES index.
        self.assertIn("test", settings.ES_INDEX)
        self.es = es.Elasticsearch()
        es.drop_and_create_index()

        return super(DatabaseTest, self).setUp()

    def tearDown(self):
        # Drop MySQL tables.
        db_session.remove()
        engine.dispose()
        delete_db()

        # Empty ES index.
        es.drop_and_create_index()

        return super(DatabaseTest, self).tearDown()
