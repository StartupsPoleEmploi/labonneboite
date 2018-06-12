# coding: utf8
import logging

from backports.functools_lru_cache import lru_cache
import requests

from labonneboite.conf import settings


logger = logging.getLogger('main')



def search(address, limit=10):
    """
    Return a list of locations with latitude/longitude coordinates that
    corresponds to the required address. Perfect for autocomplete.

    Example: https://api-adresse.data.gouv.fr/search/?q=8%20bd%20du%20port
    """
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
    # FIXME: insecure SSL request because we don't have SNI in production
    response = requests.get(settings.API_ADRESSE_BASE_URL + endpoint, params=params, verify=False)
    if response.status_code >= 400:
        error = u'adresse-api.data.gouv.fr responded with a {} error: {}'.format(
            response.status_code, response.content
        )
        # We log an error only if we made an incorrect request
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        return []

    # When you need to store a response and later use it as a mock in the tests,
    # just run a breakpoint here in dev environnement then:
    # $ json.dump(response.json(), open("mymock.json", "w"), indent=4, sort_keys=True)
    return response.json()['features']
