from functools import lru_cache

import requests
from flask import current_app

from labonneboite.conf import settings

from ..exceptions import BackendUnreachable


TIMEOUT_SECONDS = 5


def isochrone(origin, duration):
    data = request_location_api(
        "isochrones",
        origin,
        {
            "from": "{:.7f};{:.7f}".format(origin[1], origin[0]),
            "max_duration": int(duration * 60),
            # Activate transport by car only (although navitia was clearly not made
            # for car transport)
            # 'first_section_mode[]': 'car',
            # 'last_section_mode[]': 'car',
        },
    )

    coordinates = data["isochrones"][0]["geojson"]["coordinates"]

    # Each polygon is a pair of (lon, lat) that we convert to (lat, lon)
    return [[(coords[1], coords[0]) for coords in polygon[0]] for polygon in coordinates]


def durations(origin, destinations):
    """
    Note that the Navitia API is highly inefficient for fetching many results at a time.
    """
    # Endpoint must be computed just once so that we don't make too many
    # coverage requests to navitia
    endpoint = get_coverage_endpoint("journeys", origin)
    results = []
    for destination in destinations:
        duration = get_duration(endpoint, origin, destination)
        results.append(duration)
    return results


# Auxiliary functions


def get_duration(endpoint, origin, destination):
    params = {
        "from": "{:.7f};{:.7f}".format(origin[1], origin[0]),
        "to": "{:.7f};{:.7f}".format(destination[1], destination[0]),
    }

    try:
        data = request_json_api(endpoint, params=params)
        if data.get("error") and data["error"]["id"] == "no_solution":
            duration = None
        else:
            duration = data["journeys"][0]["duration"]
    except BackendUnreachable:
        duration = None

    return duration


def request_location_api(endpoint, location, params):
    endpoint = get_coverage_endpoint(endpoint, location)
    return request_json_api(endpoint, params=params)


def get_coverage_endpoint(endpoint, location):
    coverage_id = get_coverage(location)
    return "coverage/{}/{}".format(coverage_id, endpoint)


@lru_cache(1000)
def get_coverage(location):
    endpoint = "coverage/{:.7f};{:.7f}".format(location[1], location[0])
    data = request_json_api(endpoint)
    if data is None:
        # This is a serious error but we cannot crash the entire app
        raise BackendUnreachable

    try:
        region_id = data["regions"][0]["id"]
    except (KeyError, IndexError):
        # This is a serious error that should not happen -- unless invalid
        # coordinates were used? We'll have to examine logs to find out.
        current_app.logger.error("Coverage region could not be found for location %s", location)
        raise BackendUnreachable

    return region_id


def request_json_api(endpoint, params=None):
    url = "https://api.navitia.io/v1/{}".format(endpoint)
    headers = {"Authorization": settings.NAVITIA_API_TOKEN}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        current_app.logger.warning("Navitia API %s timeout", endpoint)
        raise BackendUnreachable

    if response.status_code == 200:
        return response.json()
    if response.status_code == 500:
        current_app.logger.error("Navitia API 500 error: %s", response.content)
    elif response.status_code == 401:
        current_app.logger.error("Navitia API invalid token")

    raise BackendUnreachable
