# coding: utf8
import unittest

from labonneboite.common import util
from labonneboite.web.admin.views.office_admin_update import format_url


class UrlTest(unittest.TestCase):

    def test_is_safe_url(self):

        # Ensure that the `allowed_hosts` parameter is optional.
        url = 'http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0'
        is_safe_url = util.is_safe_url(url)
        self.assertTrue(is_safe_url)

        # `host` not in `allowed_hosts`.
        url = 'http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0'
        is_safe_url = util.is_safe_url(url, allowed_hosts={'labonneboite.pole-emploi.fr'})
        self.assertFalse(is_safe_url)

        # `host` in `allowed_hosts`.
        url = 'http://labonneboite.pole-emploi.fr/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0'
        is_safe_url = util.is_safe_url(url, allowed_hosts={'labonneboite.pole-emploi.fr'})
        self.assertTrue(is_safe_url)

    def test_format_url(self):
        # Urls modified
        url = 'www.decathlon.fr'
        self.assertEquals(format_url(url), 'http://www.decathlon.fr')

        url = 'decathlon.fr'
        self.assertEquals(format_url(url), 'http://decathlon.fr')

        # Urls not modified
        url = 'http://www.decathlon.fr'
        self.assertEquals(format_url(url), url)

        url = 'https://www.decathlon.fr'
        self.assertEquals(format_url(url), url)
