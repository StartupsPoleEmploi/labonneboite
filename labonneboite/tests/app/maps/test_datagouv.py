# coding: utf8
import unittest

import mock

from labonneboite.common.maps.vendors import datagouv
from . import places


class DatagouvVendorTests(unittest.TestCase):

    def test_empty_response(self):
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value={
                'type': 'FeatureCollection',
                'features': [None]
            })
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(datagouv.requests, 'get', requests_get):
            isochrone = datagouv.isochrone(places.paris, 1)

        self.assertIsNone(isochrone)
