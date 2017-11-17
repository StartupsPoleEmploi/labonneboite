import requests


def isochrone(origin, duration):
    """
    Args:
        origin (float tuple): (latitude, longitude) float coordinates
        duration (float): max travel time, in minutes

    Returns:
        [(lat, lon), ...]: float coordinates of the corners of the polygon that
        bounds the isochrone.
    """
    url = 'http://api-isochrone.geo.data.gouv.fr'
    params = {
        'lat': '{:.7f}'.format(origin[0]),
        'lng': '{:.7f}'.format(origin[1]),
        'intervals': duration,
        # Matrix size
        'radius': 2*duration,
        # Matrix precision in km
        'cellSize': 0.5,
    }

    # TODO timeout?
    # TODO http error?
    response = requests.get(url, params=params)
    # if response.status_code >= 500:
        # # TODO do what?
        # return None
    # if response.status_code >= 400:
        # # TODO do what?
        # return None

    # Empty responses have the following form:
    # '{"type":"FeatureCollection","features":[null]}'
    # TODO handle error of the type 'Each LinearRing of a Polygon must have 4 or more Positions'
    data = response.json()
    features = data['features'][0]
    if features is None:
        # TODO raise an exception with a message, so that the user can see a
        # nice explanation?
        return None

    # TODO what if the polygon is not connex?
    coordinates = features['geometry']['coordinates'][0]

    # Response is a pair of (lon, lat) that we convert to (lat, lon)
    # TODO check that we return an array of arrays
    return [[(coords[1], coords[0]) for coords in coordinates]]
