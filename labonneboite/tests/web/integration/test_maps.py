# coding: utf8
import json

from flask import url_for
from unittest import mock

from labonneboite.common.maps import constants
from labonneboite.tests.test_base import AppTest
from labonneboite.tests.app.maps import places


class IsochroneTest(AppTest):

    def test_valid_arguments(self):
        with self.test_request_context():
            rv = self.app.get(url_for('maps.isochrone') + '?zipcode={}&dur={}&tr={}'.format(
                '75000',
                constants.ISOCHRONE_DURATIONS_MINUTES[0],
                constants.DEFAULT_TRAVEL_MODE
            ))
            self.assertEqual(200, rv.status_code)

    def test_invalid_zipcode(self):
        with self.test_request_context():
            rv = self.app.get(url_for('maps.isochrone') + '?zipcode={}&dur={}&tr={}'.format(
                '195000',
                constants.ISOCHRONE_DURATIONS_MINUTES[0],
                constants.DEFAULT_TRAVEL_MODE
            ))
            self.assertEqual(400, rv.status_code)

    def test_invalid_duration(self):
        with self.test_request_context():
            rv = self.app.get(url_for('maps.isochrone') + '?zipcode={}&dur={}&tr={}'.format(
                '75000',
                10000,
                constants.DEFAULT_TRAVEL_MODE
            ))
            self.assertEqual(400, rv.status_code)

    def test_non_integer_duration(self):
        with self.test_request_context():
            rv = self.app.get(url_for('maps.isochrone') + '?zipcode={}&dur={}&tr={}'.format(
                '75000',
                'plonk',
                constants.DEFAULT_TRAVEL_MODE
            ))
            self.assertEqual(400, rv.status_code)

    def test_invalid_travel_mode(self):
        with self.test_request_context():
            rv = self.app.get(url_for('maps.isochrone') + '?zipcode={}&dur={}&tr={}'.format(
                '75000',
                constants.ISOCHRONE_DURATIONS_MINUTES[0],
                'hoverboard'
            ))
            self.assertEqual(400, rv.status_code)

    def test_missing_argument(self):
        with self.test_request_context():
            rv = self.app.get(url_for('maps.isochrone') + '?zipcode={}&dur={}'.format(
                '75000',
                constants.ISOCHRONE_DURATIONS_MINUTES[0],
            ))
            self.assertEqual(302, rv.status_code)


class DurationsTest(AppTest):

    def test_valid_arguments(self):
        def durations(origin, destinations):
            for dst in destinations:
                if dst == places.paris:
                    yield 3600
                elif dst == places.vallouise:
                    yield 7200
                else:
                    yield None

        mock_backend = mock.Mock(durations=durations)
        with mock.patch('labonneboite.common.maps.travel.vendors.backend', return_value=mock_backend):
            with self.test_request_context():
                rv = self.app.post(url_for('maps.durations'), data=json.dumps({
                    'origin': [places.metz[0], places.metz[1]],
                    'destinations': [
                        [places.paris[0], places.paris[1]],
                        [places.vallouise[0], places.vallouise[1]],
                    ],
                    'travel_mode': constants.DEFAULT_TRAVEL_MODE,
                }), content_type='application/json')

        self.assertEqual(200, rv.status_code, msg='Response data: {}'.format(rv.data))
        self.assertEqual([3600, 7200], json.loads(rv.data))
