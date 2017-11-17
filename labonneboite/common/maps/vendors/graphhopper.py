import requests


def isochrone(origin, duration):
    """
    TODO
    """
    # url = 'http://192.168.1.101:8989/isochrone'
    url = 'http://192.168.4.105:8989/isochrone'
    params = {
        'point': '{:.7f},{:.7f}'.format(origin[0], origin[1]),
        'time_limit': int(duration*60),
        'vehicle': 'car',
    }

    # TODO timeout?
    # TODO http error?
    response = requests.get(url, params=params)
    # import ipdb; ipdb.set_trace()
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
    if 'polygons' not in data:
        print data
    coordinates = data['polygons'][0]['geometry']['coordinates'][0]

    # Response is a pair of (lon, lat) that we convert to (lat, lon)
    # TODO check that we return an array of arrays
    return [[(coords[1], coords[0]) for coords in coordinates]]
