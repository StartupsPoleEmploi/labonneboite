# coding: utf8
from urllib import urlencode

from labonneboite.tests.test_base import DatabaseTest
from labonneboite.common import util
from labonneboite.common.models import User
from labonneboite.conf import settings

class RootTest(DatabaseTest):

    def test_no_kit_if_public_user(self):
        rv = self.app.get(self.url_for('root.kit'))
        self.assertEquals(rv.status_code, 404)

    def test_no_kit_if_pro_but_not_enabled(self):
        self.assertIn('@pole-emploi.fr', settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES)

        user_pro = User.create(email=u'x@pole-emploi.fr', gender=u'male', first_name=u'John', last_name=u'Doe')

        self.login(user_pro)
        self.assertTrue(util.user_is_pro())
        self.assertFalse(util.pro_version_enabled())

        rv = self.app.get(self.url_for('root.kit'))
        self.assertEquals(rv.status_code, 404)

    def test_kit_if_pro_and_enabled(self):
        self.assertIn('@pole-emploi.fr', settings.VERSION_PRO_ALLOWED_EMAIL_SUFFIXES)

        user_pro = User.create(email=u'x@pole-emploi.fr', gender=u'male', first_name=u'John', last_name=u'Doe')

        self.login(user_pro)
        self.assertTrue(util.user_is_pro())

        next_url = u'http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0&f_a=0'
        pro_version_url = '%s?%s' % (self.url_for('user.pro_version'), urlencode({'next': next_url}))
        self.assertFalse(util.pro_version_enabled())

        rv = self.app.get(pro_version_url)
        self.assertTrue(util.pro_version_enabled())
        
        # Non-empty pdf file
        rv = self.app.get(self.url_for('root.kit'))
        self.assertEquals(rv.status_code, 200)
        self.assertEqual('application/pdf', rv.content_type)
        self.assertLess(1000, rv.content_length)
