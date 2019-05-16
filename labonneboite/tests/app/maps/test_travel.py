# coding: utf8
import unittest
from unittest import mock

from labonneboite.common.maps import constants
from labonneboite.common.maps import travel
from . import places


class mock_backend(object):
    @staticmethod
    def durations(origin, destinations):
        distances = {
            (places.vallouise, places.paris): 7000,
            (places.vallouise, places.metz): 5000,
        }
        return [distances.get((origin, destination)) for destination in destinations]


class BackendCacheFuncTests(unittest.TestCase):

    def test_cache_key(self):
        self.assertEqual(
            b'["funcname", "travelmode", "arg1", "arg2"]',
            travel.cache_key('funcname', 'travelmode', 'arg1', 'arg2')
        )

    def test_available_backend(self):
        backend = mock.Mock(isochrone=mock.Mock(return_value=666))
        cache = travel.Cache()

        backend_name, mode = travel.backend_info('isochrone', None)
        cache_key = travel.cache_key(backend_name, 'isochrone', mode, 'arg')
        with mock.patch.object(travel.vendors, 'backend', return_value=backend):
            result = travel.backend_cached_func(cache, 'isochrone', constants.DEFAULT_TRAVEL_MODE, 'arg')

        self.assertEqual(666, result)
        self.assertEqual(result, cache.get(cache_key))

    def test_unavailable_backend(self):
        backend = mock.Mock(isochrone=mock.Mock(side_effect=travel.exceptions.BackendUnreachable))
        cache = travel.Cache()

        backend_name, mode = travel.backend_info('isochrone', None)
        cache_key = travel.cache_key(backend_name, 'isochrone', mode)
        with mock.patch.object(travel.vendors, 'backend', return_value=backend):
            result = travel.backend_cached_func(cache, 'isochrone', mode)

        self.assertIsNone(result)
        self.assertEqual(-1, cache.get(cache_key, -1))


class DurationsTests(unittest.TestCase):

    def setUp(self):
        travel.DURATIONS_CACHE.clear()

    @mock.patch.object(travel.vendors, 'backend', return_value=mock_backend)
    def test_durations(self, backend):
        durations = travel.durations(places.vallouise, [places.paris, places.metz], 'car')
        self.assertEqual([7000, 5000], durations)

    @mock.patch.object(travel.vendors, 'backend', return_value=mock_backend)
    def test_invalid_destination(self, backend):
        invalid = (95, 0)
        durations = travel.durations(places.vallouise, [invalid], 'car')

        self.assertEqual([None], durations)

    def test_caching(self):
        def durations(origin, destinations):
            return [1] * len(destinations)

        # Fill cache
        with mock.patch.object(travel.vendors, 'backend', return_value=mock.Mock(durations=durations)):
            durations1 = travel.durations(places.vallouise, [places.paris], 'car')

        # If there was no cache, this would raise a ZeroDivisionError
        with mock.patch.object(travel.vendors, 'backend', return_value=mock.Mock(side_effect=ZeroDivisionError)):
            durations2 = travel.durations(places.vallouise, [places.paris], 'car')

        self.assertEqual([1], durations1)
        self.assertEqual(durations1, durations2)
