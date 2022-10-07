import os
import json
from unittest import mock, TestCase

from labonneboite.conf import settings  # noqa
from labonneboite.common.geocoding import datagouv

autocomplete_cal_formatted = [{
    'department': '14',
    'label': 'Calvados (14)',
    'score': 0.5637810393596784,
}, {
    'department': '62',
    'label': 'Pas-de-Calais (62)',
    'score': 0.5262018995338849,
}]

search_lelab_formatted = [{
    'latitude': 48.884085,
    'longitude': 2.38728,
    'label': '22 Allée Darius Milhaud 75019 Paris',
    'score': 0.9421181818181817,
    'city': 'Paris',
    'city_code': '75119',
    'zipcode': '75019',
}]


def get_fixture(fixture, api_name='adresse.data.gouv.fr'):
    """
    Load a fixture from the fixtures/ folder and mock the request.get function.
    """
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', api_name, fixture)
    fixture = json.load(open(fixture_path))
    return fixture


class DatagouvTest(TestCase):

    def test_long_addresses_are_shortened(self):
        long_address = 'a' * 300
        short_address = 'a' * 200
        with mock.patch.object(datagouv, 'get_addresses', return_value=search_lelab_formatted) as mock_get_addresses, \
                mock.patch.object(datagouv, 'get_departments', return_value=autocomplete_cal_formatted) as mock_get_departments:  # noqa
            result = datagouv.search(long_address)
            self.assertEqual(short_address, mock_get_addresses.call_args[1]['q'])
            self.assertEqual(autocomplete_cal_formatted[0], result[0])
            self.assertEqual(autocomplete_cal_formatted[1], result[1])
            self.assertEqual(search_lelab_formatted[0], result[2])


class DepartmentApiTest(TestCase):

    def setUp(self):
        datagouv.fetch_json.cache_clear()

    def test_autocomplete_cal(self):
        fixture = get_fixture('autocomplete-cal.json', 'geo.api.gouv.fr')
        departments = datagouv.format_departments(fixture)

        self.assertEqual(autocomplete_cal_formatted, departments)

    def test_autocomplete_empty(self):
        departments = datagouv.format_departments([])

        self.assertEqual([], departments)

    def test_400_error(self):
        fixture = mock.Mock(status_code=400, json=mock.Mock(side_effect=ValueError))
        with mock.patch.object(datagouv.requests, 'get', return_value=fixture):
            coordinates = datagouv.get_departments('anything')

        self.assertEqual([], coordinates)


class AdresseApiTest(TestCase):

    def setUp(self):
        datagouv.fetch_json.cache_clear()

    def test_get_coordinates(self):
        fixture = get_fixture('search-lelab.json')
        features = fixture['features']

        coordinates = datagouv.format_coordinates(features)

        self.assertEqual(search_lelab_formatted, coordinates)

    def test_city_homonyms_can_be_distinguished_by_zipcode(self):
        """
        Five homonym cities "Saint-Paul" should have distinguishable labels.
        """
        fixture = get_fixture('search-saint-paul.json')
        features = fixture['features']

        coordinates = datagouv.format_coordinates(features)

        self.assertEqual(len(coordinates), 5)
        for coordinate in coordinates:
            self.assertIn(coordinate['zipcode'], coordinate['label'])

    def test_400_error(self):
        fixture = mock.Mock(status_code=400, json=mock.Mock(side_effect=ValueError))
        with mock.patch.object(datagouv.requests, 'get', return_value=fixture):
            coordinates = datagouv.search('22 Allée Darius Milhaud, 75019 Paris')

        self.assertEqual([], coordinates)

    def test_empty_query(self):
        with mock.patch.object(datagouv.requests, 'get', side_effect=ZeroDivisionError):
            coordinates = datagouv.search('')

        self.assertEqual([], coordinates)

    def test_get_address(self):
        fixture = get_fixture('reverse-lelab.json')
        features = fixture['features']

        address = datagouv.format_addresses(features)

        self.assertEqual([{
            'city': 'Paris',
            'zipcode': '75019',
            'city_code': '75119',
            'label': '22 Allée Darius Milhaud 75019 Paris',
        }], address)

    def test_duplicate_features(self):
        fixture = get_fixture('search-metz.json')
        features = fixture['features']

        coordinates = datagouv.format_coordinates(features)

        self.assertNotEqual(coordinates[0]['label'], coordinates[1]['label'])

    def test_get_address_of_unknown_location(self):
        fixture = get_fixture('reverse-middleearth.json')
        features = fixture['features']

        address = datagouv.format_addresses(features)

        self.assertEqual([], address)

    def test_get_coordinates_of_location_with_no_city(self):
        fixture = get_fixture('search-balltrapp.json')
        features = fixture['features']

        coordinates = datagouv.format_coordinates(features)

        self.assertIn("city", coordinates[0])
