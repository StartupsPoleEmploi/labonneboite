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
