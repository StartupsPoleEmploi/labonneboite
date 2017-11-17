# coding: utf8
import json
import os
import unittest

import mock

from labonneboite.common.maps.vendors import google
from . import places


class GoogleVendorTests(unittest.TestCase):

    @mock.patch.object(google.settings, 'GOOGLE_API_KEY', 'apikey')
    def test_valid_response(self):
        response_content = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            'google_vallouise_paris_metz.json'
        )).read()
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=json.loads(response_content))
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(google.requests, 'get', requests_get):
            durations = google.durations(places.vallouise, [places.paris, places.metz])

        self.assertEqual([28574, 27942], durations)
        requests_get.assert_called_once_with(google.DISTANCE_MATRIX_URL, params={
            # Precision is important here
            'origins': ['44.8596709,6.4214523'],
            'key': 'apikey',
            'destinations': '48.8588376,2.2768492|49.1048477,6.1613009'
        })

    def test_400_response(self):
        requests_get = mock.Mock(return_value=mock.Mock(status_code=400))
        with mock.patch.object(google.requests, 'get', requests_get):
            durations = google.durations(places.vallouise, [places.paris, places.metz])

        self.assertEqual([None, None], durations)

    def test_invalid_destination(self):
        response_json = {
            'status': 'OK',
            'rows': [
                {
                    'elements': [
                        {'status': 'NOT_FOUND'}
                    ]
                }
            ],
            'origin_addresses': [''],
            'destination_addresses': ['']
        }
        response = mock.Mock(
            status_code=200,
            json=mock.Mock(return_value=response_json)
        )
        requests_get = mock.Mock(return_value=response)

        with mock.patch.object(google.requests, 'get', requests_get):
            durations = google.durations(places.vallouise, [(95, 2)])

        self.assertEqual([None], durations)
