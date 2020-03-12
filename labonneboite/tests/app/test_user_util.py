from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common.scope import Scope
from labonneboite.common.user_util import has_scope, get_key, string_to_enum, UnknownUserException
from labonneboite.conf import settings

class UserTest(DatabaseTest):

    def test_has_scopes(self):
        self.assertFalse(has_scope('labonneboite', None, Scope.COMPANY_EMAIL))
        self.assertTrue(has_scope('labonneboite', None, Scope.COMPANY_WEBSITE))
        self.assertFalse(has_scope('unknown_user', None, Scope.COMPANY_WEBSITE))
        self.assertFalse(has_scope('empty_user', None, Scope.COMPANY_WEBSITE))
        self.assertTrue(has_scope('unknown_user', 'labonneboite', Scope.COMPANY_WEBSITE))

    def test_get_key(self):
        self.assertEqual(get_key('labonneboite'), 'dummykey')
        self.assertEqual(get_key('unknown_user'), None)

    def test_string_to_enum(self):
        self.assertEqual(string_to_enum(Scope, 'unknon_value'), None)
        self.assertEqual(string_to_enum(Scope, 'unknon_value', Scope.COMPANY_WEBSITE), Scope.COMPANY_WEBSITE)
        self.assertEqual(string_to_enum(Scope, Scope.COMPANY_WEBSITE.value), Scope.COMPANY_WEBSITE)
