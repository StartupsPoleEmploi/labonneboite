import json
import os
import unittest

from unittest import mock

from labonneboite.common.maps import constants
from labonneboite.common.maps import exceptions
from labonneboite.common.maps.vendors import ign
from labonneboite.tests.test_base import AppTest
from . import places


class IgnVendorIsochroneTest(AppTest):

    def test_valid_response_positive_lat_lon(self):
        response_content = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            'ign_metz_isochrone.json'
        )).read()
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=json.loads(response_content))
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(ign.requests, 'get', requests_get):
            isochrone = ign.isochrone(places.metz, constants.ISOCHRONE_DURATIONS_MINUTES[0])

        self.assertEqual(1, len(isochrone))
        self.assertEqual(3876, len(isochrone[0]))
        self.assertEqual((48.929064, 6.110025), isochrone[0][0])

    def test_valid_response_negative_latitude(self):
        response_content = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            'ign_saint_paul_la_reunion_isochrone.json'
        )).read()
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=json.loads(response_content))
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(ign.requests, 'get', requests_get):
            isochrone = ign.isochrone(places.metz, constants.ISOCHRONE_DURATIONS_MINUTES[0])

        self.assertEqual(1, len(isochrone))
        self.assertEqual(25, len(isochrone[0]))
        self.assertEqual((-21.054997, 55.342211), isochrone[0][0])

    def test_valid_response_negative_longitude(self):
        response_content = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            'ign_la_rochelle_isochrone.json'
        )).read()
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=json.loads(response_content))
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(ign.requests, 'get', requests_get):
            isochrone = ign.isochrone(places.metz, constants.ISOCHRONE_DURATIONS_MINUTES[0])

        self.assertEqual(1, len(isochrone))
        self.assertEqual(5935, len(isochrone[0]))
        self.assertEqual((45.921463, -0.971666), isochrone[0][0])


    def test_ign_500_error(self):
        response = mock.Mock(
            status_code=500,
        )
        requests_get = mock.Mock(return_value=response)

        with self.test_request_context():
            with mock.patch.object(ign.requests, 'get', requests_get):
                self.assertRaises(exceptions.BackendUnreachable,
                                  ign.isochrone, places.vallouise, constants.ISOCHRONE_DURATIONS_MINUTES[0])

    def test_ign_authentication_error(self):
        response = mock.Mock(
            status_code=403,
            content='Invalid key'
        )
        requests_get = mock.Mock(return_value=response)

        with self.test_request_context():
            with mock.patch.object(ign.requests, 'get', requests_get):
                self.assertRaises(exceptions.BackendUnreachable,
                                  ign.isochrone, places.metz, constants.ISOCHRONE_DURATIONS_MINUTES[0])

    def test_ign_timeout(self):
        requests_get = mock.Mock(side_effect=ign.requests.exceptions.Timeout())

        with self.test_request_context():
            with mock.patch.object(ign.requests, 'get', requests_get):
                self.assertRaises(exceptions.BackendUnreachable,
                                  ign.isochrone, places.metz, constants.ISOCHRONE_DURATIONS_MINUTES[0])


class IgnVendorJourneyTest(unittest.TestCase):

    def mock_request_get(self):
        response_content = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            'ign_directions_metz_oxycoupure.json'
        )).read()
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=json.loads(response_content))
        )
        requests_get = mock.Mock(return_value=response)
        return requests_get

    def test_durations(self):
        with mock.patch.object(ign.requests, 'get', self.mock_request_get()):
            # Get travel duration from Metz downtown to Oxycoupure company
            durations = ign.durations(places.metz, [(49.1029, 6.17488)])

        self.assertEqual([238.41], durations)
