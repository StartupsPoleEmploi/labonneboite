from unittest import mock

from social_flask_sqlalchemy.models import UserSocialAuth

# from labonneboite.common.database import db_session
from labonneboite.common.models import User
from labonneboite.common.models import Office
from labonneboite.common.models import UserFavoriteOffice
from labonneboite.conf import settings
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.web.auth.backends.peam import PEAMOpenIdConnect


class UserAccountTest(DatabaseTest):

    def setUp(self):
        """
        Populate the DB with data required for these tests to work.
        """
        super(UserAccountTest, self).setUp()

        self.user = User(email='john@doe.com', gender='male', first_name='John', last_name='Doe')
        self.db_session.add(self.user)
        self.db_session.flush()

        self.office1 = Office(
            departement='57',
            siret='00000000000001',
            company_name='1',
            headcount='5',
            city_code='57070',
            zipcode='57070',
            naf='4646Z',
            hiring=120,  # aka score 90
            x=6.166667,
            y=49.133333,
        )
        self.office2 = Office(
            departement='57',
            siret='00000000000002',
            company_name='1',
            headcount='5',
            city_code='57070',
            zipcode='57070',
            naf='4646Z',
            hiring=120,  # aka score 90
            x=6.166667,
            y=49.133333,
        )
        self.db_session.add_all([self.office1, self.office2])
        self.db_session.flush()

        self.user_social_auth = UserSocialAuth(
            provider=PEAMOpenIdConnect.name,
            extra_data={'id_token': 'fake'},
            user_id=self.user.id,
        )
        self.fav1 = UserFavoriteOffice(user_id=self.user.id, office_siret=self.office1.siret)
        self.fav2 = UserFavoriteOffice(user_id=self.user.id, office_siret=self.office2.siret)
        self.db_session.add_all([self.user_social_auth, self.fav1, self.fav2])
        self.db_session.flush()

        self.db_session.commit()

        self.assertEqual(self.db_session.query(User).count(), 1)
        self.assertEqual(self.db_session.query(Office).count(), 2)
        self.assertEqual(self.db_session.query(UserFavoriteOffice).count(), 2)
        self.assertEqual(self.db_session.query(UserSocialAuth).count(), 1)

    def test_download_user_personal_data(self):
        """
        Test the download of personal data.
        """

        url = self.url_for('user.personal_data_as_csv')

        with self.login_client.test_client(user=self.user) as client:

            # Display the account deletion confirmation page.
            rv = client.get(url)
            self.assertEqual(rv.status_code, 200)
            self.assertIn('john@doe.com', rv.data.decode('utf-8'))

    @mock.patch.object(settings, 'PEAM_AUTH_BASE_URL', 'http://peamauthbaseurl.com')
    def test_delete_user_account(self):
        """
        Test the deletion of a user account.
        """

        url = self.url_for('user.account_delete')

        with self.login_client.test_client(user=self.user) as client:

            # Display the account deletion confirmation page.
            with client.session_transaction() as sess:
                # Session info set by Python Social Auth.
                sess['social_auth_last_login_backend'] = 'peam-openidconnect'
                sess['%s_state' % 'peam-openidconnect'] = 'a1z2e3r4t5y6y'

            rv = client.get(url)
            self.assertEqual(rv.status_code, 200)

            # Confirm account deletion.
            rv = client.post(url, data={'confirm_deletion': 1})
            # The user should be redirected to the PEAM logout endpoint.
            self.assertEqual(rv.status_code, 302)
            self.assertIn(settings.PEAM_AUTH_BASE_URL, rv.location)
            self.assertIn(self.user_social_auth.extra_data['id_token'], rv.location)

            # The user and its info should have been deleted.
            self.assertEqual(db_session.query(User).count(), 0)
            self.assertEqual(db_session.query(UserFavoriteOffice).count(), 0)
            self.assertEqual(db_session.query(UserSocialAuth).count(), 0)

            # The user should now be anonymous and cannot access protected pages.
            rv = client.get(url)
            self.assertEqual(rv.status_code, 401)
