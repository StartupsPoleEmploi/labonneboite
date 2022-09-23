from unittest import mock
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import parse_qsl

from flask import url_for

from labonneboite.conf import settings
from labonneboite.tests.test_base import AppTest, DatabaseTest
from labonneboite.web.search.views import get_canonical_results_url, get_location, get_url_for_rome 


class SearchEntreprisesTest(DatabaseTest):

    def setUp(self):
        super(SearchEntreprisesTest, self).setUp()
        self.gotham_city = {
            'label': 'Gotham City 19100',
            'zipcode': '19100',
            'city_code': '19111',
            'city': 'Gotham'
        }

    def test_search_by_coordinates(self):
        url = self.url_for('search.entreprises', lat=42, lon=6, occupation='strategie-commerciale')

        addresses = [self.gotham_city]
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=addresses) as get_address:
            response = self.app.get(url)

            get_address.assert_called_once_with(42, 6, limit=1)
            self.assertEqual(200, response.status_code)

        self.assertIn("Gotham City 19100", response.data.decode())

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

    def test_search_by_non_float_coordinates(self):
        self.es.index(index=settings.ES_INDEX, doc_type='ogr', id=1, body={
            'ogr_code': '10974',
            'ogr_description': 'Animateur commercial / Animatrice commerciale',
            'rome_code': 'D1501',
            'rome_description': 'Animation de vente'
        })
        self.es.indices.flush(index=settings.ES_INDEX)

        url = self.url_for('search.entreprises', lat='undefined', lon='undefined', j='D1501')
        response = self.app.get(url)
        self.assertEqual(200, response.status_code)
        self.assertIn("La ville que vous avez choisie n'est pas valide", response.data.decode())

    def test_canonical_url(self):
        with self.app_context():
            url = get_canonical_results_url('05100', 'Cervières', 'Boucherie')
        response = self.app.get(url)

        self.assertEqual(
            settings.PREFERRED_URL_SCHEME + '://' + settings.SERVER_NAME + '/entreprises?city=cervieres&zipcode=05100&occupation=boucherie',
            url
        )
        self.assertEqual(200, response.status_code)


class EntreprisesLocationTest(AppTest):

    def test_get_location_no_arguments(self):
        location, named_location, departements = get_location({})
        self.assertIsNone(location, named_location)

    def test_get_location_incorrect_coordinates(self):
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=[]):
            location, named_location, departements = get_location({
                'lat': 0,
                'lon': 0
            })
        self.assertIsNotNone(location)
        self.assertEqual(0, location.latitude)
        self.assertEqual(0, location.longitude)
        self.assertIsNone(named_location)

    def test_get_location_invalid_coordinates_valid_name(self):
        metz = {
            'latitude': 45,
            'longitude': 8,
            'label': 'Metz',
            'zipcode': '01000',
            'city': 'Wurst City'
        }
        with mock.patch('labonneboite.common.geocoding.get_coordinates', return_value=[metz]):
            location, named_location, departements = get_location({
                'lat': '',
                'lon': '',
                'l': 'metz'
            })
        self.assertIsNotNone(location)
        self.assertEqual(45, location.latitude)
        self.assertEqual(8, location.longitude)
        self.assertEqual('Metz', named_location.name)
        self.assertEqual('Wurst City', named_location.city)
        self.assertEqual('01000', named_location.zipcode)

    def test_get_location_correct_coordinates(self):
        addresses = [{
            'label': 'Copacabana',
            'city': 'Rio',
            'city_code': '19111',
            'zipcode': '666',
        }]
        with mock.patch('labonneboite.common.geocoding.get_address', return_value=addresses):
            location, named_location, departements = get_location({
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

    def test_get_location_location_not_found(self):
        with mock.patch('labonneboite.common.geocoding.get_coordinates', return_value=[]):
            location, named_location, departements = get_location({
                'l': 42,  # I swear, this happened in production
            })
        self.assertIsNone(location)
        self.assertIsNone(named_location)


class SearchLegacyResultsTest(DatabaseTest):

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

    def test_search_results_with_unicode_city(self):
        url = self.url_for('search.results', city='nîmes', zipcode='30000', occupation='strategie-commerciale')
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
        self.assertIn("La ville que vous avez choisie n'est pas valide", rv.data.decode())

    def test_search_with_wrong_zipcode_and_naf_filter(self):
        # Because of a wrong zipcode, the naf filter should not be taken into
        # account
        with self.test_request_context():
            url = url_for('search.results', city='nancy', zipcode='54100', occupation='strategie-commerciale')
            url += '?naf=8610Z'
            rv = self.app.get(url, follow_redirects=True)
            self.assertEqual(rv.status_code, 200)
            self.assertIn("La ville que vous avez choisie n'est pas valide", rv.data.decode())


class GenericUrlSearchRedirectionTest(AppTest):

    def test_generic_url_search_by_commune_and_rome(self):
        rv = self.app.get("/entreprises/commune/75056/rome/D1104")
        self.assertEqual(rv.status_code, 302)

        url, querystring = urllib.parse.splitquery(rv.location)
        parameters = dict(parse_qsl(querystring))
        expected_url = self.url_for('search.entreprises', _external=False)
        expected_parameters = {
            'city': 'paris',
            'zipcode': '75000',
            'occupation': 'patisserie-confiserie-chocolaterie-et-glacerie'
        }
        self.assertEqual(expected_url, url)
        self.assertEqual(expected_parameters, parameters)

    def test_generic_url_search_by_commune_and_rome_with_distance(self):
        """
        Ensure that the `distance` query string param follow the redirection chain.
        """
        rv = self.app.get("/entreprises/commune/75056/rome/D1104?d=100")
        self.assertEqual(rv.status_code, 302)

        url, querystring = urllib.parse.splitquery(rv.location)
        parameters = dict(parse_qsl(querystring))
        expected_url = self.url_for('search.entreprises', _external=False)
        expected_parameters = {
            'city': 'paris',
            'zipcode': '75000',
            'occupation': 'patisserie-confiserie-chocolaterie-et-glacerie',
            'd': '100'
        }
        self.assertEqual(expected_url, url)
        self.assertEqual(expected_parameters, parameters)

    def test_generic_url_search_by_commune_and_rome_with_utm_campaign(self):
        """
        Ensure that `utm*` query string params follow the redirection chain.
        """
        url = "/entreprises/commune/75056/rome/D1104?utm_medium=web&utm_source=test&utm_campaign=test"
        rv = self.app.get(url)
        self.assertEqual(rv.status_code, 302)

        expected_url = self.url_for('search.entreprises', _external=False)
        expected_parameters = {
            'city': 'paris',
            'zipcode': '75000',
            'occupation': 'patisserie-confiserie-chocolaterie-et-glacerie',
            'utm_medium': 'web',
            'utm_source': 'test',
            'utm_campaign': 'test'
        }
        url, querystring = urllib.parse.splitquery(rv.location)
        parameters = dict(parse_qsl(querystring))
        self.assertEqual(expected_url, url)
        self.assertEqual(expected_parameters, parameters)

    def test_get_url_for_rome_departments(self):
        with self.app_context():
            with mock.patch('labonneboite.common.geocoding.datagouv.get_department_by_code', return_value={"department": "57", "label": 'Moselle (57)'}):
                url = get_url_for_rome('M1805', '57')
                self.assertEqual(url, 'http://labonneboite.pole-emploi.fr/entreprises?departments=57&j=M1805&l=Moselle+(57)&occupation=etudes-et-developpement-informatique')
            with mock.patch('labonneboite.common.geocoding.datagouv.get_department_by_code', return_value=None):
                url = get_url_for_rome('M1805', '57')
                self.assertEqual(url, None)

