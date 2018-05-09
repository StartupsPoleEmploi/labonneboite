# coding: utf8
import json
import os
import unittest

import mock
from labonneboite.common import geocoding


class GeocodingTest(unittest.TestCase):

    def test_get_cities(self):
        all_cities = geocoding.get_cities()
        found = False
        for city in all_cities:
            if city['name'] == u"Paris":
                found = True
                break
        self.assertTrue(found)

    def test_is_commune_id(self):
        self.assertFalse(geocoding.is_commune_id(u"75010"))
        self.assertTrue(geocoding.is_commune_id(u"75110"))

    def test_is_departement(self):
        self.assertFalse(geocoding.is_departement(u"AAAAA"))
        self.assertTrue(geocoding.is_departement(u"57"))

    def test_saint_denis_reunion_have_correct_coordinates(self):
        city = geocoding.get_city_by_zipcode(u"97400", u"montigny-les-metz")
        self.assertEquals(int(float(city['coords']['lat'])), -20)
        self.assertEquals(int(float(city['coords']['lon'])), 55)

    def test_montigny_les_metz_is_correctly_found(self):
        cities_zipcodes = [[city['name'], city['zipcode']] for city in geocoding.get_cities()]
        montigny_zipcodes = [x[1] for x in cities_zipcodes if x[0].startswith('Montigny-l') and x[0].endswith('s-Metz')]
        self.assertEquals(len(montigny_zipcodes), 1)
        zipcode = montigny_zipcodes[0]
        self.assertEquals(zipcode, u"57950")
        city = geocoding.get_city_by_zipcode(zipcode, u"paris-4eme")
        self.assertEquals(city['coords']['lat'], 49.09692140157696)
        self.assertEquals(city['coords']['lon'], 6.1549924040022725)

    def test_paris4eme_is_correctly_found(self):
        cities_zipcodes = [[city['name'], city['zipcode']] for city in geocoding.get_cities()]
        paris4eme_zipcodes = [x[1] for x in cities_zipcodes if x[1] == "75004"]
        self.assertEquals(len(paris4eme_zipcodes), 1)
        zipcode = paris4eme_zipcodes[0]
        self.assertEquals(zipcode, u"75004")
        city = geocoding.get_city_by_zipcode(zipcode, u"saint-denis")
        self.assertEquals(city['coords']['lat'], 48.8544006347656)
        self.assertEquals(city['coords']['lon'], 2.36240005493164)

    def test_communes_with_same_zipcodes_are_correctly_found(self):

        oraison = geocoding.get_city_by_zipcode(u"04700", u"oraison")
        puimichel = geocoding.get_city_by_zipcode(u"04700", u"puimichel")
        self.assertEquals(oraison['commune_id'], u'04143')
        self.assertEquals(puimichel['commune_id'], u'04156')

        vantoux = geocoding.get_city_by_zipcode(u"57070", u"vantoux")
        saint_julien_les_metz = geocoding.get_city_by_zipcode(u"57070", u"saint-julien-les-metz")
        self.assertEquals(vantoux['commune_id'], u'57693')
        self.assertEquals(saint_julien_les_metz['commune_id'], u'57616')


class AdresseApiTest(unittest.TestCase):


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
            coordinates = geocoding.get_coordinates(u'22 Allée Darius Milhaud, 75019 Paris')

        self.assertEqual([{
            'latitude': 48.884085,
            'longitude': 2.38728,
            'label': u'22 Allée Darius Milhaud 75019 Paris',
            'city': 'Paris',
            'zipcode': '75019',
        }], coordinates)


    def test_400_error(self):
        mock_get = mock.Mock(status_code=400, json=mock.Mock(side_effect=ValueError))
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates(u'22 Allée Darius Milhaud, 75019 Paris')

        self.assertEqual([], coordinates)


    def test_get_address(self):
        mock_get = self.mock_get('reverse-lelab.json')
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            address = geocoding.get_address(48.884085, 2.38728)

        self.assertEqual([{
            'city': 'Paris',
            'zipcode': '75019',
            'label': u'22 Allée Darius Milhaud 75019 Paris',
        }], address)


    def test_duplicate_features(self):
        mock_get = self.mock_get('search-metz.json')

        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            coordinates = geocoding.get_coordinates(u'metz', limit=10)

        self.assertNotEqual(coordinates[0]['label'], coordinates[1]['label'])


    def test_get_address_of_unknown_location(self):
        mock_get = self.mock_get('reverse-middleearth.json')
        with mock.patch.object(geocoding.datagouv.requests, 'get', return_value=mock_get):
            address = geocoding.get_address(0, 0)

        self.assertEqual([], address)
