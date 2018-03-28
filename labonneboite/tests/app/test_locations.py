# coding: utf8
import unittest

from labonneboite.common import locations


class CityLocationTest(unittest.TestCase):

    def test_hyphenated_city_name(self):
        city = locations.CityLocation('19100', 'brive-la-gaillarde')
        self.assertEqual(city.name, 'Brive-la-Gaillarde')

    def test_unicode_city_name(self):
        city = locations.CityLocation('05100', 'briancon')
        self.assertEqual(city.name, u'Briançon')

    def test_no_slug(self):
        city = locations.CityLocation('05100')
        self.assertEqual(city.name, u'Briançon')
