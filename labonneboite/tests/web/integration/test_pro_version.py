# coding: utf8
from urllib import urlencode

from labonneboite.common import util
from labonneboite.common.models import User
from labonneboite.conf import settings
from labonneboite.tests.test_base import DatabaseTest


class ProVersionTest(DatabaseTest):

    def test_user_is_pro(self):
        """
        Test that the Pro user is correctly detected in various cases.

        Note : A pro user can be defined by his IP address too but it's not possible to test.
        So, only tests by email are provided
        """
        self.assertIn('@pole-emploi.fr', settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES)

        user_pro = User.create(email=u'john.doe@pole-emploi.fr', gender=u'male', first_name=u'John', last_name=u'Doe')
        user_public = User.create(email=u'john.doe@gmail.com', gender=u'male', first_name=u'John', last_name=u'Doe')

        with self.test_request_context:
            # User which is not logged in should not be considered a pro user.
            self.assertFalse(util.user_is_pro())

            # User with a pro email should be considered as a pro user.
            self.login(user_pro)
            self.assertTrue(util.user_is_pro())
            self.logout()
            self.assertFalse(util.user_is_pro())

            # User with a non pro email should not be considered a pro user.
            self.login(user_public)
            self.assertFalse(util.user_is_pro())
            self.logout()
            self.assertFalse(util.user_is_pro())

    def test_enable_disable_pro_version_view(self):
        """
        Test that the Pro Version is correctly enabled/disabled.
        """
        self.assertIn('@pole-emploi.fr', settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES)

        # Create a user.
        user_pro = User.create(email=u'x@pole-emploi.fr', gender=u'male', first_name=u'John', last_name=u'Doe')

        next_url = u'http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0&f_a=0'
        url = '%s?%s' % (self.url_for('user.pro_version'), urlencode({'next': next_url}))

        with self.test_request_context:

            # Log the user in.
            self.login(user_pro)
            self.assertTrue(util.user_is_pro())
            self.assertFalse(util.pro_version_enabled(), False)

            with self.app.session_transaction() as sess:
                self.assertNotIn('pro_version', sess)

            # Enable pro version.
            rv = self.app.get(url)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, next_url)

            with self.app.session_transaction() as sess:
                self.assertIn('pro_version', sess)
                self.assertTrue(sess['pro_version'])
                self.assertFalse(util.pro_version_enabled(), True)

            # Disable pro version.
            rv = self.app.get(url)
            self.assertEqual(rv.status_code, 302)
            self.assertEqual(rv.location, next_url)
            self.assertFalse(util.pro_version_enabled(), False)
            
            with self.app.session_transaction() as sess:
                self.assertNotIn('pro_version', sess)
