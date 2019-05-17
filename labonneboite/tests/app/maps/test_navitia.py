# coding: utf8
import os
import json
import unittest

import mock

from labonneboite.common.maps import constants
from labonneboite.common.maps import exceptions
from labonneboite.common.maps.vendors import navitia
from . import places


class NavitiaVendorTests(unittest.TestCase):

    @mock.patch.object(navitia, 'get_coverage', return_value='fr-ne')
    def test_isochrone_valid_response(self, mock_coverage):
        response_content = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            'navitia_metz_isochrone.json'
        )).read()
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=json.loads(response_content))
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(navitia.requests, 'get', requests_get):
            isochrone = navitia.isochrone(places.metz, constants.ISOCHRONE_DURATIONS_MINUTES[0])

        self.assertEqual(4, len(isochrone))
        self.assertEqual(182, len(isochrone[0]))
        self.assertEqual((49.1002798583, 6.1419329507), isochrone[0][0])


    @mock.patch.object(navitia, 'get_coverage', side_effect=exceptions.BackendUnreachable)
    def test_durations_navitia_unreachable(self, mock_coverage):
        self.assertRaises(exceptions.BackendUnreachable, navitia.durations, places.metz, [places.paris])
