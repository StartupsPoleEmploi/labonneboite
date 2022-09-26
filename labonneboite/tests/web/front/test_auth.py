import urllib.parse

from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import db_session
from labonneboite.common.models import get_user_social_auth, User
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.app import app
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect
from labonneboite.web.auth import utils as auth_utils


class AuthTest(DatabaseTest):

    def test_logout(self):
        """
        Test that the session is cleaned after a logout.
        """

        user = User(email='j@test.com', gender='male', first_name='John', last_name='Doe')
        db_session.add(user)
        db_session.flush()

        # This `UserSocialAuth` entry will be required later by the logout function.
        user_social_auth = UserSocialAuth(
            provider=PEAMOpenIdConnect.name,
            extra_data={'id_token': 'fake'},
            user_id=user.id,
        )
        db_session.add(user_social_auth)
        db_session.commit()

        with self.login_client.test_client(user=user) as client:

            with client.session_transaction() as sess:
                sess['this_should_not_be_deleted'] = 'foo'  # This should not be deleted by a login or logout.

            with client.session_transaction() as sess:
                social_auth_backend = 'peam-openidconnect'
                # Session info set by Flask-Login.
                sess['_user_id'] = user.id
                # Session info set by Python Social Auth.
                sess['social_auth_last_login_backend'] = social_auth_backend
                sess['%s_state' % social_auth_backend] = 'a1z2e3r4t5y6y'

            with client.session_transaction() as sess:
                self.assertIn('this_should_not_be_deleted', sess)
                self.assertIn('_user_id', sess)
                self.assertIn('social_auth_last_login_backend', sess)
                self.assertIn('peam-openidconnect_state', sess)

            client.get('/authentication/logout')

            with client.session_transaction() as sess:
                self.assertIn('this_should_not_be_deleted', sess)
                self.assertNotIn('_user_id', sess)
                self.assertNotIn('social_auth_last_login_backend', sess)
                self.assertNotIn('peam-openidconnect_state', sess)

    def test_get_user_social_auth(self):
        """
        Test the `get_user_social_auth()` function.
        """
        user = User(email='john@doe.com', gender='male', first_name='John', last_name='Doe')
        db_session.add(user)
        db_session.flush()

        expected_user_social_auth = UserSocialAuth(provider=PEAMOpenIdConnect.name, extra_data=None, user_id=user.id)
        db_session.add(expected_user_social_auth)
        db_session.flush()

        db_session.commit()

        self.assertEqual(db_session.query(User).count(), 1)
        self.assertEqual(db_session.query(UserSocialAuth).count(), 1)

        user_social_auth = get_user_social_auth(user.id)
        self.assertEqual(user_social_auth.id, expected_user_social_auth.id)

    def test_login_url(self):
        with self.app_context():
            login_url = auth_utils.login_url()

        parsed = urllib.parse.urlsplit(login_url)
        querystring = urllib.parse.parse_qs(parsed.query)
        self.assertIsNotNone(login_url)
        self.assertEqual(['1'], querystring['keep'])
        self.assertNotIn('next', querystring)

    def test_login_url_with_next(self):
        next_url = 'http://infinityandbeyond.com/subpath?arg=value'
        with self.app_context():
            login_url = auth_utils.login_url(next_url=next_url)

        parsed = urllib.parse.urlsplit(login_url)
        querystring = urllib.parse.parse_qs(parsed.query)
        self.assertEqual([next_url], querystring['next'])

    def test_login_url_with_request(self):
        with app.test_request_context(path='/pioupiou', base_url='http://laser.com'):
            login_url = auth_utils.login_url()

        parsed = urllib.parse.urlsplit(login_url)
        querystring = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(['http://laser.com/pioupiou'], querystring['next'])
