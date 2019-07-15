"""
These functions are used to mock Navitia API responses.
"""

import os
import json
from unittest import mock

from labonneboite.common.maps.vendors import navitia

FIXTURES_ROOT = os.path.join(os.path.dirname(__file__), 'fixtures', 'navitia')

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

    response = _mock_response_from_json(file)

    # The Navitia module makes two API requests:
    # one to get a coverage id and a second one to get isochrones.
    # For more details on the coverage_id, see the full request answer here:
    # fixtures/navitia_metz_coverage.json
    with mock.patch.object(navitia, 'get_coverage', return_value='fr-ne'):
        with mock.patch.object(navitia.requests, 'get', response):
            isochrone = navitia.isochrone(origin, duration)

    return isochrone



def durations(origin, destinations):
    """
    Return commute time from an origin to several destinations.
    /!\ This only works in test mode, not in local, as we load one JSON file
    per office.

    Input:
        - origin: coordinates (tuple(latitude, longitude))
        - destinations: list or coordinates.

    Output:
        List of durations in seconds (float).
    """
    coverage_response_file = open(os.path.join(
        FIXTURES_ROOT,
        f'metz_coverage.json'
    )).read()

    coverage_response = _mock_response_from_json(coverage_response_file)

    with mock.patch.object(navitia.requests, 'get', coverage_response):
        endpoint = navitia.get_coverage_endpoint('journeys', origin)

    results = []
    for destination in destinations:
        file = open(os.path.join(
            FIXTURES_ROOT,
            'destinations',
            f'{destination[0]}_{destination[1]}.json'
        )).read()

        response = _mock_response_from_json(file)

        with mock.patch.object(navitia.requests, 'get', response):
            duration = navitia.get_duration(endpoint, origin, destination)

        results.append(duration)

    return results


def _mock_response_from_json(file):
    """
    Mock an HTTP request based on a JSON file.
    Return a 200 status code and the response.
    """
    response = mock.Mock(
        status_code=200,
        json=mock.Mock(return_value=json.loads(file))
    )
    return mock.Mock(return_value=response)
