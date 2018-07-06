# coding: utf8
import json
import os
from unittest import mock, TestCase
from labonneboite.common import geocoding


class GeocodingTest(TestCase):

    def test_get_cities(self):
        all_cities = geocoding.get_cities()
        found = False
        for city in all_cities:
            if city['name'] == "Paris":
                found = True
                break
        self.assertTrue(found)

    def test_is_commune_id(self):
        self.assertFalse(geocoding.is_commune_id("75010"))
        self.assertTrue(geocoding.is_commune_id("75110"))

    def test_is_departement(self):
        self.assertFalse(geocoding.is_departement("AAAAA"))
        self.assertTrue(geocoding.is_departement("57"))

    def test_saint_denis_reunion_have_correct_coordinates(self):
        city = geocoding.get_city_by_zipcode("97400", "montigny-les-metz")
        self.assertEqual(int(float(city['coords']['lat'])), -20)
        self.assertEqual(int(float(city['coords']['lon'])), 55)

    def test_montigny_les_metz_is_correctly_found(self):
        cities_zipcodes = [[city['name'], city['zipcode']] for city in geocoding.get_cities()]
        montigny_zipcodes = [x[1] for x in cities_zipcodes if x[0].startswith('Montigny-l') and x[0].endswith('s-Metz')]
        self.assertEqual(len(montigny_zipcodes), 1)
        zipcode = montigny_zipcodes[0]
        self.assertEqual(zipcode, "57950")
        city = geocoding.get_city_by_zipcode(zipcode, "paris-4eme")
        self.assertEqual(city['coords']['lat'], 49.09692140157696)
        self.assertEqual(city['coords']['lon'], 6.1549924040022725)

    def test_paris4eme_is_correctly_found(self):
        cities_zipcodes = [[city['name'], city['zipcode']] for city in geocoding.get_cities()]
        paris4eme_zipcodes = [x[1] for x in cities_zipcodes if x[1] == "75004"]
        self.assertEqual(len(paris4eme_zipcodes), 1)
        zipcode = paris4eme_zipcodes[0]
        self.assertEqual(zipcode, "75004")
        city = geocoding.get_city_by_zipcode(zipcode, "saint-denis")
        self.assertEqual(city['coords']['lat'], 48.8544006347656)
        self.assertEqual(city['coords']['lon'], 2.36240005493164)

    def test_communes_with_same_zipcodes_are_correctly_found(self):

        oraison = geocoding.get_city_by_zipcode("04700", "oraison")
        puimichel = geocoding.get_city_by_zipcode("04700", "puimichel")
        self.assertEqual(oraison['commune_id'], '04143')
        self.assertEqual(puimichel['commune_id'], '04156')

        vantoux = geocoding.get_city_by_zipcode("57070", "vantoux")
        saint_julien_les_metz = geocoding.get_city_by_zipcode("57070", "saint-julien-les-metz")
        self.assertEqual(vantoux['commune_id'], '57693')
        self.assertEqual(saint_julien_les_metz['commune_id'], '57616')


class AdresseApiTest(TestCase):


    def setUp(self):
        geocoding.datagouv.get_features.cache_clear()


    def mock_get(self, fixture):
        """
        Load a fixture from the fixtures/ folder and mock the request.get function.
        """
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'adresse.data.gouv.fr', fixture)
        mock_response = json.load(open(fixture_path))
        mock_get = mock.Mock(json=mock.Mock(return_value=mock_response), status_code=200)
        return mock_get


    def test_get_coordinates(self):
        mock_get = self.mock_get('search-lelab.json')

        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates('22 Allée Darius Milhaud, 75019 Paris')

        self.assertEqual([{
            'latitude': 48.884085,
            'longitude': 2.38728,
            'label': '22 Allée Darius Milhaud 75019 Paris',
            'city': 'Paris',
            'zipcode': '75019',
        }], coordinates)


    def test_city_homonyms_can_be_distinguished_by_zipcode(self):
        """
        Five homonym cities "Saint-Paul" should have distinguishable labels.
        """
        mock_get = self.mock_get('search-saint-paul.json')

        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates('Saint-Paul')

        self.assertEqual(len(coordinates), 5)
        for coordinate in coordinates:
            self.assertIn(coordinate['zipcode'], coordinate['label'])


    def test_400_error(self):
        mock_get = mock.Mock(status_code=400, json=mock.Mock(side_effect=ValueError))
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates('22 Allée Darius Milhaud, 75019 Paris')

        self.assertEqual([], coordinates)

    def test_empty_query(self):
        with mock.patch.object(geocoding.datagouv.requests, 'get', side_effect=ZeroDivisionError):
            coordinates = geocoding.get_coordinates('')

        self.assertEqual([], coordinates)


    def test_get_address(self):
        mock_get = self.mock_get('reverse-lelab.json')
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            address = geocoding.get_address(48.884085, 2.38728)

        self.assertEqual([{
            'city': 'Paris',
            'zipcode': '75019',
            'label': '22 Allée Darius Milhaud 75019 Paris',
        }], address)


    def test_duplicate_features(self):
        mock_get = self.mock_get('search-metz.json')

        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates('metz', limit=10)

        self.assertNotEqual(coordinates[0]['label'], coordinates[1]['label'])


    def test_get_address_of_unknown_location(self):
        mock_get = self.mock_get('reverse-middleearth.json')
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            address = geocoding.get_address(0, 0)

        self.assertEqual([], address)

    def test_get_coordinates_of_location_with_no_city(self):
        mock_get = self.mock_get('search-balltrapp.json')
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates("ball trapp")

        self.assertIn("city", coordinates[0])
