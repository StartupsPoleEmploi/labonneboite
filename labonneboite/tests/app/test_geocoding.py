# coding: utf8
import unittest

from labonneboite.common import geocoding


class GeocodingTest(unittest.TestCase):

    def test_get_cities(self):
        all_cities = geocoding.get_cities()
        found = False
        for city in all_cities:
            if city['name'].lower().startswith("paris"):
                print city['name']
            if city['name'] == u"Paris":
                found = True
                break
        self.assertTrue(found)

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
