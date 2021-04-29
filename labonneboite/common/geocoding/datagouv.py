import logging

from functools import lru_cache
import requests
from requests.exceptions import ConnectionError, ReadTimeout

from labonneboite.common.util import unique_elements
from labonneboite.conf import settings

import json

logger = logging.getLogger('main')

BAN_TIMEOUT = 3



def search(address, limit=10):
    """
    Return a list of locations with latitude/longitude coordinates that
    corresponds to the required address. Perfect for autocomplete.

    This API mixess the results of the address API (https://api-adresse.data.gouv.fr/)
    with the departments API (https://geo.api.gouv.fr/departements)
    """
    if not address:
        return []

    addresses = get_addresses('/search', **{
        'q': address[:200], # Longer requests cause a 413 error
        'limit': limit
    })
    departments = get_departments(address, 2)

    combined = departments + addresses

    return combined[0:limit]


def reverse(latitude, longitude, limit=10):
    """
    Find the candidate addresses associated to given latitude/longitude
    coordinates.
    """
    return get_addresses('/reverse', **{
        'lat': latitude,
        'lon': longitude,
        'limit': limit
    })

def get_addresses(endpoint, **params):
    """
    Request the https://api-adresse.data.gouv.fr API.
    Documentation: https://adresse.data.gouv.fr/api

    Args:
        endpoint (str)
        params (dict): key/value dictionary to pass as query string
    """
    response = fetch_json(
        url=settings.API_ADRESSE_BASE_URL + endpoint,
        name='api-adresse.data.gouv.fr',
        **params,
    )

    addresses = response.get('features', [])

    if (endpoint == '/search'):
        return format_coordinates(addresses)
    if (endpoint == '/reverse'):
        return format_addresses(addresses)
    raise Exception('Unknown endpoint for adresse API')

def format_addresses(addresses):
    features = []
    for result in addresses:
        try:
            features.append({
                'label': result['properties']['label'],
                'zipcode': result['properties']['postcode'],
                'city': result['properties']['city'],
                'city_code': result['properties']['citycode'],
            })
        except KeyError:
            pass
    return unique_elements(features)

def format_coordinates(addresses):
    features = []
    for result in addresses:
        try:
            feature = {
                'latitude': result['geometry']['coordinates'][1],
                'longitude': result['geometry']['coordinates'][0],
                'label': result['properties']['label'],
                'zipcode': result['properties']['postcode'],
                'city': result['properties']['city'],
                'city_code': result['properties']['citycode'],
                'score': result['properties']['score'],
            }
            # The zipcode is normally always present in the label,
            # but sometimes is inconsistently absent from it (e.g. Saint-Paul)
            # thus we add it if necessary.
            if feature['zipcode'] not in feature['label']:
                feature['label'] += " %s" % feature['zipcode']
            features.append(feature)
        except KeyError:
            continue

    return unique_elements(features, key=lambda x: (x['latitude'], x['longitude']))

def get_departments(query, limit=10):
    """
    Request the https://geo.api.gouv.fr/departements API
    Documentation: https://geo.api.gouv.fr/decoupage-administratif/departements

    Args:
        query (str): the name of a department (département) - possibly incomplete
    """
    departments = fetch_json(
        url=settings.API_DEPARTMENTS_URL,
        name='geo.api.gouv.fr/departements',
        is_array=True,
        **{'nom': query, 'limit': limit},
    )
    return format_departments(departments)

def get_department_by_code(code):
    """
    Request the https://geo.api.gouv.fr/departements API
    Documentation: https://geo.api.gouv.fr/decoupage-administratif/departements

    Args:
        code (str): the code of a department (département)
    """
    department = fetch_json(
        url=settings.API_DEPARTMENTS_URL + '/' + code,
        name='geo.api.gouv.fr/departements',
        is_array=False,
    )
    return format_single_department(department)

def format_departments(departments):
    return list(map(format_single_department, departments))

def format_single_department(department):
    return {
        'department': department['code'],
        'label': "%s (%s)" % (department['nom'], department['code']),
        'score': department['_score'] if '_score' in department else 0, # score is None when calling get_department_by_code
    }

@lru_cache(1000)
def fetch_json(url, name, is_array = False, **params):
    """
    Request the desired API and handle errors

    Args:
        url (str)
        name (str): the name to identify the API in the logs
        params (dict): key/value dictionary to pass as query string
    """
    try:
        response = requests.get(
            url,
            params=params,
            timeout=BAN_TIMEOUT,
        )
    except (ConnectionError, ReadTimeout):
        # FIXME log BAN DOWN event
        return [] if is_array else {}
    if response.status_code >= 400:
        error = name + ' responded with a {} error: {}'.format(
            response.status_code, response.content
        )
        # We log an error only if we made an incorrect request
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        return [] if is_array else {}
    try:
        result = response.json()
    except Exception as e:
        error = name + ' responded with an invalid JSON. Error: {}'.format(e)
        log_level = logging.WARNING if response.status_code >= 500 else logging.ERROR
        logger.log(log_level, error)
        return [] if is_array else {}
    return result
