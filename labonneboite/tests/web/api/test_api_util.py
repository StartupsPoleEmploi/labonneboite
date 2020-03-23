from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common.constants import Scope
from labonneboite.web.api.util import has_scope, get_key, UnknownUserException

class UserTest(DatabaseTest):

    def test_has_scopes(self):
        # emploi_store_dev is no user, it has no scope
        self.assertFalse(has_scope('emploi_store_dev', None, Scope.COMPANY_EMAIL))
        self.assertFalse(has_scope('emploi_store_dev', None, Scope.COMPANY_WEBSITE))
        # labonneboite is a user and has a safe scope
        self.assertFalse(has_scope('labonneboite', None, Scope.COMPANY_EMAIL))
        self.assertTrue(has_scope('labonneboite', None, Scope.COMPANY_WEBSITE))
        # labonneboite can request through a proxy
        self.assertFalse(has_scope('emploi_store_dev', 'labonneboite', Scope.COMPANY_EMAIL))
        self.assertTrue(has_scope('emploi_store_dev', 'labonneboite', Scope.COMPANY_WEBSITE))
        self.assertTrue(has_scope('unknown_user', 'labonneboite', Scope.COMPANY_WEBSITE))
        self.assertTrue(has_scope(None, 'labonneboite', Scope.COMPANY_WEBSITE))
        # unknown users have no scopes with or without proxies
        self.assertFalse(has_scope('unknown_user', None, Scope.COMPANY_WEBSITE))
        self.assertFalse(has_scope(None, 'unknown_user', Scope.COMPANY_WEBSITE))
        self.assertFalse(has_scope('emploi_store_dev', 'unknown_user', Scope.COMPANY_WEBSITE))
        self.assertFalse(has_scope('empty_user', None, Scope.COMPANY_WEBSITE))

    def test_get_key(self):
        self.assertEqual(get_key('labonneboite'), 'dummykey')
        self.assertEqual(get_key('emploi_store_dev'), 'anotherdummykey')
        self.assertEqual(get_key('unknown_user'), None)
        self.assertEqual(get_key('unknown_user', 'default123'), 'default123')

