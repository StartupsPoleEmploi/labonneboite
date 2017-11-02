# coding: utf8
import unittest

from labonneboite.common import util


class SafeUrlTest(unittest.TestCase):

    def test_is_safe_url(self):

        # Ensure that the `allowed_hosts` parameter is optional.
        url = u'http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0&f_a=0'
        is_safe_url = util.is_safe_url(url)
        self.assertTrue(is_safe_url)

        # `host` not in `allowed_hosts`.
        url = u'http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0&f_a=0'
        is_safe_url = util.is_safe_url(url, allowed_hosts={'labonneboite.pole-emploi.fr'})
        self.assertFalse(is_safe_url)

        # `host` in `allowed_hosts`.
        url = u'http://labonneboite.pole-emploi.fr/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0&f_a=0'
        is_safe_url = util.is_safe_url(url, allowed_hosts={'labonneboite.pole-emploi.fr'})
        self.assertTrue(is_safe_url)
