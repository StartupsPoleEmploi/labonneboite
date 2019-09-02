from labonneboite.common import autocomplete
from labonneboite.conf import settings
from labonneboite.scripts import create_index
from labonneboite.tests.test_base import DatabaseTest


class SuggestLocationTest(DatabaseTest):

    def setUp(self):
        super(SuggestLocationTest, self).setUp()

        create_index.create_locations()
        self.es.indices.flush(index=settings.ES_INDEX)

    def test_suggest_locations_paris_1_findable(self):
        term = "paris 1er"
        suggestions = autocomplete.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertTrue("paris-1er" in city_names)

    def test_suggest_locations_paris_75000_first(self):
        term = "paris"
        suggestions = autocomplete.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEqual("paris", city_names[0])

    def test_suggest_locations_pau_first(self):
        term = "pau"
        suggestions = autocomplete.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEqual("pau", city_names[0])

    def test_suggest_locations_pezziardi_lilas_first(self):
        term = "lilas"
        suggestions = autocomplete.build_location_suggestions(term)
        city_names = [suggestion['city'] for suggestion in suggestions]
        self.assertEqual("les-lilas", city_names[0])
