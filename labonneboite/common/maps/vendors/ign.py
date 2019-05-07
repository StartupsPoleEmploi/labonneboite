import re

from requests.auth import HTTPBasicAuth
import requests

from flask import current_app

from labonneboite.conf import settings
from ..exceptions import BackendUnreachable


TIMEOUT_SECONDS = 8


def isochrone(origin, duration):
    # Documentation: https://geoservices.ign.fr/documentation/geoservices/isochrones.html
    endpoint = 'isochrone/isochrone.json'
    params = {
        'location': '{:.7f},{:.7f}'.format(origin[1], origin[0]),
        'time': int(duration * 60),
        'smoothing': 'true',
        # Settings holes=true yields really beautiful maps, but very hard to
        # debug. Also, requires more data transfer.
        # 'holes': 'true',
    }
    data = request_json_api(endpoint, params)

    # geometry is a string of the form: 'POLYGON ((3.504869 45.910195, ...), (...))'
    geometry = data['wktGeometry']
    polygons = re.findall(r'\([0-9. ,]+\)', geometry)
    isochrones = []
    for polygon in polygons:
        coordinates = polygon.strip(')').strip('(').split(', ')
        lon_lat = [coords.split(' ') for coords in coordinates]
        isochrones.append([
            (float(lat), float(lon)) for lon, lat in lon_lat
        ])
    return isochrones


def durations(origin, destinations):
    result = []
    for destination in destinations:
        data = get_journey(origin, destination)
        result.append(float(data['durationSeconds']))
    return result


def get_journey(origin, destination):
    """
    As a rough estimate, the IGN API replies in 1-2s.

    Documentation: https://geoservices.ign.fr/documentation/geoservices/itineraires.html

    Args:
        origin (coordinates)
        destination (coordinates)

    Return: the JSON data returned by the IGN "itineraire" API.
    """
    endpoint = 'itineraire/rest/route.json'
    params = {
        'origin': '{:.7f},{:.7f}'.format(origin[1], origin[0]),
        'destination': '{:.7f},{:.7f}'.format(destination[1], destination[0]),
        'graphName': 'Voiture'
    }
    data = request_json_api(endpoint, params)
    return data


def request_json_api(endpoint, params):
    ign_credentials = settings.IGN_CREDENTIALS
    url = 'https://wxs.ign.fr/{}/{}'.format(ign_credentials['key'], endpoint)
    auth = HTTPBasicAuth(
        ign_credentials['username'], ign_credentials['password']
    ) if 'username' in ign_credentials else None
    headers = {
        "Referer": ign_credentials['referer']
    } if 'referer' in ign_credentials else None

    try:
        response = requests.get(url, params=params, auth=auth, timeout=TIMEOUT_SECONDS, headers=headers)
    except requests.exceptions.Timeout:
        # This occurs frequently so we don't trigger a timeout
        current_app.logger.warning('IGN API timeout')
        raise BackendUnreachable

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        current_app.logger.error('Invalid IGN API user/password')
    elif response.status_code == 403:
        current_app.logger.error('Invalid IGN API key: %s', response.content)
    elif response.status_code == 500:
        # A 500 error from the IGN API is quite common
        current_app.logger.warning('IGN API 500 error: %s', response.content)
    else:
        current_app.logger.warning('IGN API %d error', response.status_code)
    raise BackendUnreachable
