import unittest

from labonneboite.common.geocoding import datagouv


class DatagouvTest(unittest.TestCase):

    def test_empty_query_raises_error(self):
        self.assertRaises(ValueError, datagouv.search, '')
