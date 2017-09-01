# coding: utf8
import unittest

from labonneboite.common import search


class SuggestLocationTest(unittest.TestCase):

    def test_suggest_locations_paris_1_findable(self):
        term = u"paris 1"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertTrue(u"paris - 1er" in city_names)

    def test_suggest_locations_paris_75000_first(self):
        term = u"paris"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEquals(u"paris", city_names[0])

    def test_suggest_locations_pau_first(self):
        term = u"pau"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEquals(u"pau", city_names[0])

    def test_suggest_locations_pezziardi_lilas_first(self):
        term = u"lilas"
        suggestions = search.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEquals(u"les lilas", city_names[0])
