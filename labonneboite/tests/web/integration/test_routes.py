# coding: utf8
from urlparse import parse_qsl, urlparse

from labonneboite.tests.test_base import AppTest


class RouteTest(AppTest):

    def test_zicodes_mistakenly_used_as_commune_ids(self):
        # 14118 is a commune_id, normal behavior
        rv = self.app.get("/entreprises/commune/14118/rome/D1101")
        self.assertEqual(rv.status_code, 302)

        # 14000 is a zipcode, not a commune_id, should result as a 404
        rv = self.app.get("/entreprises/commune/14000/rome/D1101")
        self.assertEqual(rv.status_code, 404)

    def test_unknown_rome_id(self):
        # normal behavior
        rv = self.app.get("/entreprises/commune/14118/rome/D1101")
        self.assertEqual(rv.status_code, 302)

        # D8888 does not exist
        rv = self.app.get("/entreprises/commune/14118/rome/D8888")
        self.assertEqual(rv.status_code, 404)

    def test_search_url_without_human_params_does_not_break(self):
        """
        this type of URL without any parameter is never used by humans
        and only by bots crawling our sitemap.xml
        """
        rv = self.app.get("/entreprises/grenoble-38000/strategie-commerciale")
        self.assertEqual(rv.status_code, 200)

    def test_search_url_with_wrong_zipcode_does_not_break(self):
        """
        Nancy has zipcode 54000 and not 54100.
        However some bots happened to call this URL which was broken.
        https://github.com/StartupsPoleEmploi/labonneboite/pull/61
        """
        rv = self.app.get("/entreprises/nancy-54100/strategie-commerciale")
        self.assertEqual(rv.status_code, 200)


class GenericUrlSearchRedirectionTest(AppTest):

    def test_generic_url_search_by_commune_and_rome(self):
        rv = self.app.get("/entreprises/commune/75056/rome/D1104")
        self.assertEqual(rv.status_code, 302)
        expected_relative_url = "/entreprises/paris-75000/patisserie-confiserie-chocolaterie-et-glacerie"
        self.assertTrue(rv.location.endswith(expected_relative_url))

    def test_generic_url_search_by_commune_and_rome_with_distance(self):
        """
        Ensure that the `distance` query string param follow the redirection chain.
        """
        rv = self.app.get("/entreprises/commune/75056/rome/D1104?d=100")
        self.assertEqual(rv.status_code, 302)
        expected_relative_url = ("/entreprises/paris-75000/patisserie-confiserie-chocolaterie-et-glacerie?d=100")
        self.assertTrue(rv.location.endswith(expected_relative_url))

    def test_generic_url_search_by_commune_and_rome_with_utm_campaign(self):
        """
        Ensure that `utm*` query string params follow the redirection chain.
        """
        url = "/entreprises/commune/75056/rome/D1104?utm_medium=web&utm_source=test&utm_campaign=test"
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 302)

        expected_path = '/entreprises/paris-75000/patisserie-confiserie-chocolaterie-et-glacerie'
        expected_query = {'utm_medium': 'web', 'utm_source': 'test', 'utm_campaign': 'test'}
        redirection_path = urlparse(rv.location).path
        redirection_query = dict(parse_qsl(urlparse(rv.location).query))
        self.assertEqual(redirection_path, expected_path)
        self.assertEqual(redirection_query, expected_query)
