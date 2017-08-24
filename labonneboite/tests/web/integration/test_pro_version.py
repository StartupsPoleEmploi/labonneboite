# coding: utf8
from labonneboite.common.models import User
from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common import util


class ProVersionTest(DatabaseTest):

    def test_user_is_pro(self):
        """
        Test that the Pro Version is correctly detected in various cases.
        """

        user_pro = User.create(email=u'john.doe@pole-emploi.fr', gender=u'male', first_name=u'John', last_name=u'Doe')
        user_public = User.create(email=u'john.doe@gmail.com', gender=u'male', first_name=u'John', last_name=u'Doe')

#        FIXME restore when version PRO will be back
#        with self.test_request_context:
#
#            # Pro Version should be disabled for non logged users.
#            self.assertFalse(util.user_is_pro())
#
#            # Pro Version should be enabled for a user with a PRO email.
#            self.login(user_pro)
#            self.assertTrue(util.user_is_pro())
#            self.logout()
#            self.assertFalse(util.user_is_pro())
#
#            # Pro Version should be disabled for a user with a non PRO email.
#            self.login(user_public)
#            self.assertFalse(util.user_is_pro())
#            self.logout()
#            self.assertFalse(util.user_is_pro())
