# coding: utf8
import unittest

from labonneboite.common import locations


class CityLocationTest(unittest.TestCase):

    def test_hyphenated_city_name(self):
        city = locations.CityLocation('19100', 'brive-la-gaillarde')
        self.assertEqual(city.name, 'Brive-la-Gaillarde')

    def test_unicode_city_name(self):
        city = locations.CityLocation('05100', 'briancon')
        self.assertEqual(city.name, 'Briançon')

    def test_no_slug(self):
        city = locations.CityLocation('05100')
        self.assertEqual(city.name, 'Briançon')

    def test_accented_city_name(self):
        city = locations.CityLocation('05100', 'Cervières')
        self.assertEqual(city.name, 'Cervières')
        self.assertEqual(6.756570896485574, city.location.longitude)
        self.assertEqual(44.86053112144938, city.location.latitude)
