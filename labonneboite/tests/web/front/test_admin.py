# coding: utf8
from social_flask_sqlalchemy.models import UserSocialAuth

from labonneboite.common.database import db_session
from labonneboite.common.models import User
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect


class AdminTest(DatabaseTest):

    def setUp(self, *args, **kwargs):
        super(AdminTest, self).setUp(*args, **kwargs)

        self.user = User(email='john@doe.com', gender='male', first_name='John', last_name='Doe')
        db_session.add(self.user)
        db_session.flush()

        # Required for `self.logout` to work which looks for the `extra_data` attribute.
        user_social_auth = UserSocialAuth(
            provider=PEAMOpenIdConnect.name,
            extra_data={'id_token': 'fake'},
            user_id=self.user.id,
        )
        db_session.add(user_social_auth)
        db_session.commit()

        self.assertEqual(db_session.query(User).count(), 1)

    def test_admin_access(self):
        """
        Test admin access permissions.
        """

        admin_urls = [
            self.url_for('admin.index'),
            self.url_for('users.index_view'),
            self.url_for('officeadminadd.index_view'),
            self.url_for('officeadminremove.index_view'),
            self.url_for('officeadminupdate.index_view'),
            self.url_for('officeadminextrageolocation.index_view'),
        ]

        with self.test_request_context():

            for url in admin_urls:

                # Access should be denied when a user is not logged in.
                db_session.query(User).update({User.active: True, User.is_admin: False})
                db_session.commit()
                self.user = db_session.query(User).filter_by(id=self.user.id).first()
                self.assertTrue(self.user.active)
                self.assertFalse(self.user.is_admin)
                rv = self.app.get(url)
                self.assertEqual(rv.status_code, 404)

                self.login(self.user)

                # Access should be denied when a user is logged in but is not an admin.
                rv = self.app.get(url)
                self.assertEqual(rv.status_code, 404)

                # Access should be granted when a user is logged in and is admin.
                db_session.query(User).update({User.active: True, User.is_admin: True})
                db_session.commit()
                self.user = db_session.query(User).filter_by(id=self.user.id).first()
                self.assertTrue(self.user.active)
                self.assertTrue(self.user.is_admin)
                rv = self.app.get(url)
                self.assertEqual(rv.status_code, 200)

                # Access should be denied when a user is not active.
                db_session.query(User).update({User.active: False, User.is_admin: True})
                db_session.commit()
                self.user = db_session.query(User).filter_by(id=self.user.id).first()
                self.assertFalse(self.user.active)
                self.assertTrue(self.user.is_admin)
                rv = self.app.get(url)
                self.assertEqual(rv.status_code, 404)

                self.logout()
