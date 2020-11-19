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


class DurationsTests(unittest.TestCase):

    @mock.patch.object(travel.vendors, 'backend', return_value=mock_backend)
    def test_durations(self, backend):
        durations = travel.durations(places.vallouise, [places.paris, places.metz], 'car')
        self.assertEqual([7000, 5000], durations)

    @mock.patch.object(travel.vendors, 'backend', return_value=mock_backend)
    def test_invalid_destination(self, backend):
        invalid = (95, 0)
        durations = travel.durations(places.vallouise, [invalid], 'car')

        self.assertEqual([None], durations)

