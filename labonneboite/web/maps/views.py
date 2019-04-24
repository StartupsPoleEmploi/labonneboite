# coding: utf8
import json

from flask import abort, redirect, render_template, request, url_for
from flask import Blueprint

from labonneboite.common import geocoding
from labonneboite.common.maps import constants
from labonneboite.common.maps import travel


mapsBlueprint = Blueprint('maps', __name__)


@mapsBlueprint.route('/isochrone')
def isochrone():
    """
    Display the isochrone for a given location and travel mode. This is
    useful for debugging and pre-filling the cache in production.

    Request args:
        dur (int): Isochrone duration, in minutes. Must be one of allowed values.
        zipcode (str)
        tr (str): one of TRAVEL_MODES
    """
    zipcode = request.args.get('zipcode')
    duration = request.args.get('dur')
    travel_mode = request.args.get('tr')

    # Check argument validity
    if not zipcode:
        abort(400, description='Missing argument: zipcode')
    city = geocoding.get_city_by_zipcode(zipcode, None)
    if city is None:
        abort(400, description='Invalid zipcode')
    if duration:
        try:
            duration = int(duration)
        except ValueError:
            abort(400, description='Invalid duration')
        if duration not in constants.ISOCHRONE_DURATIONS_MINUTES:
            abort(400, description='Invalid duration: accepted values are {}'.format(
                constants.ISOCHRONE_DURATIONS_MINUTES
            ))
    if travel_mode and travel_mode not in constants.TRAVEL_MODES:
        abort(400, description='Invalid travel mode: accepted values are {}'.format(
            constants.TRAVEL_MODES
        ))

    # Check optional arguments
    if not (duration and travel_mode):
        duration = duration or constants.ISOCHRONE_DURATIONS_MINUTES[0]
        travel_mode = travel_mode or constants.DEFAULT_TRAVEL_MODE
        return redirect(url_for('maps.isochrone') + '?zipcode={}&dur={}&tr={}'.format(
            zipcode, duration, travel_mode
        ))

    latitude = city['coords']['lat']
    longitude = city['coords']['lon']

    travel_isochrone = travel.isochrone((latitude, longitude), duration, mode=travel_mode) or []

    # We reverse the isochrones to make life easier to js
    travel_isochrone = [
        [
            [coords[1], coords[0]] for coords in polygon
        ] for polygon in travel_isochrone
    ]

    return render_template(
        'search/geo.html',
        latitude=latitude,
        longitude=longitude,
        duration=duration,
        isochrone=json.dumps(travel_isochrone),
    )


# This view is a POST (with CSRF token) to prevent just anyone from making too many
# requests, exceed our API request quota and fill our cache.
@mapsBlueprint.route('/durations', methods=['POST'])
def durations():
    request_data = request.get_json(force=True) or {}
    try:
        travel_mode = request_data['travel_mode']
        origin = parse_coordinates(request_data['origin'])
        destinations = [parse_coordinates(dst) for dst in request_data['destinations']]
    except KeyError as e:
        return 'Missing argument: {}'.format(e.message), 400
    except ValueError:
        return 'Invalid coordinates: proper format is "latitude,longitude"', 400

    travel_durations = travel.durations(origin, destinations, mode=travel_mode)
    return json.dumps(travel_durations)


@mapsBlueprint.route('/directions')
def directions():
    try:
        travel_mode = request.args['tr']
        src = parse_coordinates(request.args['from'])
        dst = parse_coordinates(request.args['to'])
    except KeyError as e:
        return 'Missing argument: {}'.format(e.message), 400
    except ValueError:
        return 'Invalid coordinates: proper format is "latitude,longitude"', 400

    travel_directions = travel.directions(src, dst, mode=travel_mode)
    return json.dumps(travel_directions)


def parse_coordinates(point):
    """
    Parse str coordinates of the form "lat,lon". Raise ValueError on invalid
    arguments.
    """
    lat, lon = point.split(',')
    return float(lat), float(lon)
