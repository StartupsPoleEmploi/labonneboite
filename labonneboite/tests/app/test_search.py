# coding: utf8
import unittest

from labonneboite.common import search


class CityLocationTest(unittest.TestCase):

    def test_hyphenated_city_name(self):
        city = search.CityLocation('19100', 'brive-la-gaillarde')
        self.assertEqual(city.name, 'Brive-la-Gaillarde')

    def test_unicode_city_name(self):
        city = search.CityLocation('05100', 'briancon')
        self.assertEqual(city.name, u'Briançon')

    def test_no_slug(self):
        city = search.CityLocation('05100')
        self.assertEqual(city.name, u'Briançon')
