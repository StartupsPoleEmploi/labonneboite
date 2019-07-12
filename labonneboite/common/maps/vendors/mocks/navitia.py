import os
import json
from unittest import mock

from labonneboite.common.maps.vendors import navitia
from flask import current_app

"""
These functions are used to mock Navitia API responses.
"""


def isochrone(origin, duration):
    """

    """
    navitia_response = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            f'navitia_metz_isochrone_{duration}_minutes.json'
        )).read()

    response = mock.Mock(
        status_code=200,
        json=mock.Mock(return_value=json.loads(navitia_response))
    )

    requests_get = mock.Mock(return_value=response)

    # The Navitia module makes two API requests:
    # one to get a coverage id and a second one to get isochrones.
    # For more details on the coverage_id, see the full request answer here:
    # fixtures/navitia_metz_coverage.json
    with mock.patch.object(navitia, 'get_coverage', return_value='fr-ne'):
        with mock.patch.object(navitia.requests, 'get', requests_get):
            isochrone = navitia.isochrone(origin, duration)

    return isochrone



def durations(origin, destinations):
    """
    A dummy duration estimator that answers 'I don't know the durations' all
    the time.

    Returns: list of float durations, or None when duration could not be
    computed. The list has the same length as the destinations argument.
    """
    return [None]*len(destinations)
