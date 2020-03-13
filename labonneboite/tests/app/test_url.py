import unittest

from labonneboite.common import util
from labonneboite.web.admin.views.office_admin_update import format_url


class UrlTest(unittest.TestCase):
    def test_is_decoded_url_safe(self):
        # relative url without domain name
        url = "/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0"
        self.assertTrue(util.is_decoded_url_safe(url))

        # Any absolute url including a domain name should be rejected.

        # correct domain name - https
        url = "https://labonneboite.pole-emploi.fr/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0"
        self.assertFalse(util.is_decoded_url_safe(url))

        # correct domain name - http
        url = "http://labonneboite.pole-emploi.fr/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0"
        self.assertFalse(util.is_decoded_url_safe(url))

        # wrong domain name
        url = "http://localhost:8090/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0"
        self.assertFalse(util.is_decoded_url_safe(url))

        # wrong domain name
        url = "http://labonneboite1.beta.pole-emploi.fr/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0"
        self.assertFalse(util.is_decoded_url_safe(url))

        # hacking attempt
        url = "http://www.doingbadthingsisbad.com/entreprises/metz-57000/boucherie?sort=score&d=10&h=1&p=0"
        self.assertFalse(util.is_decoded_url_safe(url))

    def test_format_url(self):
        # Urls modified
        url = "www.decathlon.fr"
        self.assertEqual(format_url(url), "http://www.decathlon.fr")

        url = "decathlon.fr"
        self.assertEqual(format_url(url), "http://decathlon.fr")

        # Urls not modified
        url = "http://www.decathlon.fr"
        self.assertEqual(format_url(url), url)

        url = "https://www.decathlon.fr"
        self.assertEqual(format_url(url), url)
