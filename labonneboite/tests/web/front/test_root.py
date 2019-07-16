from unittest import mock

from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common import pro
from labonneboite.common.models import User

class RootTest(DatabaseTest):

    def login_as_pro(self):
        user_pro = User.create(email='x@pole-emploi.fr', gender='male', first_name='John', last_name='Doe')
        self.login(user_pro)
        self.assertTrue(pro.user_is_pro())
        self.assertFalse(pro.pro_version_enabled())

    def test_no_kit_if_public_user(self):
        rv = self.app.get(self.url_for('root.kit'))
        self.assertEqual(rv.status_code, 404)

    @mock.patch('labonneboite.conf.settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES', ['@pole-emploi.fr'])
    def test_no_kit_if_pro_but_not_enabled(self):
        with self.test_request_context():
            self.login_as_pro()

            rv = self.app.get(self.url_for('root.kit'))
            self.assertEqual(rv.status_code, 404)

    @mock.patch('labonneboite.conf.settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES', ['@pole-emploi.fr'])
    def test_kit_if_pro_and_enabled(self):
        with self.test_request_context():
            self.login_as_pro()

            # enable pro version
            with self.app.session_transaction() as sess:
                sess[pro.PRO_VERSION_SESSION_KEY] = True

            # Non-empty pdf file
            rv = self.app.get(self.url_for('root.kit'))
            self.assertEqual(rv.status_code, 200)
            self.assertEqual('application/pdf', rv.content_type)
            self.assertLess(1000, rv.content_length)
