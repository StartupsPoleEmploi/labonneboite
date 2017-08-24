# coding: utf8
import unittest

from labonneboite.common import geocoding


class GeocodingTest(unittest.TestCase):

    def test_load_coordinates_for_cities(self):
        all_cities = geocoding.load_coordinates_for_cities()
        found = False
        for _, city_name, _, _, _, _ in all_cities:
            if city_name.lower().startswith("paris"):
                print city_name
            if city_name == "Paris":
                found = True
        self.assertTrue(found)

    def test_saint_denis_reunion_have_correct_coordinates(self):
        city = "saint denis"
        zipcode = "97490"
        lat_long = geocoding.get_latitude_and_longitude_from_file(city, zipcode)
        self.assertEquals(int(float(lat_long[0])), -20)
        self.assertEquals(int(float(lat_long[1])), 55)

    def test_montigny_les_metz_is_correctly_found(self):
        cities_zipcodes = [[x[1], x[2]] for x in geocoding.load_coordinates_for_cities()]

        montigny_zipcodes = [x[1] for x in cities_zipcodes if x[0].startswith('Montigny-l') and x[0].endswith('s-Metz')]
        self.assertEquals(len(montigny_zipcodes), 1)
        zipcode = montigny_zipcodes[0]
        self.assertEquals(zipcode, "57158")

        city = "Montigny les Metz"
        lat_long = geocoding.get_latitude_and_longitude_from_file(city, zipcode)
        self.assertEquals(lat_long, ('49.1', '6.15'))

    def test_paris4eme_is_correctly_found(self):
        cities_zipcodes = [[x[1], x[2]] for x in geocoding.load_coordinates_for_cities()]

        paris4eme_zipcodes = [x[1] for x in cities_zipcodes if x[1] == "75004"]
        self.assertEquals(len(paris4eme_zipcodes), 1)
        zipcode = paris4eme_zipcodes[0]
        self.assertEquals(zipcode, "75004")

        city = "Paris 4eme arrondissement"
        lat_long = geocoding.get_latitude_and_longitude_from_file(city, zipcode)
        self.assertEquals(lat_long, ('48.8553815318', '2.35541102422'))
