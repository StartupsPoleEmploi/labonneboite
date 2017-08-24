# coding: utf8
import unittest

from labonneboite.common import search


class SuggestLocationTest(unittest.TestCase):

    def test_suggest_locations_paris_1_findable(self):
        term = "paris 1"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertTrue("paris - 1er" in city_names)

    def test_suggest_locations_paris_75000_first(self):
        term = "paris"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEquals("paris", city_names[0])

    def test_suggest_locations_pau_first(self):
        term = "pau"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEquals("pau", city_names[0])

    def test_suggest_locations_pezziardi_lilas_first(self):
        term = "lilas"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEquals("lilas", city_names[0])
