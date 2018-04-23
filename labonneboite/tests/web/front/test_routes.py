# coding: utf8
from urlparse import parse_qsl, urlparse

from flask import url_for
import mock

from labonneboite.tests.test_base import AppTest
from labonneboite.web.search.views import get_canonical_results_url, get_location



class SearchEntreprisesTest(AppTest):

    def setUp(self):
        super(SearchEntreprisesTest, self).setUp()
        self.gotham_city = {
            'label': 'Gotham City 19100',
            'zipcode': '19100',
            'city': 'Gotham'
        }


    def test_search_by_coordinates(self):
        url = self.url_for('search.entreprises', lat=42, lon=6, occupation='strategie-commerciale')

        addresses = [self.gotham_city]
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=addresses) as get_address:
            response = self.app.get(url)

            get_address.assert_called_once_with(42, 6, limit=1)
            self.assertEqual(200, response.status_code)

        self.assertIn("Gotham City 19100", response.data)


    def test_search_by_coordinates_with_no_associated_address(self):
        url = self.url_for('search.entreprises', lat=42, lon=6, occupation='strategie-commerciale')
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=[]) as get_address:
            response = self.app.get(url)

            get_address.assert_called_once_with(42, 6, limit=1)
            self.assertEqual(200, response.status_code)


    def test_search_by_invalid_coordinates(self):
        url = self.url_for('search.entreprises', lat=91, lon=181, occupation='strategie-commerciale')
        addresses = [self.gotham_city]
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=addresses):
            response = self.app.get(url)
        self.assertEqual(200, response.status_code)


    def test_canonical_url(self):
        with self.app_context:
            url_no_alternance = get_canonical_results_url('05100', u'Cervières', 'Boucherie')
            url_alternance = get_canonical_results_url('05100', u'Cervières', 'Boucherie', alternance=True)
        response_no_alternance = self.app.get(url_no_alternance)
        response_alternance = self.app.get(url_alternance)

        self.assertEqual(
            'http://' + self.TEST_SERVER_NAME + '/entreprises?city=cervieres&zipcode=05100&occupation=boucherie',
            url_no_alternance
        )
        self.assertEqual(
            'http://' + self.TEST_SERVER_NAME + '/entreprises?city=cervieres&zipcode=05100&occupation=boucherie&f_a=1',
            url_alternance
        )
        self.assertEqual(200, response_alternance.status_code)
        self.assertEqual(200, response_no_alternance.status_code)


    def test_get_location_no_arguments(self):
        location, named_location = get_location({})
        self.assertIsNone(location, named_location)


    def test_get_location_incorrect_coordinates(self):
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=[]):
            location, named_location = get_location({
                'lat': 0,
                'lon': 0
            })
        self.assertIsNotNone(location)
        self.assertEqual(0, location.latitude)
        self.assertEqual(0, location.longitude)
        self.assertIsNone(named_location)

    def test_get_location_correct_coordinates(self):
        addresses = [{
            'label': 'Copacabana',
            'city': 'Rio',
            'zipcode': '666',
        }]
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=addresses):
            location, named_location = get_location({
                'lat': -2,
                'lon': -15
            })
        self.assertIsNotNone(location)
        self.assertEqual(-2, location.latitude)
        self.assertEqual(-15, location.longitude)
        self.assertIsNotNone(named_location)
        self.assertEqual('Rio', named_location.city)
        self.assertEqual('666', named_location.zipcode)
        self.assertEqual('Copacabana', named_location.name)


class SearchLegacyResultsTest(AppTest):

    def test_zipcodes_mistakenly_used_as_commune_ids(self):
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
        url = self.url_for('search.results', city='grenoble', zipcode='38000', occupation='strategie-commerciale')
        rv = self.app.get(url, follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

    def test_search_url_with_wrong_zipcode_does_not_break(self):
        """
        Nancy has zipcode 54000 and not 54100.
        However some bots happened to call this URL which was broken.
        https://github.com/StartupsPoleEmploi/labonneboite/pull/61
        """
        url = self.url_for('search.results', city='nancy', zipcode='54100', occupation='strategie-commerciale')
        rv = self.app.get(url, follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn("La ville que vous avez choisie n'est pas valide", rv.data)

    def test_search_with_wrong_zipcode_and_naf_filter(self):
        # Because of a wrong zipcode, the naf filter should not be taken into
        # account
        with self.test_request_context:
            url = url_for('search.results', city='nancy', zipcode='54100', occupation='strategie-commerciale')
            url += '?naf=8610Z'
            rv = self.app.get(url, follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertIn("La ville que vous avez choisie n'est pas valide", rv.data)



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
