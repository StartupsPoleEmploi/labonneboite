import unittest
import unittest.mock

from labonneboite.common.geocoding import datagouv


class DatagouvTest(unittest.TestCase):

    def test_empty_query_raises_error(self):
        self.assertRaises(ValueError, datagouv.search, '')

    def test_long_addresses_are_shortened(self):
        long_address = 'a' * 300
        short_address = 'a' * 200
        with unittest.mock.patch.object(datagouv, 'get_features', return_value=[]) as mock_get_features:
            datagouv.search(long_address)
            self.assertEqual(short_address, mock_get_features.call_args[1]['q'])
