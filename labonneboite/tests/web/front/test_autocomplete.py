import json
from unittest import mock

from labonneboite.scripts import create_index as script
from labonneboite.tests.test_base import AppTest


class AutocompleteAddressLocations(AppTest):

    def test_autocomplete_le_lab(self):
        coordinates = [
            {
                'latitude': 20,
                'longitude': -21,
                'label': 'Le dernier bar avant la fin du monde',
            }
        ]

        with mock.patch("labonneboite.common.geocoding.get_coordinates", return_value=coordinates):
            response = self.app.get(self.url_for('search.autocomplete_locations', term='ledernierbar'))

        expected_result = coordinates[:]
        expected_result[0]['value'] = expected_result[0]['label']

        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_result, json.loads(response.data.decode()))

    def test_autocomplete_empty_query(self):
        response = self.app.get(self.url_for('search.autocomplete_locations'))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.data.decode()))

    def test_autocomplete_whitespace(self):
        response = self.app.get(self.url_for('search.autocomplete_locations', term='    '))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.data.decode()))


class AutocompleteCityLocations(AppTest):

    def setUp(self):
        """
        Populate ES with data required for these tests to work.
        """
        super(AutocompleteCityLocations, self).setUp()
        script.disable_verbose_loggers()
        script.create_locations()
        script.enable_verbose_loggers()

    def test_autocomplete_happy_path(self):
        response = self.app.get(self.url_for('search.suggest_locations', term='metz'))
        self.assertEqual(200, response.status_code)
        result = json.loads(response.data.decode())
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]['city'], 'metz')
        self.assertEqual(result[0]['zipcode'], '57000')

    def test_autocomplete_empty_query(self):
        response = self.app.get(self.url_for('search.suggest_locations'))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.data.decode()))

    def test_autocomplete_whitespace(self):
        response = self.app.get(self.url_for('search.suggest_locations', term='    '))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.data.decode()))


class AutocompleteJobLabels(AppTest):

    def setUp(self):
        """
        Populate ES with data required for these tests to work.
        """
        super(AutocompleteJobLabels, self).setUp()
        script.disable_verbose_loggers()
        script.create_job_codes()
        script.enable_verbose_loggers()

    def test_autocomplete_happy_path(self):
        response = self.app.get(self.url_for('search.suggest_job_labels', term='boucher'))
        self.assertEqual(200, response.status_code)
        result = json.loads(response.data.decode())
        self.assertEqual(len(result), 6)
        self.assertEqual(result[0]['id'], 'D1101')
        self.assertEqual(result[0]['occupation'], 'boucherie')

    def test_autocomplete_thesaurus_ios(self):
        response = self.app.get(self.url_for('search.suggest_job_labels', term='ios'))
        self.assertEqual(200, response.status_code)
        result = json.loads(response.data.decode())
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]['id'], 'M1805')
        self.assertEqual(result[0]['occupation'], 'etudes-et-developpement-informatique')

    def test_autocomplete_thesaurus_android(self):
        response = self.app.get(self.url_for('search.suggest_job_labels', term='android'))
        self.assertEqual(200, response.status_code)
        result = json.loads(response.data.decode())
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0]['id'], 'M1805')
        self.assertEqual(result[0]['occupation'], 'etudes-et-developpement-informatique')

    def test_autocomplete_empty_query(self):
        response = self.app.get(self.url_for('search.suggest_job_labels'))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.data.decode()))

    def test_autocomplete_whitespace(self):
        response = self.app.get(self.url_for('search.suggest_job_labels', term='    '))
        self.assertEqual(200, response.status_code)
        self.assertEqual([], json.loads(response.data.decode()))
