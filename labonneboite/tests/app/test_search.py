import unittest

import mock

from labonneboite.common import search


class mock_backend(object):
    @staticmethod
    def isochrone(origin, duration):
        # Return a square of size 1x1 around the origin
        return [
            [
                (origin[0] - 0.5, origin[1] - 0.5),  # bottom left
                (origin[0] - 0.5, origin[1] + 0.5),  # bottom right
                (origin[0] + 0.5, origin[1] + 0.5),  # top right
                (origin[0] + 0.5, origin[1] - 0.5),  # top left
            ]
        ]


class SearchIsochroneTests(unittest.TestCase):

    def setUp(self):
        search.travel.ISOCHRONE_CACHE.clear()

    def test_isochrone(self):
        latitude = 45
        longitude = 6

        with mock.patch.object(search.travel.vendors, 'backend', return_value=mock_backend):
            body = search.build_json_body_elastic_search([], "romecode", latitude, longitude, 10, duration=10)

        should_filters = body['query']['function_score']['query']['function_score']['query']['filtered']['filter']['bool']['should']
        self.assertEqual(
            [longitude - 0.5, latitude - 0.5],
            should_filters[0]['geo_polygon']['locations']['points'][0]
        )

    def test_isochrone_with_broken_backend(self):
        latitude = 45
        longitude = 6

        broken_backend = mock.Mock(isochrone=mock.Mock(side_effect=search.travel.exceptions.BackendUnreachable))
        with mock.patch.object(search.travel.vendors, 'backend', return_value=broken_backend):
            body = search.build_json_body_elastic_search([], "romecode", latitude, longitude, 10, duration=10)

        self.assertNotIn('should', body['query']['function_score']['query']['function_score']['query']['filtered']['filter']['bool'])
