import logging

from functools import lru_cache
import requests
from requests.exceptions import ConnectionError, ReadTimeout

from labonneboite.conf import settings


logger = logging.getLogger('main')

BAN_TIMEOUT = 3



def search(address, limit=10):
    """
    Return a list of locations with latitude/longitude coordinates that
    corresponds to the required address. Perfect for autocomplete.

    Example: https://api-adresse.data.gouv.fr/search/?q=8%20bd%20du%20port
    """
    if not address:
        raise ValueError(address)

    # Longer requests cause a 413 error
    address = address[:200]

    return get_features('/search', **{
        'q': address,
        'limit': limit
    })


def reverse(latitude, longitude, limit=10):
    """
    Find the candidate addresses associated to given latitude/longitude
    coordinates.
    """
    return get_features('/reverse', **{
        'lat': latitude,
        'lon': longitude,
        'limit': limit
    })


@lru_cache(1000)
def get_features(endpoint, **params):
    """
    Request the https://api-adresse.data.gouv.fr API.
    Documentation: https://adresse.data.gouv.fr/api

    Args:
        endpoint (str)
        params (dict): key/value dictionary to pass as query string
    """
    try:
        response = requests.get(
            settings.API_ADRESSE_BASE_URL + endpoint,
            params=params,
            timeout=BAN_TIMEOUT,
        )
    except (ConnectionError, ReadTimeout):
        # FIXME log BAN DOWN event
        return []
    if response.status_code >= 400:
        error = 'adresse-api.data.gouv.fr responded with a {} error: {}'.format(
            response.status_code, response.content
        )
        # We log an error only if we made an incorrect request
        # FIXME Where does this log go? Not found in uwsgi log nor sentry.
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        return []

    return response.json()['features']
