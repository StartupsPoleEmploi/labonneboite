import os
import json
from unittest import mock

from labonneboite.common.maps.vendors import ign
from flask import current_app

"""
These functions are used to mock IGN API responses in Selenium tests.
"""



def isochrone(origin, duration):
    """

    """
    ign_response = open(os.path.join(
            os.path.dirname(__file__), 'fixtures',
            f'ign_metz_isochrone_{duration}_minutes.json'
        )).read()

    response = mock.Mock(
        status_code=200,
        json=mock.Mock(return_value=json.loads(ign_response))
    )
    requests_get = mock.Mock(return_value=response)

    with mock.patch.object(ign.requests, 'get', requests_get):
        isochrone = ign.isochrone(origin, duration)

    return isochrone



def durations(origin, destinations):
    """
    A dummy duration estimator that answers 'I don't know the durations' all
    the time.

    Returns: list of float durations, or None when duration could not be
    computed. The list has the same length as the destinations argument.
    """
    return [None]*len(destinations)
