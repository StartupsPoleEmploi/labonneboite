# coding: utf8
import unittest

from labonneboite.common import search


class SearchTest(unittest.TestCase):

    def search_in_naf(self, naf, lat, lon):
        distance = 5
        companies, _ = search.get_companies([naf, ], lat, lon, distance, 1, 1000)
        return [company.siret for company in companies]

    def test_lorraine_tube(self):
        siret = "44465668000048"
        naf = "2420Z"
        lat = 49.443509
        lon = 6.327310
        siret_list = self.search_in_naf(naf, lat, lon)
        self.assertNotIn(siret, siret_list)
