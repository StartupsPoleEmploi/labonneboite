# coding: utf8
import json

import mock

from labonneboite.tests.test_base import AppTest


class AutocompleteLocations(AppTest):

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
