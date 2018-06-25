# coding: utf8
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import db_session
from labonneboite.common.models import get_user_social_auth, User
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect


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

        with self.test_request_context:

            with self.app.session_transaction() as sess:
                sess['this_should_not_be_deleted'] = 'foo'  # This should not be deleted by a login or logout.

            self.login(user)

            with self.app.session_transaction() as sess:
                self.assertIn('this_should_not_be_deleted', sess)
                self.assertIn('user_id', sess)
                self.assertIn('social_auth_last_login_backend', sess)
                self.assertIn('peam-openidconnect_state', sess)

            self.logout()

            with self.app.session_transaction() as sess:
                self.assertIn('this_should_not_be_deleted', sess)
                self.assertNotIn('user_id', sess)
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
