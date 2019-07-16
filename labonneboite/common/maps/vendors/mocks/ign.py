"""
These functions are used to mock IGN API requests.
"""

import os
from unittest import mock

from labonneboite.common.maps.vendors import ign
from .utils import mock_response_from_json


FIXTURES_ROOT = os.path.join(os.path.dirname(__file__), 'fixtures', 'ign')


def isochrone(origin, duration):
    """
    Return isochrones in the Metz area only based on a JSON file.

    origin: tuple(latitude, longitude)
    duration: integer
    """
    file = open(os.path.join(
        FIXTURES_ROOT,
        'isochrones',
        f'metz_{duration}_minutes.json'
    )).read()

    response = mock_response_from_json(file)

    with mock.patch.object(ign.requests, 'get', response):
        isochrone = ign.isochrone(origin, duration)

    return isochrone



def durations(origin, destinations):
    """
    Return commute time from an origin to several destinations.
    /!\ This only works in test mode, not in development, as we load one JSON file
    per office and we have too many in dev to make it possible.

    Input:
        - origin: coordinates (tuple(latitude, longitude))
        - destinations: list or coordinates.

    Output:
        List of durations in seconds (float).
    """
    result = []
    for destination in destinations:

        file = open(os.path.join(
            FIXTURES_ROOT,
            'destinations',
            f'{destination[0]}_{destination[1]}.json'
        )).read()

        response = mock_response_from_json(file)


        with mock.patch.object(ign.requests, 'get', response):
            data = ign.get_journey(origin, destination)

        result.append(float(data['durationSeconds']))

    return result
